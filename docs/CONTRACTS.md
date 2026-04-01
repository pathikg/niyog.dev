# Contracts — Graph Inputs & Outputs

Every agentic flow (LangGraph graph) has a defined contract: what it receives, what it produces, and what side effects it has. This is the glue between components.

**Processing rule**: Graphs that interact with the user (JD Creation, Candidate Onboarding) stream in real-time. **Resume extraction is synchronous** — candidate needs to see, verify, and correct extracted fields live. Everything after the candidate is done (normalization, embedding generation, matching) runs as **background jobs**.

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

**Handoff**: Output feeds into the Rich Editor. After HR edits and clicks "Post", the job is saved and JD Extraction fires in the background. HR is done — no review step.

---

## 2. JD Extraction Graph

**Trigger**: HR clicks "Post" on the edited JD. Runs in **background** — HR doesn't wait.

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
        "department": "string | null",
        "experience_range": {"min": int, "max": int, "unit": "years"},

        "skills": [
            {
                "raw": "string",               # Exactly as written in JD
                "normalized": "string | list",  # Normalized via cache/LLM
                "category": "string",
                "importance": "required | nice_to_have",
                "note": "string | null"         # "either one", "bonus", etc.
            }
        ],

        "ctc_range": {"min": int, "max": int, "currency": "string"},

        "location": {
            "cities": ["string"],
            "remote_policy": "enum",
            "relocation_support": "bool | null"
        },

        "education": {
            "raw": "string",                   # Exact text from JD
            "parsed": {
                "degrees": ["string"],         # ["masters", "mba"]
                "fields": ["string"],          # ["CS", "IT"]
                "equivalence": "strict | experience_accepted | not_specified",
                "strictness": "required | preferred | not_mentioned"
            }
        },

        "extras": {                            # Everything else worth capturing
            # company_stage, team_size, benefits, visa, travel, etc.
            # Schema is intentionally loose — extract what's there
        }
    },

    "embedding": [float],

    "confidence_flags": [
        # Logged for internal debugging, NOT shown to HR
        {"field": "ctc_range", "reason": "Not explicitly mentioned in JD"},
        {"field": "education.equivalence", "reason": "JD says 'or equivalent' but unclear what qualifies"}
    ],

    "normalization_log": [
        {"raw": "Golang", "normalized": "Go", "cache_hit": true},
        {"raw": "event-driven architecture", "normalized": "Event-Driven Architecture", "cache_hit": false}
    ]
}
```

**Side effects** (all background):
- Updates Job record with extracted attributes + embedding
- Updates skill normalization cache with any new mappings
- Triggers matching engine for this job against all active candidate profiles

**Handoff**: None to HR. Extraction → embedding → matching all cascade in background. HR sees matched candidates appear on their dashboard.

---

## 3. Candidate Onboarding Graph

**Trigger**: Candidate signs up and uploads resume, OR returns to update profile.

**Key principle**: Resume extraction is **synchronous** — candidate sees extracted fields live, corrects them in chat, and every correction is tracked. This gives us two things: accurate profiles AND training signal for improving extraction prompts.

**Input**:
```python
{
    "candidate_id": "uuid",
    "resume_file": "bytes | file_path | null",  # Null if returning to update via chat
    "messages": [],                              # Ongoing conversation (empty at start)
    "is_update": false,                          # True if updating existing profile
    "existing_profile": "{ ... } | null"         # Current profile if updating
}
```

**Internal steps**:
1. **Extract from resume (synchronous)** → parse PDF/DOCX → LLM extraction → structured data
2. **Present extracted fields to candidate** → "Here's what I found:" with each field editable
3. **Candidate reviews + corrects** → changes any field via chat. Every correction is tracked (see Extraction Corrections below).
4. **Gap-filling conversation** → ask about things NOT in the resume:
   - Expected CTC range
   - Notice period (+ is it negotiable?)
   - Reason for job switch / leaving current role
   - Are they actively interviewing? Any offers in hand?
   - Location preferences / remote preference
   - What they're looking for in next role
   - Dealbreakers
5. **Candidate confirms** → "Looks good" → profile finalized
6. **Background kicks off** → normalization, embedding, matching

**Chat behavior rules**:
- **Never re-ask what the resume already told us.** If we extracted 2.5 years experience, don't ask "how many years of experience do you have?" — show it, let them correct if wrong.
- **If candidate says "not applicable" or "I don't have that" or "skip" → store null, move on.** Don't loop or rephrase the question.
- **For updates**: Show what changed from previous version. Only ask about gaps in the NEW data, don't re-onboard from scratch.
- **Batch related questions.** Don't ask one question per message — group 2-3 related ones: "What's your expected CTC range, and what's your notice period? Is it negotiable?"
- **Respect the user's final word.** If AI extracted "2.5 years" and candidate says "it's 3 years including freelance" — the profile stores 3 years. The user's version is truth. AI's version goes to correction log.

**Output**:
```python
{
    "profile": {
        "resume_raw": "string",
        "resume_sections": {               # Parsed sections from PDF/DOCX
            "sections": [
                {"heading": "Experience", "content": "...", "order": 1},
                {"heading": "Skills", "content": "...", "order": 2}
            ],
            "raw_text": "Full extracted text...",
            "file_hash": "sha256:abc123..."   # Dedup — skip re-extraction if same file
        },

        "current_role": "string",
        "total_experience": {"value": float, "unit": "years"},

        "work_history": [
            {
                "company": "string",
                "role": "string",
                "duration": {"value": float, "unit": "years"},
                "raw_description": "string",
                "skills_used": ["string"]    # Raw, not normalized yet
            }
        ],

        "skills": [
            {
                "raw": "string",
                "proficiency": "enum",
                "years_used": "float | null",
                "context": "string | null"
            }
        ],

        "current_ctc": {"value": int, "currency": "string", "includes_esop": "bool | null"},
        "expected_ctc": {"min": int, "max": int, "currency": "string"},

        "location": {
            "current_city": "string",
            "open_to": ["string"],
            "remote_preference": "enum",
            "willing_to_relocate": "bool"
        },

        "education": {
            "raw": "string",
            "parsed": {
                "degree": "string",
                "field": "string",
                "institution": "string",
                "year": "int | null"
            }
        },

        "notice_period": {
            "days": "int | null",
            "negotiable": "bool",
            "note": "string | null"          # "Can negotiate to 15 days for the right role"
        },

        "job_switch": {
            "reason": "string | null",       # Why switching — chat-sourced, never on resume
            "urgency": "active | open_to_offers | not_looking | urgent",
            "actively_interviewing": "bool",
            "offers_in_hand": "int | null"
        },

        "preferences": {
            "looking_for": "string",
            "dealbreakers": ["string"],
            "preferred_company_stage": ["string"],
            "preferred_team_size": "string | null"
        },

        "extras": {
            "languages_spoken": ["string"],
            "certifications": ["string"],
            "portfolio_url": "string | null"
            # Anything else the resume or chat revealed
        }
    },
    "corrections": [                         # Every field the candidate corrected
        {
            "field": "total_experience",
            "extracted_value": {"value": 2.5, "unit": "years"},
            "user_value": {"value": 3, "unit": "years"},
            "user_reason": "including freelance work",
            "resume_source_text": "2.5 years at Startup X...",
            "timestamp": "2026-04-01T12:00:00Z"
        },
        {
            "field": "skills",
            "action": "added",               # added | removed | modified
            "user_value": {"raw": "Docker", "proficiency": "intermediate"},
            "user_reason": "used in all projects but not listed on resume",
            "timestamp": "2026-04-01T12:01:00Z"
        }
    ],
    "conversation_id": "uuid",
    "version_trigger": "initial_onboarding | resume_upload | chat_update"
}
```

**Side effects**:
- Saves conversation state (persistent — candidate can resume later)
- Creates/updates CandidateProfile record with **user-corrected values** (user's version is truth)
- Stores extraction corrections in `ExtractionCorrection` table (training signal)
- If updating: snapshots current profile as ProfileVersion before overwriting
- Kicks off normalization + embedding + matching as **background jobs** (candidate doesn't wait)

**Handoff**: Candidate sees "Profile saved!" and lands on dashboard. Normalization, embedding, matching all happen in background.

### Extraction Corrections — The Feedback Loop

Every correction is a data point for improving extraction. Over time:

```
Collect corrections
    ↓
