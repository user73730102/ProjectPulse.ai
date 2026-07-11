"""
agents/rfi_agent.py

LangGraph-based RFI (Request for Information) Agent.

Workflow:
  1. embed_question    — Embed the user's question locally
  2. retrieve_context  — pgvector similarity search over all SpecSections
  3. generate_answer   — Groq/Llama 3 answers with mandatory citations
  4. save_entry        — Log Q&A + citations to RFIEntry table

Design:
  - Groq is used here (not Gemini) for low latency — chat UI must feel snappy
  - Citations are MANDATORY: every answer must reference source document + page
  - If retrieval finds nothing useful, agent says so rather than hallucinating
"""

import logging
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

import models
import database
from embeddings.embedder import similarity_search_vector
from llm_router import call_llm, TaskType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent State
# ---------------------------------------------------------------------------

class RFIState(TypedDict):
    question: str
    asked_by_user_id: Optional[int]
    retrieved_chunks: list[dict]
    answer: Optional[str]
    citations: list[dict]
    saved_entry_id: Optional[int]
    error: Optional[str]


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

def retrieve_context(state: RFIState) -> RFIState:
    """
    pgvector similarity search — find the top-8 most relevant spec sections
    for the user's question.
    """
    db: Session = database.SessionLocal()
    try:
        query_vector = similarity_search_vector(state["question"])

        results = (
            db.query(models.SpecSection)
            .filter(models.SpecSection.embedding.isnot(None))
            .order_by(models.SpecSection.embedding.cosine_distance(query_vector))
            .limit(8)
            .all()
        )

        # Also search NCR deviation descriptions (stored as text in NCR table)
        # This lets the agent answer "why was X rejected?" questions
        ncr_keywords = ["why", "rejected", "ncr", "non-conformance", "deviation", "failed"]
        if any(kw in state["question"].lower() for kw in ncr_keywords):
            ncrs = (
                db.query(models.NonConformanceReport)
                .order_by(models.NonConformanceReport.created_at.desc())
                .limit(5)
                .all()
            )
            ncr_context = [
                {
                    "id": None,
                    "clause_number": f"NCR-{n.ncr_number}",
                    "clause_title": f"Non-Conformance: {n.severity}",
                    "content": f"NCR {n.ncr_number}: {n.deviation_description}",
                    "page_number": None,
                    "document_id": None,
                    "document_name": "NCR Register",
                }
                for n in ncrs
            ]
        else:
            ncr_context = []

        chunks = [
            {
                "id": r.id,
                "clause_number": r.clause_number,
                "clause_title": r.clause_title,
                "content": r.content,
                "page_number": r.page_number,
                "document_id": r.document_id,
                "document_name": None,  # Loaded below
            }
            for r in results
        ]

        # Enrich with document names for citations
        doc_ids = {c["document_id"] for c in chunks if c["document_id"]}
        if doc_ids:
            docs = db.query(models.Document).filter(models.Document.id.in_(doc_ids)).all()
            doc_map = {d.id: d for d in docs}
            for chunk in chunks:
                chunk["document_name"] = doc_map[chunk["document_id"]].original_name if chunk["document_id"] in doc_map else "Unknown Document"
                chunk["file_path"] = doc_map[chunk["document_id"]].file_path if chunk["document_id"] in doc_map else None

        all_context = chunks + ncr_context
        logger.info(f"Retrieved {len(all_context)} context chunks for question: '{state['question'][:80]}'")
        return {**state, "retrieved_chunks": all_context, "error": None}

    except Exception as e:
        logger.error(f"Context retrieval failed: {e}")
        return {**state, "retrieved_chunks": [], "error": str(e)}
    finally:
        db.close()


def generate_answer(state: RFIState) -> RFIState:
    """
    Groq/Llama 3 generates a cited answer from the retrieved context.
    Citations are MANDATORY — agent must not answer from training data.
    """
    chunks = state.get("retrieved_chunks", [])

    if not chunks:
        return {
            **state,
            "answer": "I couldn't find relevant information in the project documents to answer this question. Please ensure specification documents have been uploaded and processed.",
            "citations": [],
        }

    # Format context with clear source labels and truncate massive chunks
    # (SentenceTransformers only embeds the first 512 tokens anyway)
    context_text = "\n\n".join([
        f"[SOURCE {i+1}: {c.get('clause_number') or 'Section'} — {c.get('clause_title') or ''}"
        f" | Document: {c.get('document_name') or 'Project Document'}"
        f" | Page: {c.get('page_number') or 'N/A'}]\n{c['content'][:1200]}..."
        for i, c in enumerate(chunks[:4])
    ])

    prompt = f"""You are the ProjectPulse AI assistant for a Data Centre EPC project. 
You answer questions based ONLY on the project documents provided below.

IMPORTANT RULES:
1. Only answer from the provided sources. Do not use general knowledge.
2. Every factual claim must cite its source using [SOURCE N] notation.
3. If the sources don't contain enough information, say so clearly.
4. Be concise but complete. Use markdown formatting for readability.

PROJECT DOCUMENTS (retrieved context):
{context_text}

QUESTION: {state['question']}

ANSWER (cite sources using [SOURCE N]):"""

    try:
        answer = call_llm(TaskType.CHAT, prompt)

        # Build structured citation list from chunks used
        citations = [
            {
                "document_id": c.get("document_id"),
                "document_name": c.get("document_name"),
                "file_path": c.get("file_path"),
                "clause_id": c.get("id"),
                "clause_number": c.get("clause_number"),
                "page": c.get("page_number"),
                "excerpt": c["content"][:200] + "..." if len(c["content"]) > 200 else c["content"],
            }
            for c in chunks[:5]  # Top 5 as primary citations
        ]

        return {**state, "answer": answer, "citations": citations}

    except Exception as e:
        logger.error(f"RFI answer generation failed: {e}")
        return {**state, "error": f"Answer generation failed: {str(e)}"}


def save_entry(state: RFIState) -> RFIState:
    """Save the Q&A + citations to the RFIEntry log table."""
    if state.get("error") and not state.get("answer"):
        return state

    db: Session = database.SessionLocal()
    try:
        entry = models.RFIEntry(
            question=state["question"],
            answer=state.get("answer"),
            citations=state.get("citations", []),
            asked_by=state.get("asked_by_user_id"),
            retrieved_chunk_ids=[c["id"] for c in state.get("retrieved_chunks", []) if c.get("id")],
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        logger.info(f"RFI entry {entry.id} saved.")
        return {**state, "saved_entry_id": entry.id}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save RFI entry: {e}")
        return {**state, "error": f"Failed to save RFI entry: {str(e)}"}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Graph definition
# ---------------------------------------------------------------------------

def build_rfi_graph() -> StateGraph:
    graph = StateGraph(RFIState)

    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("save_entry", save_entry)

    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "generate_answer")
    graph.add_edge("generate_answer", "save_entry")
    graph.add_edge("save_entry", END)

    return graph.compile()


rfi_graph = build_rfi_graph()


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def run_rfi_query(question: str, user_id: Optional[int] = None) -> dict:
    """
    Run the full RFI workflow for a question.
    Returns state with answer + citations.

    Usage:
        result = run_rfi_query("Why was the UPS submittal rejected?", user_id=2)
        print(result["answer"])
        print(result["citations"])
    """
    initial_state: RFIState = {
        "question": question,
        "asked_by_user_id": user_id,
        "retrieved_chunks": [],
        "answer": None,
        "citations": [],
        "saved_entry_id": None,
        "error": None,
    }
    return rfi_graph.invoke(initial_state)
