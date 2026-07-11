"""
routers/ncr.py

FastAPI router for Non-Conformance Reports.

Routes:
  GET  /ncr/               — List NCRs (filterable by status, severity, submittal)
  GET  /ncr/{id}           — Get full NCR detail with spec clause + submittal context
  PATCH /ncr/{id}/approve  — Approve NCR (engineer/pm only)
  PATCH /ncr/{id}/void     — Void NCR (pm only)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models, database
from auth import get_current_user, require_roles, Role
from models import NCRStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ncr", tags=["Non-Conformance Reports"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class NCROut(BaseModel):
    id: int
    ncr_number: str
    submittal_id: Optional[int] = None
    clause_id: Optional[int] = None
    test_record_id: Optional[int] = None
    required_value: Optional[str]
    submitted_value: Optional[str]
    deviation_description: str
    severity: Optional[str]
    status: str
    ai_confidence: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class NCRDetail(NCROut):
    """Full NCR detail including source clause and submittal context."""
    clause_number: Optional[str] = None
    clause_title: Optional[str] = None
    clause_content: Optional[str] = None
    clause_page: Optional[int] = None
    submittal_number: Optional[str] = None
    vendor_name: Optional[str] = None


class ApprovalPayload(BaseModel):
    notes: Optional[str] = None  # Optional review notes attached to approval


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[NCROut])
def list_ncrs(
    status: Optional[NCRStatus] = None,
    severity: Optional[str] = None,
    submittal_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.NonConformanceReport)
    if status:
        query = query.filter(models.NonConformanceReport.status == status)
    if severity:
        query = query.filter(models.NonConformanceReport.severity == severity)
    if submittal_id:
        query = query.filter(models.NonConformanceReport.submittal_id == submittal_id)
    return query.order_by(models.NonConformanceReport.created_at.desc()).all()


@router.get("/{ncr_id}", response_model=NCRDetail)
def get_ncr(
    ncr_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    ncr = db.query(models.NonConformanceReport).filter(
        models.NonConformanceReport.id == ncr_id
    ).first()
    if not ncr:
        raise HTTPException(404, "NCR not found.")

    clause = db.query(models.SpecSection).filter(
        models.SpecSection.id == ncr.clause_id
    ).first()
    submittal = db.query(models.Submittal).filter(
        models.Submittal.id == ncr.submittal_id
    ).first()

    detail = NCRDetail.model_validate(ncr)
    if clause:
        detail.clause_number = clause.clause_number
        detail.clause_title = clause.clause_title
        detail.clause_content = clause.content
        detail.clause_page = clause.page_number
    if submittal:
        detail.submittal_number = submittal.submittal_number
        detail.vendor_name = submittal.vendor_name

    return detail


@router.patch("/{ncr_id}/approve", response_model=NCROut)
def approve_ncr(
    ncr_id: int,
    payload: ApprovalPayload,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles([Role.ENGINEER, Role.PM])),
):
    ncr = db.query(models.NonConformanceReport).filter(
        models.NonConformanceReport.id == ncr_id
    ).first()
    if not ncr:
        raise HTTPException(404, "NCR not found.")
    if ncr.status not in (NCRStatus.draft, NCRStatus.pending_review):
        raise HTTPException(409, f"NCR is already in status '{ncr.status}' — cannot approve.")

    ncr.status = NCRStatus.approved
    ncr.approved_by = current_user.id
    db.commit()
    db.refresh(ncr)
    logger.info(f"NCR {ncr.ncr_number} approved by user {current_user.id}")
    return ncr


@router.patch("/{ncr_id}/void", response_model=NCROut)
def void_ncr(
    ncr_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles([Role.PM])),
):
    ncr = db.query(models.NonConformanceReport).filter(
        models.NonConformanceReport.id == ncr_id
    ).first()
    if not ncr:
        raise HTTPException(404, "NCR not found.")
    if ncr.status == NCRStatus.closed:
        raise HTTPException(409, "Cannot void a closed NCR.")

    ncr.status = NCRStatus.voided
    db.commit()
    db.refresh(ncr)
    logger.info(f"NCR {ncr.ncr_number} voided by PM {current_user.id}")
    return ncr
