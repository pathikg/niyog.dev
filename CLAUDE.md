# Niyog — Project Context

## What is this?
Niyog is an agentic onboarding platform for hiring. Two sides: companies (HR) and candidates. Both interact through AI-driven conversational flows, not static forms.

## Tech Stack
- **Frontend**: Next.js (App Router)
- **Backend**: FastAPI + LangGraph (Python)
- **Database**: PostgreSQL + pgvector
- **AI**: LLM-powered agentic graphs for JD creation, candidate onboarding, matching

## Core Concepts
- **Agentic flows**: Multi-step AI conversations that produce structured outputs (JDs, profiles)
- **Shared ontology**: JDs and candidate profiles map to the same attribute schema so matching works
- **Three-tier matching**: Hard filters → semantic similarity → stretch candidates

## Project Structure
```
docs/
  PRODUCT.md      — User journeys and personas
  HLD.md          — Architecture and key decisions
  DATA_MODEL.md   — Entities, schemas, shared ontology
  CONTRACTS.md    — Graph inputs/outputs, API contracts
  BLUEPRINT.md    — Phases and progress tracking
```

## Current Phase
Phase 0 — Fresh start. Documentation and architecture in place. No code yet.

## Conventions
- Backend code lives in `backend/`
- Frontend code lives in `frontend/`
- All agentic flows are LangGraph graphs in `backend/app/graphs/`
- API routes in `backend/app/api/routers/`
- Keep graphs decoupled — they communicate through defined contracts, not direct imports
