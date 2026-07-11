# ProjectPulse AI — EPC Intelligence Platform

## Backend Structure

```
backend/
├── main.py              # FastAPI app entry point, all routers registered here
├── database.py          # SQLAlchemy engine, session, get_db dependency
├── models.py            # All SQLAlchemy models (User, Document, SpecSection, Submittal, NCR, RFI)
├── auth.py              # JWT auth, role constants, require_roles() dependency factory
├── llm_router.py        # call_llm(task_type, prompt) — routes to Gemini or Groq
├── init_db.py           # One-time DB setup: enable pgvector + create tables
├── seed_data.py         # Realistic DC EPC sample data for development/testing
├── requirements.txt     # Python dependencies
├── .env.example         # Copy to .env and fill in secrets
├── parsers/
│   └── docling_extractor.py   # Docling-first PDF extractor (PyMuPDF + Tesseract fallback)
├── embeddings/
│   └── embedder.py            # Local SentenceTransformers embedding (384-dim, free)
└── routers/
    ├── documents.py     # Upload, list, get, chunks endpoints
    ├── submittals.py    # Submittal CRUD + status management
    └── ncr.py           # NCR list, detail, approve, void endpoints
```

## Quick Start (once Docker is installed)

```bash
# 1. Start the database
docker-compose up -d

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Copy env file and fill in your API keys
cp .env.example .env

# 4. Create tables and enable pgvector
python init_db.py

# 5. Load sample data
python seed_data.py

# 6. Start the API
uvicorn main:app --reload --port 8000
```

API docs will be at: http://localhost:8000/docs

## Test Credentials (from seed_data.py)

| Role | Email | Password |
|------|-------|----------|
| PM | admin@projectpulse.ai | admin123 |
| Engineer | engineer@projectpulse.ai | engineer123 |
| Auditor | auditor@projectpulse.ai | auditor123 |
| Contractor | contractor@eaton.com | contractor123 |

## Free API Keys

- **Gemini** (for Compliance Agent): https://aistudio.google.com/app/apikey
- **Groq** (for RFI chat speed): https://console.groq.com
