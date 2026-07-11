"""
SQLAlchemy models for Phase 1.

All relationships use plain foreign keys — no graph DB needed.
Neo4j is deferred to Phase 2 for multi-hop graph queries.

Entity relationships:
  Document --< SpecSection   (one spec doc has many clause chunks)
  Document --< Submittal     (one submittal doc per submittal)
  SpecSection --< NCR        (an NCR references the violated clause)
  Submittal --< NCR          (an NCR references the failing submittal)
  User --< NCR               (who raised / approved the NCR)
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Text, Float,
    DateTime, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from database import Base
import enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UserRole(str, enum.Enum):
    contractor = "contractor"
    engineer = "engineer"
    auditor = "auditor"
    pm = "pm"


class DocumentType(str, enum.Enum):
    specification = "specification"
    submittal = "submittal"
    drawing = "drawing"
    test_report = "test_report"
    other = "other"


class SubmittalStatus(str, enum.Enum):
    pending = "pending"
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"
    resubmit_required = "resubmit_required"


class NCRStatus(str, enum.Enum):
    draft = "draft"           # AI generated, not yet reviewed
    pending_review = "pending_review"
    approved = "approved"     # Confirmed by engineer/pm
    closed = "closed"
    voided = "voided"


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(SAEnum(UserRole), default=UserRole.engineer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ncrs_raised = relationship("NonConformanceReport", back_populates="raised_by_user", foreign_keys="NonConformanceReport.raised_by")
    ncrs_approved = relationship("NonConformanceReport", back_populates="approved_by_user", foreign_keys="NonConformanceReport.approved_by")


# ---------------------------------------------------------------------------
# Documents (source files — specs, submittals, drawings)
# ---------------------------------------------------------------------------

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500), nullable=False)
    original_name = Column(String(500), nullable=False)
    # Local disk path (Phase 1). Replace with S3 URL in Phase 2.
    file_path = Column(String(1000), nullable=False)
    doc_type = Column(SAEnum(DocumentType), nullable=False)
    project_id = Column(String(100), nullable=True, index=True)  # For multi-project support later
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    page_count = Column(Integer, nullable=True)
    is_processed = Column(Boolean, default=False)  # False until ingestion worker completes

    spec_sections = relationship("SpecSection", back_populates="document")
    submittals = relationship("Submittal", back_populates="source_document")


# ---------------------------------------------------------------------------
# Spec Sections (extracted clauses — chunked from spec Documents)
# ---------------------------------------------------------------------------

class SpecSection(Base):
    __tablename__ = "spec_sections"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    clause_number = Column(String(50), nullable=True)   # e.g. "3.2.1"
    clause_title = Column(String(500), nullable=True)   # e.g. "UPS Battery Runtime"
    content = Column(Text, nullable=False)               # Full extracted text of the clause
    page_number = Column(Integer, nullable=True)         # Source page for citations
    # 384-dim vector from all-MiniLM-L6-v2 (SentenceTransformers)
    embedding = Column(Vector(384), nullable=True)
    chunk_index = Column(Integer, default=0)             # Position within document

    document = relationship("Document", back_populates="spec_sections")
    ncrs = relationship("NonConformanceReport", back_populates="violated_clause")


# ---------------------------------------------------------------------------
# Submittals (vendor-submitted documents to be checked against specs)
# ---------------------------------------------------------------------------

class Submittal(Base):
    __tablename__ = "submittals"

    id = Column(Integer, primary_key=True, index=True)
    submittal_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    vendor_name = Column(String(255), nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)  # Source PDF
    spec_section_ref = Column(String(100), nullable=True)  # e.g. "16600" — which spec section it's for
    submitted_value = Column(Text, nullable=True)           # Extracted submitted spec value
    status = Column(SAEnum(SubmittalStatus), default=SubmittalStatus.pending)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    source_document = relationship("Document", back_populates="submittals")
    ncrs = relationship("NonConformanceReport", back_populates="submittal")


# ---------------------------------------------------------------------------
# Non-Conformance Reports (AI-drafted, human-approved)
# ---------------------------------------------------------------------------

class NonConformanceReport(Base):
    __tablename__ = "ncrs"

    id = Column(Integer, primary_key=True, index=True)
    ncr_number = Column(String(100), unique=True, nullable=False, index=True)
    submittal_id = Column(Integer, ForeignKey("submittals.id"), nullable=False, index=True)
    clause_id = Column(Integer, ForeignKey("spec_sections.id"), nullable=False, index=True)
    raised_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    required_value = Column(Text, nullable=True)    # What the spec says
    submitted_value = Column(Text, nullable=True)   # What the vendor submitted
    deviation_description = Column(Text, nullable=False)  # AI-generated deviation summary
    severity = Column(String(50), nullable=True)    # e.g. "Critical", "Major", "Minor"
    status = Column(SAEnum(NCRStatus), default=NCRStatus.draft)
    ai_confidence = Column(Float, nullable=True)    # 0.0–1.0 confidence score from LLM

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    submittal = relationship("Submittal", back_populates="ncrs")
    violated_clause = relationship("SpecSection", back_populates="ncrs")
    raised_by_user = relationship("User", back_populates="ncrs_raised", foreign_keys=[raised_by])
    approved_by_user = relationship("User", back_populates="ncrs_approved", foreign_keys=[approved_by])


# ---------------------------------------------------------------------------
# RFI Entries (logged Q&A from the RFI Agent)
# ---------------------------------------------------------------------------

class RFIEntry(Base):
    __tablename__ = "rfi_entries"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    # List of dicts: [{"document_id": 1, "clause_id": 3, "page": 12, "excerpt": "..."}]
    citations = Column(JSON, nullable=True)
    asked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Track which chunks were retrieved (for debugging retrieval quality)
    retrieved_chunk_ids = Column(JSON, nullable=True)
