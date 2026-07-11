"""
LLM Router — call_llm(task_type, prompt)

A thin abstraction so every agent calls this function, not a model directly.
Swapping models per-task, adding new providers, or upgrading to paid tiers
only requires changes here, never inside agent code.

Task routing strategy:
  - "compliance" / "reasoning" → Gemini (long context window, better structured comparison)
  - "chat" / "rfi"            → Groq/Llama 3 (low latency, feels snappy in chat UI on stage)
"""

import os
import asyncio
from enum import Enum
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage


class TaskType(str, Enum):
    COMPLIANCE = "compliance"   # Compliance Agent: structured reasoning over long spec sections
    REASONING = "reasoning"     # General deep reasoning tasks
    CHAT = "chat"               # RFI chat UI: prioritise low latency
    RFI = "rfi"                 # RFI Agent: same as chat
    EMBED = "embed"             # Not routed to an LLM — handled by SentenceTransformers


# --- Model Initialisation ---
# Models are lazy-initialised so the app doesn't crash on startup if a key is missing.

def _get_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY is not set in the environment.")
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",  # Update to available 2026 model
        google_api_key=api_key,
        temperature=0.1,  # Low temperature for deterministic compliance checking
    )


def _get_groq():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set in the environment.")
    return ChatGroq(
        model="llama-3.1-8b-instant",  # Fast, free-tier Llama 3.1 on Groq
        groq_api_key=api_key,
        temperature=0.3,
    )


# --- Rate-limit resilient retry wrapper ---
# Both Gemini and Groq free tiers throttle hard on RPM/RPD.
# This catches HTTP 429s and backs off exponentially before retrying.
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _invoke_with_retry(model, prompt: str) -> str:
    response = model.invoke([HumanMessage(content=prompt)])
    return response.content


# --- Public Interface ---

def call_llm(task_type: TaskType, prompt: str) -> str:
    """
    Route a prompt to the correct LLM based on task type.
    Falls back to Gemini if Groq key is missing, and vice versa.
    """
    if task_type in (TaskType.COMPLIANCE, TaskType.REASONING):
        try:
            model = _get_gemini()
        except EnvironmentError:
            # Graceful fallback if only one key is configured during dev
            model = _get_groq()
    elif task_type in (TaskType.CHAT, TaskType.RFI):
        try:
            model = _get_groq()
        except EnvironmentError:
            model = _get_gemini()
    else:
        raise ValueError(f"Unsupported task type for call_llm: {task_type}")

    return _invoke_with_retry(model, prompt)


async def call_llm_async(task_type: TaskType, prompt: str) -> str:
    """Async wrapper — use this from FastAPI endpoints to avoid blocking the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, call_llm, task_type, prompt)
