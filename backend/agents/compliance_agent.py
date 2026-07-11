"""
agents/compliance_agent.py

LangGraph-based Specification Compliance Agent.

Workflow:
  1. receive_submittal    — Load submittal from DB
  2. retrieve_clauses     — pgvector similarity search to find relevant spec clauses
  3. compare_values       — Gemini LLM compares required vs submitted values
  4. generate_ncrs        — Parse LLM output into structured NCR records
  5. save_ncrs            — Persist NCRs to Postgres, update submittal status

Design principles:
  - Deterministic control flow via LangGraph state machine (no hallucinated tool calls)
  - LLM only used at step 3 — everything else is deterministic Python
  - All NCRs start as 'draft' — engineer must approve before they are official
  - Citations always link back to SpecSection.id + page_number
"""

import json
import logging
import re
from typing import TypedDict, Optional, Annotated
from datetime import datetime, timezone

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from pgvector.sqlalchemy import Vector

import models
import database
from embeddings.embedder import similarity_search_vector
from llm_router import call_llm, TaskType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent State
# ---------------------------------------------------------------------------

class ComplianceState(TypedDict):
    submittal_id: int
    submittal: Optional[dict]
    retrieved_clauses: list[dict]
    llm_analysis: Optional[str]
    parsed_ncrs: list[dict]
    saved_ncr_ids: list[int]
    error: Optional[str]


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

def receive_submittal(state: ComplianceState) -> ComplianceState:
    """Load the submittal from Postgres."""
    db: Session = database.SessionLocal()
    try:
        sub = db.query(models.Submittal).filter(
            models.Submittal.id == state["submittal_id"]
        ).first()

        if not sub:
            return {**state, "error": f"Submittal {state['submittal_id']} not found."}

        return {
            **state,
            "submittal": {
                "id": sub.id,
                "submittal_number": sub.submittal_number,
                "title": sub.title,
                "vendor_name": sub.vendor_name,
                "spec_section_ref": sub.spec_section_ref,
                "submitted_value": sub.submitted_value,
            },
            "error": None,
        }
    finally:
        db.close()


def retrieve_clauses(state: ComplianceState) -> ComplianceState:
    """
    pgvector similarity search — find the top-5 most relevant spec clauses
    for this submittal's content.
    """
    if state.get("error"):
        return state

    db: Session = database.SessionLocal()
    try:
        sub = state["submittal"]
        # Build a rich query string combining title + submitted value
        query_text = f"{sub['title']} {sub['spec_section_ref'] or ''} {sub['submitted_value'] or ''}"
        query_vector = similarity_search_vector(query_text)

        # pgvector cosine distance search — <=> operator
        # Returns top 5 most semantically similar spec clauses
        results = (
            db.query(models.SpecSection)
            .filter(models.SpecSection.embedding.isnot(None))
            .order_by(models.SpecSection.embedding.cosine_distance(query_vector))
            .limit(5)
            .all()
        )

        # Also pull clauses matching the spec_section_ref directly (exact match boost)
        if sub.get("spec_section_ref"):
            direct_matches = (
                db.query(models.SpecSection)
                .filter(models.SpecSection.clause_number.like(f"{sub['spec_section_ref']}%"))
                .all()
            )
            # Merge without duplicates
            seen_ids = {r.id for r in results}
            for dm in direct_matches:
                if dm.id not in seen_ids:
                    results.append(dm)

        clauses = [
            {
                "id": c.id,
                "clause_number": c.clause_number,
                "clause_title": c.clause_title,
                "content": c.content,
                "page_number": c.page_number,
            }
            for c in results
        ]

        logger.info(f"Retrieved {len(clauses)} clauses for submittal {sub['submittal_number']}")
        return {**state, "retrieved_clauses": clauses}
    finally:
        db.close()