Analyze patterns: "extraction consistently underestimates experience
                    when freelance work is involved"
    ↓
Update extraction prompts: "When extracting experience, look for
                            freelance, contract, and consulting
                            work that may not be listed as
                            traditional employment"
    ↓
Extraction improves → fewer corrections → better UX
```

This is stored in `ExtractionCorrection` table (see DATA_MODEL.md). It's not used in real-time — it's a harness for prompt engineering. Periodically review corrections, spot patterns, update prompts.

---

## 4. Profile Extraction Graph

**Trigger**: Candidate completes onboarding OR updates profile. Runs in **background**.

**Input**:
```python
{
    "candidate_id": "uuid",
    "profile": { ... },           # Full profile from onboarding graph
    "previous_version": "{ ... } | null"  # For diffing
}
```

**Output**:
```python
{
    "profile_attributes": {
        # Same structure as profile, but with normalized skills
        "skills": [
            {
                "raw": "K8s",
                "normalized": "Kubernetes",
                "category": "infra/orchestration",
                "proficiency": "intermediate",
                "years_used": 1,
                "context": "managed production clusters"
            }
        ],
        "seniority": "enum",       # Inferred from experience + role history
        # ... all other fields carried forward
    },
    "embedding": [float],
    "normalization_log": [
        {"raw": "K8s", "normalized": "Kubernetes", "cache_hit": true},
        {"raw": "FastAPI", "normalized": "FastAPI", "cache_hit": false}
    ],
    "diff_from_previous": {
        # What changed from last version — null if first version
        "added_skills": ["Docker"],
        "removed_skills": [],
        "experience_change": {"old": 2.5, "new": 3.0},
        "ctc_change": {"old": {"min": 18, "max": 22}, "new": {"min": 20, "max": 25}},
        "new_work_history_entries": [{"company": "New Corp", "role": "Senior Engineer"}]
    }
}
```

**Side effects** (all background):
- Updates ProfileAttributes with normalized data + embedding
- Saves ProfileVersion snapshot with diff
- Updates skill normalization cache with any new mappings
- Triggers re-matching for all active jobs

---

## 5. Matching Engine

**Trigger**: New job posted, job updated, new profile completed, profile updated. Always runs in **background**.

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
                "skills_required": {"pass": true, "detail": "4/5 required skills matched"},
                "location": {"pass": false, "detail": "Candidate: Remote only, Job: Hybrid"}
            },
            "semantic_breakdown": {
                "education_fit": 0.78,
                "domain_fit": 0.92,
                "seniority_fit": 0.85
            },
            "explanation": {
                "why_matched": "Strong Python + distributed systems experience, relevant startup background",
                "gaps": ["Location mismatch — candidate prefers remote"],
                "stretch_reason": null
            }
        }
    ]
}
```

