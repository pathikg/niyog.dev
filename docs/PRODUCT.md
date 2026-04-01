# Product — User Journeys & Personas

## Personas

### HR / Recruiter (Company Side)
- Works at a company, needs to hire talent
- Hates writing JDs from scratch, hates sifting through 500 irrelevant resumes
- Wants: post a job fast, see relevant candidates, make decisions with data

### Candidate
- Looking for jobs or passively open
- Hates filling the same form on every platform, hates black-hole applications
- Wants: build profile once, see relevant jobs, know when companies are interested

---

## User Journeys

### Journey 1: HR Creates a Job Opening

```
HR logs in
  → Lands on company dashboard
  → Clicks "New Opening"
  → Chat interface opens: "Tell me about the role you're hiring for"
  → HR describes in natural language:
      "We need a senior backend engineer, 3-5 years,
       Python/Go, knows distributed systems, 20-30 LPA"
  → AI generates a full JD in rich editable format
  → HR edits inline (Notion-like block editor)
  → HR clicks "Finalize"
  → System extracts structured attributes from JD:
      - Role, seniority, experience range
      - Required skills, nice-to-have skills
      - CTC range, location, remote policy
  → HR reviews extracted attributes, corrects if needed
  → Job goes live on platform
```

**Key design decisions:**
- Chat-first, not form-first. The form is the output, not the input.
- Extraction happens after human editing, so we extract from the final version.
- HR can always override extracted attributes manually.

### Journey 2: Candidate Onboards

```
Candidate signs up
  → Prompted: "Upload your resume to get started"
  → Uploads resume (PDF/DOCX)
  → AI extracts everything it can:
      - Name, contact, current role, experience
      - Skills, education, past companies
      - Current CTC (if mentioned), notice period
  → Extracted data shown in chat:
      "Here's what I found. Let's fill in the gaps."
  → Conversational flow asks about:
      - Expected CTC range
      - Preferred locations / remote preference
      - What they're looking for in next role
      - Any dealbreakers
  → Candidate can edit any extracted field in the chat
  → Profile is built progressively, saved persistently
  → Candidate lands on dashboard with complete profile
```

**Key design decisions:**
- Resume upload is step 1, always. It reduces friction massively.
- Chat fills gaps, doesn't re-ask what the resume already told us.
- Profile is persistent — candidate can come back and update via chat anytime.

### Journey 3: Candidate Browses Jobs

```
Candidate on dashboard
  → Sees job listings (filtered by their profile match)
  → Each listing shows: match score, why they match, any gaps
  → Can filter/search manually too
  → Clicks on a job → sees full JD + their fit analysis
  → Can "Express Interest" (soft apply)
```

### Journey 4: HR Reviews Candidates

```
HR on job dashboard
  → Sees three sections for a posted job:

  [Strong Matches]
    Candidates who pass all hard filters AND have high semantic match.
    Sorted by overall fit score.

  [Semantic Matches]
    Candidates who match on skills/experience semantically
    but may not pass every hard filter exactly.

  [Stretch Candidates]
    Candidates who are strong skill matches but miss on
    experience or CTC by small margins.
    "This candidate has 2.5 yrs (you asked for 3+) but
     matches 95% on skills."

  → HR can view candidate profiles
  → HR "Shortlists" candidates
  → Candidate sees "Company X is interested" on their dashboard
```

**Key design decisions:**
- Three-tier display is the product differentiator. Most platforms show a flat ranked list.
- Stretch candidates surface hidden gems that hard-filter-only platforms miss.
- Transparency: candidates know when they're shortlisted. No black hole.

### Journey 5: HR Views Analytics

```
HR on company dashboard
  → Per-job analytics:
      - Total applicants, match distribution
      - Skills gap analysis (what skills are candidates missing most)
      - CTC distribution of matched candidates
      - Time-to-fill estimates
  → Cross-job analytics:
      - Which roles attract most candidates
      - Company's overall hiring pipeline health
```

---

## What we are NOT building (for now)
- Messaging / chat between HR and candidate (phase later)
- Interview scheduling
- Offer management
- ATS integration
- Multi-company teams / permissions
- Candidate skill assessments / tests