def compare_values(state: ComplianceState) -> ComplianceState:
    """
    Send submittal + relevant clauses to Gemini for structured compliance comparison.
    Returns raw LLM JSON response.
    """
    if state.get("error"):
        return state

    sub = state["submittal"]
    clauses = state["retrieved_clauses"]

    if not clauses:
        return {**state, "error": "No relevant spec clauses found for this submittal. Upload a specification document first."}

    # Format clauses for the prompt
    clauses_text = "\n\n".join([
        f"CLAUSE {c['clause_number'] or 'N/A'} — {c['clause_title'] or 'Untitled'} (Page {c['page_number'] or '?'}):\n{c['content']}"
        for c in clauses
    ])

    prompt = f"""You are a senior Data Centre EPC Quality Engineer reviewing a vendor submittal for specification compliance.

SUBMITTAL DETAILS:
- Number: {sub['submittal_number']}
- Title: {sub['title']}
- Vendor: {sub['vendor_name'] or 'Unknown'}
- Spec Section Reference: {sub['spec_section_ref'] or 'N/A'}
- Submitted Value / Description:
{sub['submitted_value'] or 'No submitted value provided.'}

RELEVANT SPECIFICATION CLAUSES:
{clauses_text}

TASK:
Compare the submitted value against each relevant specification clause.
For each deviation or non-conformance found, output a JSON array entry.
If there are NO deviations, output an empty array: []

Output ONLY valid JSON in this exact format (no markdown, no explanation):
[
  {{
    "clause_id": <integer — the clause ID from the list above>,
    "clause_number": "<string>",
    "required_value": "<exact requirement from the spec clause>",
    "submitted_value": "<what the vendor submitted>",
    "deviation_description": "<clear, professional description of the non-conformance. Include specific numbers and cite the spec clause.>",
    "severity": "<Critical|Major|Minor>",
    "confidence": <float 0.0-1.0>
  }}
]

SEVERITY GUIDE:
- Critical: Functional failure risk, safety issue, or >20% shortfall on a key metric.
- Major: Significant deviation from spec that requires formal response from vendor.
- Minor: Small deviation that may be accepted with conditions or waiver.
"""

    try:
        raw_response = call_llm(TaskType.COMPLIANCE, prompt)
        logger.info(f"LLM compliance analysis complete for {sub['submittal_number']}")
        return {**state, "llm_analysis": raw_response}
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return {**state, "error": f"LLM analysis failed: {str(e)}"}


def generate_ncrs(state: ComplianceState) -> ComplianceState:
    """Parse the LLM JSON response into structured NCR dicts."""
    if state.get("error"):
        return state

    raw = state.get("llm_analysis", "")

    # Strip markdown code fences if the LLM ignored instructions
    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        ncr_list = json.loads(raw)
    except json.JSONDecodeError as e:
        # Try to extract JSON array from response if there's surrounding text
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                ncr_list = json.loads(match.group())
            except Exception:
                return {**state, "error": f"Failed to parse LLM response as JSON: {e}\nRaw: {raw[:500]}"}
        else:
            return {**state, "error": f"LLM returned non-JSON response: {raw[:500]}"}

    if not isinstance(ncr_list, list):
        return {**state, "parsed_ncrs": [], "llm_analysis": raw}

    logger.info(f"Parsed {len(ncr_list)} NCR(s) from LLM response.")
    return {**state, "parsed_ncrs": ncr_list}


