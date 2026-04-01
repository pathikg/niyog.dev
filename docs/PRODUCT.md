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

Two paths depending on whether HR is starting fresh or has an existing JD.

```
HR logs in
  → Lands on company dashboard
  → Clicks "New Opening"
  → Two options:

  [Option A: Start from scratch]
  → Chat interface opens: "Tell me about the role you're hiring for"
  → HR describes in natural language:
      "We need a senior backend engineer, 3-5 years,
       Python/Go, knows distributed systems, 20-30 LPA"
  → AI generates a full JD in rich editable format (Notion-like)

  [Option B: Paste existing JD / template]
  → HR pastes their existing JD text or company template
  → System renders it in the same Notion-like block editor
  → Same editing experience from here on

  → HR edits in Notion-like block editor
  → Two chat interfaces available:
      1. JD-level chat: "Make the tone more casual" / "Add a section about culture"
      2. Selection-level chat: HR selects a paragraph or section →
         "Improve the writing" / "Fix grammar" / "Make this more specific" /
         "Rewrite this for senior candidates"
  → HR clicks "Post"
  → Job goes live immediately. Extraction, embedding, matching all happen
    in background. HR is done.
```

**Key design decisions:**
- Chat-first OR paste-first. Both paths converge to the same editor.
- HR may already have templates from previous hiring or other platforms — don't force them to re-describe via chat. Let them paste and edit.
- Two chat layers: JD-level (structural changes, tone, sections) and selection-level (inline improvements, grammar, rewriting). This is the "AI writing assistant" experience.
- No attribute review step. Extraction happens in background. HR posts and is done.

### Journey 2: Candidate Onboards

```
Candidate signs up
  → Prompted: "Upload your resume to get started"
  → Uploads resume (PDF/DOCX)
  → AI extracts everything it can (synchronous — candidate sees results live):
      - Name, contact, current role, experience
      - Skills, education, past companies
      - Current CTC (if mentioned)
  → Extracted data shown in chat:
      "Here's what I found from your resume. Take a look and correct
       anything that's off."
  → Candidate reviews each field, corrects what's wrong:
      "My experience is actually 3 years including freelance"
      (Every correction is tracked — AI vs user, for improving extraction)
  → Conversational flow asks about things NOT in the resume:
      - Expected CTC range
      - Notice period (+ is it negotiable?)
      - Reason for job switch
      - Actively interviewing? Offers in hand?
      - Preferred locations / remote preference
      - What they're looking for in next role
      - Any dealbreakers
  → If candidate says "skip" or "not applicable" → stored as null, move on.
    Don't loop or rephrase.
  → Profile is built progressively, saved persistently
  → Candidate lands on dashboard with complete profile
```

**Key design decisions:**
- Resume upload is step 1, always. It reduces friction massively.
- Extraction is synchronous — candidate needs to see and verify.
- Chat fills gaps, doesn't re-ask what the resume already told us.
- Every correction is training data for better extraction prompts.
- Profile is persistent — candidate can come back and update anytime.

### Journey 3: Candidate Updates Profile

```
Candidate returns after weeks/months
  → Two paths:

  [Upload new resume]
  → System detects if it's the same file (hash check) — skip if unchanged
  → If new resume: re-extract, show diff from previous profile
      "Looks like you've moved to a new role at Company Y.
       I've updated your experience. Anything else changed?"
  → Only ask about what's NEW or DIFFERENT. Don't re-onboard.

  [Update via chat]
  → "I got a raise, my CTC is now 22L"
  → "I'm now open to onsite roles in Bangalore"
  → "Add Docker to my skills"
  → System updates the specific fields mentioned

  → Previous profile is versioned (snapshot saved)
  → Background: re-normalize, re-embed, re-match
  → Candidate sees updated matches on dashboard
```

**Key design decisions:**
- Profile versioning: every update creates a snapshot. Nothing is lost.
- Resume dedup: same file uploaded = no re-extraction.
- For updates, don't re-onboard. Surgical updates only.
- Candidate can update any field via chat without going through the full flow.

### Journey 4: Candidate Searches & Browses Jobs

```
Candidate on dashboard
  → Two ways to find jobs:

  [Browse]
  → Sees job listings ranked by profile match
  → Each listing shows: match score, why they match, any gaps
  → Can filter manually (location, CTC range, remote, etc.)

  [Chat-based search]
  → Chat interface: "Show me backend roles at FAANG companies"
  → "Find me remote Python jobs paying above 25 LPA"
  → "Any startups hiring for distributed systems?"
  → AI translates natural language into filters + semantic search
  → Results shown inline in chat, can be saved/bookmarked

  → Clicks on a job → sees full JD + their personal fit analysis
  → Can "Express Interest" (soft apply)
```

**Key design decisions:**
- Chat search is the differentiator. Candidates can express preferences in ways that hard filters can't capture ("FAANG companies", "startups like Razorpay", "no consulting firms").
- Browse is always available as fallback — not everyone wants to chat.
- Fit analysis on each job is personalized to their profile.

### Journey 5: HR Reviews Candidates

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

### Journey 6: HR Views Analytics

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
