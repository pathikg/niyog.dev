# Contracts — Graph Inputs & Outputs

Every agentic flow (LangGraph graph) has a defined contract: what it receives, what it produces, and what side effects it has. This is the glue between components.

---

## 1. JD Creation Graph

**Trigger**: HR clicks "New Opening" and starts chatting.

**Input**:
```python
{
    "company_id": "uuid",
    "hr_user_id": "uuid",
    "messages": [
        # Conversation history — HR describing what they need
        {"role": "user", "content": "I need a senior backend engineer..."}
    ]
}
```

**Output**:
```python
{
    "jd_raw": "string",          # Full JD text (markdown)
    "jd_structured": {            # Block-structured for the editor
        "blocks": [
            {"type": "heading", "content": "Senior Backend Engineer"},
            {"type": "section", "label": "About the Role", "content": "..."},
            {"type": "section", "label": "Requirements", "content": "..."},
            {"type": "section", "label": "Nice to Have", "content": "..."},
            {"type": "section", "label": "Compensation", "content": "..."},
        ]
    },
    "conversation_id": "uuid"     # For resuming if needed
}
```

**Side effects**: Saves conversation state via LangGraph checkpointing.

**Handoff**: Output feeds into the Rich Editor. After HR edits, the final `jd_raw` goes to the JD Extraction graph.

---

## 2. JD Extraction Graph

**Trigger**: HR clicks "Finalize" on the edited JD.

**Input**:
```python
{
    "job_id": "uuid",
    "jd_raw": "string",           # The final, human-edited JD text
    "jd_structured": { ... }      # Optional — structured blocks if available
}
```

**Output**:
```python
{
    "job_attributes": {
        "role_title": "string",
        "seniority": "enum",
        "experience_range": {"min": int, "max": int},
        "skills_required": [{"name": "string", "importance": "enum"}],
        "ctc_range": {"min": int, "max": int, "currency": "string"},
        "location": {"cities": [], "remote_policy": "enum"},
        "education": {"min_degree": "string"},
    },
    "embedding": [float],          # Dense vector from full JD text
    "confidence_flags": [           # Anything the AI wasn't sure about
        {"field": "ctc_range", "reason": "Not explicitly mentioned in JD"}
    ]
}
```

**Side effects**: Updates Job record with extracted attributes. Generates and stores embedding in pgvector.

**Handoff**: HR reviews `job_attributes` + `confidence_flags`, corrects, confirms. Then matching engine triggers.

---

## 3. Candidate Onboarding Graph

**Trigger**: Candidate signs up and uploads resume.

**Input**:
```python
{
    "candidate_id": "uuid",
    "resume_file": "bytes | file_path",    # Uploaded resume
    "messages": [                           # Ongoing conversation (empty at start)
    ]
}
```

**Internal steps**:
1. **Extract from resume** → parse PDF/DOCX → LLM extraction → structured data
2. **Present to candidate** → "Here's what I found: [extracted]. Let me ask a few more things."
3. **Gap-filling conversation** → ask about expected CTC, preferences, dealbreakers
4. **Candidate edits** → they correct anything via chat
5. **Finalize** → produce complete profile

**Output**:
```python
{
    "profile": {
        "resume_raw": "string",            # Extracted text from resume
        "resume_structured": { ... },      # Parsed resume sections
        "current_role": "string",
        "total_experience": {"value": float, "unit": "years"},
        "skills": [{"name": "string", "proficiency": "enum"}],
        "current_ctc": {"value": int, "currency": "string"},
        "expected_ctc": {"min": int, "max": int, "currency": "string"},
        "location": { ... },
        "education": { ... },
        "preferences": {
            "looking_for": "string",       # Free text — what they want next
            "dealbreakers": ["string"],
        },
        "notice_period_days": int
    },
    "conversation_id": "uuid"
}
```

**Side effects**: 
- Saves conversation state (persistent — candidate can resume later)
- Creates/updates CandidateProfile record
- Triggers Profile Extraction on completion

**Handoff**: Output feeds into Profile Extraction graph for normalization + embedding.

---

## 4. Profile Extraction Graph

**Trigger**: Candidate completes onboarding OR updates their profile.

**Input**:
```python
{
    "candidate_id": "uuid",
    "profile": { ... }            # Full profile from onboarding graph
}
```

**Output**:
```python
{
    "profile_attributes": {
        # Normalized to shared ontology (see DATA_MODEL.md)
        "skills": [{"name": "normalized_name", "category": "string", "proficiency": "enum"}],
        "seniority": "enum",
        # ... all other normalized fields
    },
    "embedding": [float],          # Dense vector from full profile text
    "normalization_log": [         # What got normalized
        {"original": "ReactJS", "normalized": "React"},
        {"original": "Golang", "normalized": "Go"}
    ]
}
```

**Side effects**: Updates ProfileAttributes. Stores embedding. Triggers matching for all active jobs.

---

## 5. Matching Engine

**Trigger**: New job posted, job updated, new profile completed, profile updated.

**Input**:
```python
# For job-triggered matching (find candidates for a job):
{
    "mode": "job_to_candidates",
    "job_id": "uuid",
    "job_attributes": { ... },
    "job_embedding": [float]
}

# For profile-triggered matching (find jobs for a candidate):
{
    "mode": "candidate_to_jobs",
    "candidate_id": "uuid",
    "profile_attributes": { ... },
    "profile_embedding": [float]
}
```

**Output**:
```python
{
    "matches": [
        {
            "job_id": "uuid",
            "candidate_id": "uuid",
            "tier": "strong | semantic | stretch",
            "overall_score": 0.87,
            "semantic_score": 0.91,
            "hard_filter_results": {
                "experience": {"pass": true, "detail": "3 yrs in range 3-5"},
                "ctc": {"pass": true, "detail": "22L in range 20-30L"},
                "skills_required": {"pass": true, "detail": "4/5 required skills"},
                "location": {"pass": false, "detail": "Candidate: Remote only, Job: Hybrid"}
            },
            "breakdown": {
                "why_matched": "Strong Python + distributed systems experience",
                "gaps": ["Location mismatch — candidate prefers remote"],
                "stretch_reason": null   # or "Experience 2.5yr vs required 3yr"
            }
        }
    ]
}
```

**Side effects**: Creates/updates Match records.

---

## Graph ↔ API Mapping

| API Endpoint | Graph Invoked | Notes |
|---|---|---|
| `POST /api/jobs/create/chat` | JD Creation | Streaming response |
| `POST /api/jobs/{id}/finalize` | JD Extraction | Sync, returns attributes for review |
| `POST /api/candidates/onboard` | Candidate Onboarding | Streaming, persistent |
| `POST /api/candidates/{id}/profile/refresh` | Profile Extraction | Async, triggers matching |
| `POST /api/matching/compute` | Matching Engine | Async, can be triggered manually |
| `GET /api/jobs/{id}/matches` | — | Reads Match table, no graph |
| `GET /api/candidates/{id}/matches` | — | Reads Match table, no graph |