def save_ncrs(state: ComplianceState) -> ComplianceState:
    """Persist parsed NCRs to Postgres and update submittal status."""
    if state.get("error"):
        return state

    ncr_list = state.get("parsed_ncrs", [])
    submittal_id = state["submittal_id"]
    saved_ids = []

    db: Session = database.SessionLocal()
    try:
        # Count existing NCRs to generate sequential numbers
        existing_count = db.query(models.NonConformanceReport).count()

        for i, ncr_data in enumerate(ncr_list):
            ncr_number = f"NCR-{datetime.now().year}-{existing_count + i + 1:03d}"

            # Validate clause_id exists
            clause_id = ncr_data.get("clause_id")
            if clause_id:
                clause_exists = db.query(models.SpecSection).filter(
                    models.SpecSection.id == clause_id
                ).first()
                if not clause_exists:
                    # Try to find by clause_number
                    clause_by_num = db.query(models.SpecSection).filter(
                        models.SpecSection.clause_number == ncr_data.get("clause_number")
                    ).first()
                    clause_id = clause_by_num.id if clause_by_num else None

            ncr = models.NonConformanceReport(
                ncr_number=ncr_number,
                submittal_id=submittal_id,
                clause_id=clause_id or 1,  # fallback — shouldn't happen with real data
                required_value=ncr_data.get("required_value", ""),
                submitted_value=ncr_data.get("submitted_value", ""),
                deviation_description=ncr_data.get("deviation_description", ""),
                severity=ncr_data.get("severity", "Major"),
                status=models.NCRStatus.draft,
                ai_confidence=ncr_data.get("confidence", 0.0),
            )
            db.add(ncr)
            db.flush()
            saved_ids.append(ncr.id)

        # Update submittal status
        sub = db.query(models.Submittal).filter(models.Submittal.id == submittal_id).first()
        if sub:
            if ncr_list:
                sub.status = models.SubmittalStatus.under_review
            else:
                sub.status = models.SubmittalStatus.approved

        db.commit()
        logger.info(f"Saved {len(saved_ids)} NCR(s) for submittal {submittal_id}")
        return {**state, "saved_ncr_ids": saved_ids}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save NCRs: {e}")
        return {**state, "error": f"Failed to save NCRs to database: {str(e)}"}
    finally:
        db.close()


def handle_error(state: ComplianceState) -> ComplianceState:
    """Terminal node for error states — logs and returns state as-is."""
    logger.error(f"Compliance agent error: {state.get('error')}")
    return state


# ---------------------------------------------------------------------------
# Graph definition
# ---------------------------------------------------------------------------

def _should_continue(state: ComplianceState) -> str:
    """Route to error handler if any step failed."""
    return "error" if state.get("error") else "continue"


def build_compliance_graph() -> StateGraph:
    graph = StateGraph(ComplianceState)

    graph.add_node("receive_submittal", receive_submittal)
    graph.add_node("retrieve_clauses", retrieve_clauses)
    graph.add_node("compare_values", compare_values)
    graph.add_node("generate_ncrs", generate_ncrs)
    graph.add_node("save_ncrs", save_ncrs)
    graph.add_node("handle_error", handle_error)

    graph.set_entry_point("receive_submittal")

    # After each node, check for errors
    for node in ["receive_submittal", "retrieve_clauses", "compare_values", "generate_ncrs"]:
        graph.add_conditional_edges(
            node,
            _should_continue,
            {"error": "handle_error", "continue": {
                "receive_submittal": "retrieve_clauses",
                "retrieve_clauses": "compare_values",
                "compare_values": "generate_ncrs",
                "generate_ncrs": "save_ncrs",
            }[node]},
        )

    graph.add_edge("save_ncrs", END)
    graph.add_edge("handle_error", END)

    return graph.compile()


# Singleton compiled graph
compliance_graph = build_compliance_graph()


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def run_compliance_check(submittal_id: int) -> dict:
    """
    Run the full compliance workflow for a submittal.
    Returns the final state including saved NCR IDs.

    Usage:
        result = run_compliance_check(submittal_id=1)
        print(result["saved_ncr_ids"])
    """
    initial_state: ComplianceState = {
        "submittal_id": submittal_id,
        "submittal": None,
        "retrieved_clauses": [],
        "llm_analysis": None,
        "parsed_ncrs": [],
        "saved_ncr_ids": [],
        "error": None,
    }

    final_state = compliance_graph.invoke(initial_state)
    return final_state
