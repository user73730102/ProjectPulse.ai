"""
routers/documents.py

FastAPI router for document upload and ingestion.

Routes:
  POST /documents/upload   — Upload a PDF, trigger async ingestion
  GET  /documents/         — List all documents
  GET  /documents/{id}     — Get document details + processing status
  GET  /documents/{id}/chunks — List extracted spec sections for a document
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models
import database
from auth import get_current_user, require_roles, Role
from models import DocumentType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
MAX_FILE_SIZE_MB = 100


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class DocumentOut(BaseModel):
    id: int
    filename: str
    original_name: str
    doc_type: str
    project_id: Optional[str]
    page_count: Optional[int]
    is_processed: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True


class SpecSectionOut(BaseModel):
    id: int
    clause_number: Optional[str]
    clause_title: Optional[str]
    content: str
    page_number: Optional[int]
    chunk_index: int

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Background ingestion task
# ---------------------------------------------------------------------------

def _run_ingestion(document_id: int, file_path: str):
    """
    Background task: parse document → chunk → embed → store.
    Runs after the upload endpoint returns so the API stays responsive.
    """
    from parsers.docling_extractor import extract_spec_chunks
    from embeddings.embedder import embed_batch

    db = database.SessionLocal()
    try:
        logger.info(f"Starting ingestion for document {document_id}: {file_path}")

        # 1. Extract chunks
        chunks = extract_spec_chunks(file_path)
        if not chunks:
            logger.warning(f"No chunks extracted from document {document_id}")
            return

        # 2. Batch embed all chunk texts
        texts = [c.content for c in chunks]
        logger.info(f"Embedding {len(texts)} chunks...")
        embeddings = embed_batch(texts)

        # 3. Store SpecSections with embeddings
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            section = models.SpecSection(
                document_id=document_id,
                clause_number=chunk.clause_number,
                clause_title=chunk.title,
                content=chunk.content,
                page_number=chunk.page,
                embedding=embedding,
                chunk_index=i,
            )
            db.add(section)

        # 4. Mark document as processed and update page count
        doc = db.query(models.Document).filter(models.Document.id == document_id).first()
        if doc:
            doc.is_processed = True
            if chunks:
                max_page = max(c.page for c in chunks)
                doc.page_count = max_page

        db.commit()
        logger.info(f"✅ Ingestion complete for document {document_id}: {len(chunks)} chunks stored.")

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ingestion failed for document {document_id}: {e}")
        # Force is_processed to True so the UI stops polling infinitely
        try:
            doc = db.query(models.Document).filter(models.Document.id == document_id).first()
            if doc:
                doc.is_processed = True
                db.commit()
        except:
            pass
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: DocumentType = Form(...),
    project_id: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Upload a document. Saves to local disk and triggers background ingestion.
    Returns immediately — check is_processed flag to know when ingestion is done.
    """
    # Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}")

    # Save to local disk under uploads/<doc_type>/
    sub_dir = os.path.join(UPLOAD_DIR, doc_type.value + "s")
    os.makedirs(sub_dir, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(sub_dir, unique_name)

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File exceeds maximum size of {MAX_FILE_SIZE_MB}MB.")

    with open(file_path, "wb") as f:
        f.write(contents)

    # Create Document record
    doc = models.Document(
        filename=unique_name,
        original_name=file.filename or unique_name,
        file_path=file_path,
        doc_type=doc_type,
        project_id=project_id,
        uploaded_by=current_user.id,
        is_processed=False,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Kick off background ingestion (non-blocking)
    background_tasks.add_task(_run_ingestion, doc.id, file_path)

    logger.info(f"Document {doc.id} uploaded by user {current_user.id}, ingestion queued.")
    return doc


@router.get("/", response_model=list[DocumentOut])
def list_documents(
    project_id: Optional[str] = None,
    doc_type: Optional[DocumentType] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Document)
    if project_id:
        query = query.filter(models.Document.project_id == project_id)
    if doc_type:
        query = query.filter(models.Document.doc_type == doc_type)
    return query.order_by(models.Document.uploaded_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found.")
    return doc


@router.get("/{document_id}/chunks", response_model=list[SpecSectionOut])
def get_document_chunks(
    document_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return all extracted spec sections for a document (for lineage inspection)."""
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found.")
    if not doc.is_processed:
        raise HTTPException(409, "Document is still being processed. Try again shortly.")

    sections = (
        db.query(models.SpecSection)
        .filter(models.SpecSection.document_id == document_id)
        .order_by(models.SpecSection.chunk_index)
        .all()
    )
    return sections

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles([Role.PM])), # PM / Admins only
):
    """Delete a document and all its associated data (chunks, submittals, ncrs)."""
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found.")

    try:
        # Delete related SpecSections (Chunks)
        db.query(models.SpecSection).filter(models.SpecSection.document_id == document_id).delete()
        
        # If it's a submittal document, delete associated Submittals and their NCRs
        submittals = db.query(models.Submittal).filter(models.Submittal.document_id == document_id).all()
        for sub in submittals:
            db.query(models.NonConformanceReport).filter(models.NonConformanceReport.submittal_id == sub.id).delete()
            db.delete(sub)
            
        # Delete the file from local disk if it exists
        if os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except Exception as e:
                logger.warning(f"Could not remove file {doc.file_path}: {e}")

        # Delete the document record
        db.delete(doc)
        db.commit()
        
        logger.info(f"Document {document_id} deleted by PM {current_user.id}")
        return {"detail": "Document successfully deleted"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(500, f"Failed to delete document: {e}")
