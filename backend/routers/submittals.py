"""
routers/submittals.py

FastAPI router for submittal management.

Routes:
  POST /submittals/         — Create a submittal (with optional document link)
  GET  /submittals/         — List submittals (filterable by spec_section, status)
  GET  /submittals/{id}     — Get submittal details including its NCRs
  PATCH /submittals/{id}/status — Update submittal status (role-gated)
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models, database
from auth import get_current_user, require_roles, Role
from models import SubmittalStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submittals", tags=["Submittals"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SubmittalCreate(BaseModel):
    submittal_number: str
    title: str
    vendor_name: Optional[str] = None
    document_id: Optional[int] = None
    spec_section_ref: Optional[str] = None
    submitted_value: Optional[str] = None


class SubmittalOut(BaseModel):
    id: int
    submittal_number: str
    title: str
    vendor_name: Optional[str]
    spec_section_ref: Optional[str]
    submitted_value: Optional[str]
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True


class NCRSummary(BaseModel):
    id: int
    ncr_number: str
    severity: Optional[str]
    status: str
    deviation_description: str
    ai_confidence: Optional[float]

    class Config:
        from_attributes = True


class SubmittalDetail(SubmittalOut):
    ncrs: list[NCRSummary] = []


class StatusUpdate(BaseModel):
    status: SubmittalStatus


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

UPLOAD_DIR = "uploads/submittals"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=list[SubmittalOut])
async def upload_submittal(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles([Role.CONTRACTOR, Role.ENGINEER, Role.PM])),
):
    """
    Upload a vendor submittal PDF.
    This saves the file and uses the SubmittalParser agent to extract all 
    structured data (vendor, specs) automatically. Returns a list of submittals 
    if the PDF contains multiple products!
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported for submittals right now.")

    # 1. Save file locally
    file_id = uuid.uuid4().hex
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
    
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # 2. Save Document record
    doc = models.Document(
        filename=f"{file_id}.pdf",
        original_name=file.filename,
        file_path=save_path,
        doc_type=models.DocumentType.submittal,
        uploaded_by=current_user.id,
        is_processed=True,  # Processed instantly via parser
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 3. Parse PDF with AI Agent
    from agents.submittal_parser import parse_submittal_pdf
    parsed_items = parse_submittal_pdf(save_path, file.filename)

    # 4. Count existing to generate submittal number
    existing_count = db.query(models.Submittal).count()

    created_submittals = []
    
    # 5. Create Submittal Record(s)
    for i, item in enumerate(parsed_items):
        sub_num = f"SUB-{datetime.now().year}-{existing_count + i + 1:03d}"
        
        sub = models.Submittal(
            submittal_number=sub_num,
            title=item.get("title", file.filename),
            vendor_name=item.get("vendor_name"),
            document_id=doc.id,
            spec_section_ref=item.get("spec_section_ref"),
            submitted_value=item.get("submitted_value"),
            status=models.SubmittalStatus.pending,
        )
        db.add(sub)
        created_submittals.append(sub)
        
    db.commit()
    for sub in created_submittals:
        db.refresh(sub)
    
    logger.info(f"Successfully created {len(created_submittals)} submittal(s) from {file.filename}")
    return created_submittals


@router.post("/", response_model=SubmittalOut)
def create_submittal(
    payload: SubmittalCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = db.query(models.Submittal).filter(
        models.Submittal.submittal_number == payload.submittal_number
    ).first()
    if existing:
        raise HTTPException(409, f"Submittal '{payload.submittal_number}' already exists.")

    sub = models.Submittal(**payload.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.get("/", response_model=list[SubmittalOut])
def list_submittals(
    spec_section_ref: Optional[str] = None,
    status: Optional[SubmittalStatus] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Submittal)
    if spec_section_ref:
        query = query.filter(models.Submittal.spec_section_ref == spec_section_ref)
    if status:
        query = query.filter(models.Submittal.status == status)
    return query.order_by(models.Submittal.submitted_at.desc()).all()


@router.get("/{submittal_id}", response_model=SubmittalDetail)
def get_submittal(
    submittal_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    sub = db.query(models.Submittal).filter(models.Submittal.id == submittal_id).first()
    if not sub:
        raise HTTPException(404, "Submittal not found.")

    ncrs = db.query(models.NonConformanceReport).filter(
        models.NonConformanceReport.submittal_id == submittal_id
    ).all()

    result = SubmittalDetail.model_validate(sub)
    result.ncrs = [NCRSummary.model_validate(n) for n in ncrs]
    return result


@router.patch("/{submittal_id}/status", response_model=SubmittalOut)
def update_submittal_status(
    submittal_id: int,
    payload: StatusUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles([Role.ENGINEER, Role.PM])),
):
    sub = db.query(models.Submittal).filter(models.Submittal.id == submittal_id).first()
    if not sub:
        raise HTTPException(404, "Submittal not found.")

    sub.status = payload.status
    sub.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sub)
    return sub