**Side effects**: Creates/updates Match records. Old matches from previous profile version are archived (not deleted — useful for analytics).

---

## Processing Pipeline — What's Sync vs Background

```
=== HR SIDE ===                        === CANDIDATE SIDE ===

HR chats about role [SYNC/streaming]   Candidate uploads resume [SYNC]
    ↓                                        ↓
AI generates JD [SYNC/streaming]       Resume extraction [SYNC — candidate sees results]
    ↓                                        ↓
HR edits JD [SYNC]                     Candidate reviews + corrects fields [SYNC]
    ↓                                        ↓
HR clicks "Post" → DONE               Gap-filling chat [SYNC/streaming]
    ↓                                        ↓
--- HR leaves, background starts ---   Candidate confirms → DONE
    ↓                                        ↓
[BG] JD Extraction                     --- Candidate leaves, background starts ---
    ↓                                        ↓
[BG] Generate embedding               [BG] Snapshot ProfileVersion
    ↓                                        ↓
[BG] Skill norm cache update           [BG] Store extraction corrections
    ↓                                        ↓
[BG] Match against all                 [BG] Profile normalization
     active profiles                        ↓
    ↓                                  [BG] Generate embedding
[BG] Store matches                          ↓
                                       [BG] Skill norm cache update
                                            ↓
                                       [BG] Match against all active jobs
                                            ↓
                                       [BG] Store matches
```

Both sides converge on the Match table. Users never wait for background work. The critical difference: **candidate-side extraction is synchronous** because the candidate needs to see, verify, and correct extracted data live. Everything after confirmation is background.

---

## Graph ↔ API Mapping

| API Endpoint | Graph Invoked | Sync/Async | Notes |
|---|---|---|---|
| `POST /api/jobs/create/chat` | JD Creation | Streaming | Real-time chat with HR |
| `POST /api/jobs/{id}/post` | JD Extraction | **Async** | Returns immediately, extraction in background |
| `POST /api/candidates/onboard` | Candidate Onboarding | Streaming | Real-time chat with candidate |
| `POST /api/candidates/{id}/resume` | Candidate Onboarding (update) | Streaming | Re-onboard with new resume |
| `POST /api/candidates/{id}/profile/refresh` | Profile Extraction | **Async** | Background re-extraction |
| `POST /api/matching/compute` | Matching Engine | **Async** | Manual trigger if needed |
| `GET /api/jobs/{id}/matches` | — | Sync | Reads Match table |
| `GET /api/candidates/{id}/matches` | — | Sync | Reads Match table |
| `GET /api/candidates/{id}/versions` | — | Sync | Reads ProfileVersion history |

---

## Normalization Flow (cross-cutting)

Both JD Extraction and Profile Extraction use the same normalization path:

```
Extracted raw skill string
    ↓
Check skill_norm_cache (case-insensitive lookup)
    ↓
Cache HIT → use normalized_name
Cache MISS → LLM normalizes → insert into cache → use result
    ↓
Store both raw + normalized in attributes
    ↓
Log in normalization_log (for debugging / review)
```

This means the normalization cache is a **shared, growing resource** that gets smarter with every extraction. No manual curation needed at the start; it builds itself.
