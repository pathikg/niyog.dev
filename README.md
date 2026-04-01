# Niyog — Multi-Tenant HR Talent Onboarding Platform

> **नियोग** (niyog) — Sanskrit for "hiring, employment, assignment"

A conversational AI-powered platform that enables HR teams to design custom talent intake schemas and guide candidates through personalized onboarding flows.

## Features

- 🎯 **Schema Design Agent** — HR teams design custom intake schemas via natural conversation
- 💬 **Talent Onboarding Agent** — Candidates complete onboarding through conversational dialogue (not forms)
- 🔄 **Schema Versioning** — Full historical audit, multi-company support, zero table migrations
- 💾 **Persistent Sessions** — Resume onboarding mid-flow, powered by LangGraph
- 📁 **File Uploads** — Collect resumes and documents seamlessly
- 🔐 **Multi-Tenant Isolation** — Complete data isolation per company

## Tech Stack

- **Backend**: FastAPI + Python 3.11+
- **Orchestration**: LangGraph + PostgresSaver
- **Database**: PostgreSQL (JSONB for flexible schemas)
- **LLM**: Claude (Anthropic)
- **Storage**: Supabase Storage (S3-compatible)
- **Frontend**: Next.js 14

## Architecture

### Two LangGraph Loops

1. **HR Schema Graph** (`hr_schema/`)
   - Design schema via natural conversation
   - Iterate on fields interactively
   - Test in sandbox
   - Publish and activate

2. **Talent Onboarding Graph** (`talent_onboarding/`)
   - Conversational question flow
   - Collect answers (text, number, file, date, select)
   - Review and correction handling
   - Off-topic guardrail
   - Save completed profile to DB

### Database Design

- **One `schemas` table** — Each version = one JSONB row. No table migrations.
- **`talent_profiles` table** — JSONB `data` field + FK to schema version for historical audit
- **Partial unique index** enforces exactly one active schema per company
- Full multi-tenant isolation via company_id

See [Plan](/.claude/plans/refactored-jingling-bubble.md) for detailed schema and architecture.

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Node.js 18+
- Anthropic API key
- Supabase project (optional, for file storage)

### Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env with your actual values

# Install dependencies
pip install -e .

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
niyog.dev/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── api/routers/     # FastAPI route handlers
│   │   ├── graphs/          # LangGraph definitions
│   │   │   ├── hr_schema/
│   │   │   └── talent_onboarding/
│   │   ├── services/        # Business logic (storage, DB ops)
│   │   └── utils/           # Helpers (thread IDs, SSE)
│   ├── alembic/             # Database migrations
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks (SSE, uploads)
│   │   └── lib/             # Utilities & types
│   └── package.json
└── README.md
```

## Development Phases

- [ ] Phase 1: Database + migrations + seed data
- [ ] Phase 2: LangGraph checkpointer + minimal graph
- [ ] Phase 3: HR Schema Graph (all nodes)
- [ ] Phase 4: HR API endpoints + SSE streaming
- [ ] Phase 5: Talent Onboarding Graph (all nodes)
- [ ] Phase 6: Talent API endpoints + file uploads
- [ ] Phase 7: Frontend (Next.js chat UIs)

## API Reference

See [Plan](/.claude/plans/refactored-jingling-bubble.md#4-fastapi-endpoint-design) for full API specification.

### Key Endpoints

```
POST   /api/hr/schema/session          # Create HR session
POST   /api/hr/schema/chat             # SSE: HR conversation
GET    /api/hr/schemas                 # List schemas
POST   /api/hr/schemas/{id}/activate   # Activate schema

POST   /api/talent/onboarding/sessions # Create onboarding
POST   /api/talent/onboarding/chat     # SSE: Talent conversation
POST   /api/talent/onboarding/upload   # Upload file
```

## Contributing

- Follow black + ruff style guides (configured in pyproject.toml)
- Write tests for new features
- Update docs when adding endpoints

## License

MIT