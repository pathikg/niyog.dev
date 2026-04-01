# Blueprint — Phases & Progress

> Open this file to know where we are. Check things off as they're built.

---

## Phase 0: Foundation *(current)*
Setup, documentation, architecture decisions.

- [x] Project vision and product journeys documented
- [x] High-level architecture defined
- [x] Data model and shared ontology designed
- [x] Graph contracts specified
- [ ] Backend project scaffolding (FastAPI + LangGraph)
- [ ] Frontend project scaffolding (Next.js)
- [ ] Database setup (Postgres + pgvector)
- [ ] Auth setup (basic — email/password or OAuth)
- [ ] CI/CD pipeline (GitHub Actions — lint, test, deploy)

---

## Phase 1: Candidate Onboarding Flow
The hardest UX problem. If this feels magical, the rest is plumbing.

- [ ] Resume upload endpoint (PDF/DOCX parsing)
- [ ] Resume extraction graph (LLM-powered)
- [ ] Chat interface component (frontend)
- [ ] Conversational onboarding graph (gap-filling)
- [ ] Profile persistence (save/resume conversation)
- [ ] Profile extraction + normalization
- [ ] Candidate dashboard (view/edit profile)
- [ ] Skill normalization table (initial seed)

**Demo milestone**: Candidate uploads resume → chats with AI → complete profile generated.

---

## Phase 2: JD Creation Flow
HR-side agentic experience.

- [ ] JD creation chat interface
- [ ] JD creation graph (requirements → JD draft)
- [ ] Rich JD editor (Notion-like blocks)
- [ ] JD extraction graph (text → structured attributes)
- [ ] HR reviews/confirms extracted attributes
- [ ] Job posting (save + mark active)
- [ ] HR dashboard (list jobs, manage status)

**Demo milestone**: HR describes role in chat → AI generates JD → HR edits → structured attributes extracted.

---

## Phase 3: Matching Engine
Where the two sides connect.

- [ ] Embedding generation for JDs (on finalize)
- [ ] Embedding generation for profiles (on complete)
- [ ] Hard filter matching logic
- [ ] Semantic matching (pgvector cosine similarity)
- [ ] Stretch candidate logic (margin-based relaxation)
- [ ] Three-tier match display for HR
- [ ] Match visibility for candidates ("Company X is interested")
- [ ] Shortlisting action (HR selects candidate)

**Demo milestone**: Post a job + have profiles → see three-tier ranked candidates.

---

## Phase 4: Analytics & Polish
Make it useful day-to-day.

- [ ] Per-job analytics (applicant stats, skills gaps, CTC distribution)
- [ ] Company dashboard analytics
- [ ] Job listings page for candidates (browse + filter)
- [ ] Match score explanation UI ("why you matched")
- [ ] Profile update flow (candidate returns, updates via chat)
- [ ] Email notifications (shortlisted, new matches)
- [ ] Landing page / marketing site

---

## Phase 5+: Future
Not scoped yet. Ideas parking lot.

- [ ] Messaging between HR and candidate
- [ ] Interview scheduling
- [ ] Multi-role company accounts (permissions)
- [ ] ATS integrations (Greenhouse, Lever)
- [ ] Candidate skill assessments
- [ ] Salary benchmarking data
- [ ] Mobile app
- [ ] API for third-party job boards
