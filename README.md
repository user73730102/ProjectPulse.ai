# ProjectPulse AI 🏗️⚡

**AI-powered compliance, RFI, and project intelligence for Data Centre EPC delivery.**

ProjectPulse AI transforms the fragmented, highly manual Engineering, Procurement, and Construction (EPC) lifecycle into an automated, agent-driven workflow. Built for complex, large-scale projects like Data Centers, our platform ensures 100% compliance traceability and eliminates critical path delays.

---

## 🚀 The Problem
In modern EPC delivery, teams are drowning in data:
- **Engineers** spend weeks manually verifying vendor submittals against dense 1,000-page specifications.
- **Project Managers** are blindsided by supply chain delays.
- **Quality Auditors** struggle to draft accurate Non-Conformance Reports (NCRs) from scattered commissioning data.

## 💡 Our AI Solution
ProjectPulse utilizes specialized AI Agents to automate the lifecycle:
1. **The Engineer Agent (Documents & Submittals):** Ingests PDF specifications, chunks them using semantic vector embeddings, and automatically cross-checks vendor equipment submittals to instantly flag deviations.
2. **The PM Agent (Supply Chain Risk):** Monitors procurement data against the project schedule to predict delays before they impact the critical path.
3. **The Auditor Agent (Commissioning QA):** Listens to field test results. If a test fails, the AI autonomously drafts a highly detailed Non-Conformance Report (NCR) for immediate review.
4. **The RFI Assistant:** A conversational RAG interface allowing instant querying of the entire project corpus.

---

## 🛠️ Tech Stack
- **Frontend:** Next.js, React 19, TailwindCSS (Glassmorphism UI)
- **Backend:** FastAPI (Python 3.11), SQLAlchemy
- **AI & LLMs:** LangChain, Groq (Llama 3 for ultra-fast inference), Google Gemini
- **Database:** PostgreSQL with `pgvector` for semantic search
- **Document Processing:** Docling (Layout-aware PDF parsing & OCR)
- **Infrastructure:** Docker, Docker Compose, Caddy (Reverse Proxy & Auto-SSL)

---

## 💻 Running Locally

We have containerized the entire stack for a seamless 1-click setup.

### Prerequisites
- Docker & Docker Compose
- API Keys for Groq and Gemini (placed in `.env`)

### Quick Start
1. Clone the repository:
   ```bash
   git clone https://github.com/user73730102/ProjectPulse.ai.git
   cd ProjectPulse.ai
   ```
2. Start the services:
   ```bash
   docker-compose up -d --build
   ```
3. The platform is now running at `http://localhost:3000` (or behind Caddy at your configured domain).

*Note: The backend automatically handles database initialization and data seeding on startup.*

---

## 🏆 Live Demo
**Access the live platform here:** [https://project-pulse.duckdns.org](https://project-pulse.duckdns.org)

For a guided evaluation of the platform, click on any of the **Fast Access** role cards on the login screen. A tailored onboarding modal will guide you through the AI features specific to your selected persona.
