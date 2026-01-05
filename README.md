# Millennium BD Resume Search Platform (Assignment Deliverable)

This project parses resumes (PDF/DOCX) into structured JSON using an LLM API (or a mock parser),
stores normalized fields in a database, and provides a **Streamlit** web app for BD users to
search/filter candidates and visualize distributions.

## Features
- Batch upload PDF/DOCX resumes
- Text extraction (PDF via `pdfplumber`, DOCX via `python-docx`)
- LLM-based structured parsing into a strict JSON schema (Pydantic validated)
- Normalization for:
  - Geography markets (US/Europe/APAC)
  - Investment approach (Fundamental vs Systematic)
  - Sectors
  - Skills buckets (programming/data/ml/finance/tools)
- Storage in **SQLite** (easy to run locally). Designed so you can switch to Postgres later.
- Search & filter UI:
  - Geo market, country, approach, asset class, sector, role, years experience, degree level
  - Keyword search (skills/employers/bullets)
  - Candidate profile page (standardized view + evidence snippets)
  - Export results to CSV
- Insights dashboard:
  - Candidate distribution by geo/approach/sector
  - Experience histogram
  - Top skills / universities

## Quickstart

### 1) Create environment
```bash
cd millennium_bd_resume_platform
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure LLM provider
Copy `.env.example` to `.env`.

**Option A (recommended for demo):** use mock parser (no API needed)
- set `LLM_PROVIDER=mock`

**Option B:** use an OpenAI-compatible chat-completions endpoint (any vendor offering this interface)
- set `LLM_PROVIDER=openai_compatible`
- set `LLM_API_BASE=https://<your-endpoint>/v1`
- set `LLM_API_KEY=...`
- set `LLM_MODEL=...` (e.g., a JSON-mode capable model)

> This repo intentionally avoids hard-coding any single vendor. If you want an adapter for a specific
> vendor, add a new provider in `core/llm_providers/`.

### 3) Run the Streamlit app
```bash
streamlit run app/Home.py
```

## Data & DB
- Uploaded resumes are stored in `data/resumes/`
- SQLite DB: `data/db/candidates.sqlite`
- Parsed JSON is stored as canonical record + normalized columns for fast filtering.

## Scalability Notes (what you'd do next)
- Replace SQLite with Postgres (SQLAlchemy already used)
- Add async parsing: Celery/RQ + Redis
- Add a search index: OpenSearch/Elasticsearch for nested queries + faster keyword search
- Add embeddings (pgvector/OpenSearch kNN) for semantic search
- Add dedupe (email/LinkedIn hash), RBAC, audit logs, encryption at rest

## Folder Structure
- `app/` Streamlit UI
- `core/` parsing, schema, db, normalization, search
- `scripts/` CLI helpers (batch ingest/export)

