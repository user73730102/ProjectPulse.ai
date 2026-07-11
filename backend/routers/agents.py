"""
routers/agents.py

FastAPI router exposing the AI agent endpoints.

Routes:
  POST /agents/compliance/run/{submittal_id}  — Trigger Compliance Agent
  POST /agents/rfi/query                      — Ask the RFI Agent a question
  GET  /agents/rfi/history                    — List past RFI Q&A entries
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

import models, database
from auth import get_current_user, require_roles, Role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["AI Agents"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ComplianceRunResponse(BaseModel):
    submittal_id: int
    ncrs_created: int
    ncr_ids: list[int]
    error: Optional[str] = None


class RFIQueryRequest(BaseModel):
    question: str


class Citation(BaseModel):
    document_id: Optional[int]
    document_name: Optional[str]
    file_path: Optional[str] = None
    clause_number: Optional[str]
    page: Optional[int]
    excerpt: Optional[str]


class RFIQueryResponse(BaseModel):
    entry_id: Optional[int]
    question: str
    answer: Optional[str]
    citations: list[Citation]
    error: Optional[str] = None


class RFIHistoryItem(BaseModel):
    id: int
    question: str
    answer: Optional[str]
    citations: Optional[list]
    created_at: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/compliance/run/{submittal_id}", response_model=ComplianceRunResponse)
async def run_compliance_check(
    submittal_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles([Role.ENGINEER, Role.PM, Role.AUDITOR])),
):
    """
    Trigger the Compliance Agent on a submittal.
    Runs synchronously (returns result directly — fast enough for demo).
    For large batches, this can be moved to a Celery background task.
    """
    sub = db.query(models.Submittal).filter(models.Submittal.id == submittal_id).first()
    if not sub:
        raise HTTPException(404, f"Submittal {submittal_id} not found.")

    # Import here to avoid loading models at app startup (slow embedding model)
    from agents.compliance_agent import run_compliance_check as run_agent

    try:
        result = run_agent(submittal_id)

        if result.get("error"):
            return ComplianceRunResponse(
                submittal_id=submittal_id,
                ncrs_created=0,
                ncr_ids=[],
                error=result["error"],
            )

        return ComplianceRunResponse(
            submittal_id=submittal_id,
            ncrs_created=len(result.get("saved_ncr_ids", [])),
            ncr_ids=result.get("saved_ncr_ids", []),
        )

    except Exception as e:
        logger.error(f"Compliance agent error: {e}")
        raise HTTPException(500, f"Agent execution failed: {str(e)}")


@router.post("/rfi/query", response_model=RFIQueryResponse)
async def query_rfi_agent(
    payload: RFIQueryRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Ask the RFI Agent a question. Returns answer + source citations.
    """
    from agents.rfi_agent import run_rfi_query

    try:
        result = run_rfi_query(
            question=payload.question,
            user_id=current_user.id,
        )

        return RFIQueryResponse(
            entry_id=result.get("saved_entry_id"),
            question=payload.question,
            answer=result.get("answer"),
            citations=[Citation(**c) for c in result.get("citations", [])],
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"RFI agent error: {e}")
        raise HTTPException(500, f"RFI agent failed: {str(e)}")


@router.post("/simulate-world")
async def simulate_world_state(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_roles([Role.PM])),
):
    """
    Clears existing mock data and uses Gemini to generate a highly realistic 
    new world state (tasks, equipment, shipments, and test records).
    """
    from agents.simulator_agent import generate_world_simulation
    
    result = generate_world_simulation()
    if "error" in result:
        raise HTTPException(500, f"Simulation failed: {result['error']}")
    return result

@router.get("/rfi/history", response_model=list[RFIHistoryItem])
def get_rfi_history(
    limit: int = 20,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return recent RFI Q&A history."""
    entries = (
        db.query(models.RFIEntry)
        .order_by(models.RFIEntry.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        RFIHistoryItem(
            id=e.id,
            question=e.question,
            answer=e.answer,
            citations=e.citations,
            created_at=e.created_at.isoformat() if e.created_at else "",
        )
        for e in entries
    ]
