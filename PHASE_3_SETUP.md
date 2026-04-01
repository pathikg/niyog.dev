# Phase 3: HR Schema Graph — Full Implementation

This phase completes the HR Schema Design Graph with all nodes and introduces Claude AI for conversational schema extraction.

## What We're Building

**Complete HR Schema Graph:**
```
START → greet_hr 
         ↓
      propose_schema (Claude extracts JSONB from description)
         ↓ [INTERRUPT for HR review]
      classify_hr_intent (Claude classifies: modify|add_field|remove_field|save|activate|other)
         ├─ modify/add_field/remove_field
         │  ↓
         │  update_schema (Claude applies changes)
         │  ↓
         │  [INTERRUPT for HR review]
         │  ↓ [loop back to classify]
         │
         ├─ save
         │  ↓
         │  save_schema (INSERT to DB, get version)
         │  ↓
         │  END
         │
         └─ activate
            ↓
            activate_schema (archive old active, set new to active)
            ↓
            END
```

## New Components (Phase 3)

### Nodes (5 new)

1. **propose_schema.py**
   - Takes: Last HR message describing what they want
   - Calls: Claude to extract structured JSONB schema
   - Returns: current_definition (JSONB), formatted summary message
   - Uses: PROPOSE_SCHEMA_SYSTEM + PROPOSE_SCHEMA_PROMPT

2. **classify_hr_intent.py**
   - Takes: Last HR message
   - Calls: Claude to classify intent
   - Returns: hr_intent in [modify, add_field, remove_field, test, save, activate, other]
   - Uses: CLASSIFY_HR_INTENT_SYSTEM + CLASSIFY_HR_INTENT_PROMPT

3. **update_schema.py**
   - Takes: current_definition + last HR message requesting change
   - Calls: Claude to apply the modification
   - Returns: updated current_definition
   - Uses: UPDATE_SCHEMA_SYSTEM + UPDATE_SCHEMA_PROMPT

4. **save_schema.py**
   - Takes: current_definition + company_id + hr_user_id
   - Action: INSERT into schemas table, get next version
   - Returns: schema_id, current_version, success message
   - DB: Creates new Schema row with status='draft'

5. **activate_schema.py**
   - Takes: schema_id
   - Action: Archive currently active schema, set target to active
   - Returns: success message, published_at timestamp
   - DB: Updates schemas table, enforced by partial unique index

### Routing

**route_on_intent()** function:
- Reads hr_intent from state
- Routes to appropriate next node
- Enables loop-back (update_schema → propose_schema)

### Prompts (New)

All prompts are in `app/graphs/hr_schema/prompts.py`:

- `PROPOSE_SCHEMA_SYSTEM` — Claude extracts JSONB from natural language
- `PROPOSE_SCHEMA_PROMPT` — Template for HR description input
- `CLASSIFY_HR_INTENT_SYSTEM` — Classify intent from message
- `CLASSIFY_HR_INTENT_PROMPT` — Template for intent classification
- `UPDATE_SCHEMA_SYSTEM` — Apply modifications to existing schema
- `UPDATE_SCHEMA_PROMPT` — Template for schema update request
- `FORMAT_SCHEMA_SUMMARY` — Format JSONB as human-readable list
- `FORMAT_SCHEMA_PROMPT` — Template for formatting

## Architecture Changes

### Node Dependencies

Nodes that need database access use SQLAlchemy `session` parameter (FastAPI dependency injection pattern):

```python
async def save_schema(state: HRSchemaState, session: AsyncSession) -> dict:
    # session is auto-injected by FastAPI (Phase 4)
    # For Phase 3 testing, we pass it explicitly
```

### State Updates

Each node returns a dict with partial state updates:

```python
return {
    "current_definition": {...},
    "current_version": 2,
    "phase": "iterating",
    "messages": [AIMessage(...)],
}
```

LangGraph merges these into the full state automatically.

## How Claude Integration Works

### Three Types of Claude Calls

1. **Schema Extraction** (propose_schema)
   - Input: "I want name, email, and salary expectations"
   - Output: JSONB with fields array, greeting_message, completion_message
   - Model: claude-3-5-sonnet-20241022

2. **Intent Classification** (classify_hr_intent)
   - Input: "Can you add a resume field?"
   - Output: Single word from [modify, add_field, remove_field, test, save, activate, other]
   - Model: claude-3-5-sonnet-20241022

3. **Schema Modification** (update_schema)
   - Input: Current JSONB + "add a resume field"
   - Output: Updated JSONB with new field
   - Model: claude-3-5-sonnet-20241022

All use LangChain's `ChatAnthropic` for clean async/await interface.

### JSONB Schema Format

Claude is instructed to produce JSON like:

```json
{
  "fields": [
    {
      "key": "full_name",
      "label": "Full Name",
      "type": "text",
      "required": true,
      "question_hint": "What is your full legal name?"
    },
    {
      "key": "resume",
      "label": "Resume",
      "type": "file",
      "required": true,
      "accepted_mime_types": ["application/pdf"]
    }
  ],
  "greeting_message": "Hi! Welcome to onboarding...",
  "completion_message": "Your profile is complete."
}
```

Field types: text, number, date, select, file

## Files Created

```
backend/
├── app/
│   ├── graphs/
│   │   └── hr_schema/
│   │       ├── nodes/
│   │       │   ├── propose_schema.py         # NEW: Claude extracts JSONB
│   │       │   ├── classify_hr_intent.py     # NEW: Claude classifies intent
│   │       │   ├── update_schema.py          # NEW: Claude modifies JSONB
│   │       │   ├── save_schema.py            # NEW: INSERT to DB
│   │       │   └── activate_schema.py        # NEW: UPDATE status to active
│   │       ├── graph.py                      # UPDATED: wired full graph
│   │       └── prompts.py                    # UPDATED: all prompt templates
│   └── pyproject.toml                        # UPDATED: added langgraph-postgres
└── scripts/
    └── test_hr_schema_graph.py               # NEW: full workflow test
```

## Testing Phase 3

The comprehensive test simulates a real HR workflow:

```bash
cd backend
python scripts/test_hr_schema_graph.py
```

**Test Workflow:**
1. ✅ Greet HR
2. ✅ HR describes schema → Claude extracts
3. ✅ HR requests modification → Claude classifies intent
4. ✅ Schema updated → Claude applies changes
5. ✅ HR saves → INSERT to database
6. ✅ HR activates → UPDATE status to active
7. ✅ Verify DB state (schema is active, fields correct)

**Expected Output:**
```
======================================================================
Testing HR Schema Graph - Full Workflow (Phase 3)
======================================================================

📍 Setup:
  Company: TechCorp (...)
  HR User: hr@techcorp.com
  Thread ID: hr-techcorp-...

🔧 Building graph with AsyncPostgresSaver...
✓ Graph built successfully

1️⃣  Greeting HR (greet_hr node)...
✓ Greeting succeeded
  Phase: proposing
  Message: Hi! I'm here to help you design...

2️⃣  HR describes schema (propose_schema node)...
✓ Schema proposed
  Current definition fields: 3
    - Full Name (text)
    - Years of Experience (number)
    - Expected Salary (number)

3️⃣  HR requests modification (add field)...
✓ Intent classified and schema updated
  Intent: add_field
  Updated fields: 4
    - Full Name (text)
    - Years of Experience (number)
    - Expected Salary (number)
    - Resume (file)

4️⃣  HR saves schema...
✓ Schema saved to database
  Schema ID: ...
  Version: 1
  Phase: done

5️⃣  Verifying database state...
✓ Schema found in database
  Status: draft
  Version: 1
  Fields: 4

6️⃣  HR activates schema...
✓ Schema activated
  Phase: done

7️⃣  Verifying activation in database...
✓ Schema is active in database
  Status: active
  Published at: 2026-04-01 ...

======================================================================
✅ FULL HR SCHEMA WORKFLOW TEST PASSED
======================================================================

Workflow completed:
  1. ✓ Greeted HR user
  2. ✓ Proposed schema from natural language description
  3. ✓ HR requested modification (added field)
  4. ✓ Schema was updated via Claude
  5. ✓ HR saved schema to database (as draft)
  6. ✓ HR activated schema
  7. ✓ Database verified active schema
```

## How to Run

### 1. Ensure Phase 1 & 2 Complete

```bash
cd backend
alembic upgrade head
python scripts/seed_data.py
```

### 2. Install/Update Dependencies

```bash
pip install -e .
# Installs langgraph-checkpoint-postgres and other new deps
```

### 3. Set Environment Variables

```bash
# .env must have:
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql+asyncpg://...
```

### 4. Run Full Workflow Test

```bash
python scripts/test_hr_schema_graph.py
```

## Graph Execution Flow

### Invocation 1: Greeting
```
Input: initial_state (empty messages)
Nodes: greet_hr
Output: greeting message, phase='proposing'
```

### Invocation 2: Proposal
```
Input: initial_state + HR description
Nodes: greet_hr → propose_schema
Output: current_definition (JSONB), schema summary, phase='iterating'
```

### Invocation 3: Modification (Loop)
```
Input: state + HR request to add field
Nodes: propose_schema → classify_hr_intent → update_schema → propose_schema
Output: updated current_definition, phase='iterating'
(Note: Loop demonstrates full conditional routing)
```

### Invocation 4: Save
```
Input: state + HR says "save"
Nodes: propose_schema → classify_hr_intent → save_schema
Output: schema_id, DB INSERT, phase='done'
DB Effect: New Schema row with status='draft', version=1
```

### Invocation 5: Activate
```
Input: state + HR says "activate"
Nodes: propose_schema → classify_hr_intent → activate_schema
Output: success message, phase='done'
DB Effect: Archives old active schema, sets new to active
Partial unique index enforces exactly one active per company
```

## Database Interactions

### save_schema:
```python
# Find next version
SELECT MAX(version) FROM schemas WHERE company_id = ?
next_version = max_version + 1

# Insert new row
INSERT INTO schemas 
  (company_id, version, status, definition, created_by, ...)
VALUES
  (company_id, 1, 'draft', {...}, hr_user_id, ...)
```

### activate_schema:
```python
# Archive current active
UPDATE schemas SET status='archived' 
WHERE company_id=? AND status='active'

# Activate target
UPDATE schemas SET status='active', published_at=NOW()
WHERE id=?
# Partial unique index prevents duplicates
```

## Error Handling

Each node catches exceptions and returns error messages instead of raising:

```python
except json.JSONDecodeError as e:
    return {
        "messages": [AIMessage(content=f"Failed to parse schema: {e}")]
    }
except Exception as e:
    await session.rollback()
    return {
        "messages": [AIMessage(content=f"Database error: {e}")]
    }
```

## State Machine

```
START
  ↓
greet_hr (always runs)
  ↓
propose_schema
  ↓ [INTERRUPT for review]
classify_hr_intent
  ├─ modify/add/remove
  │  ↓
  │  update_schema
  │  ↓
  │  propose_schema (LOOP)
  │
  ├─ save
  │  ↓
  │  save_schema
  │  ↓ END
  │
  └─ activate
     ↓
     activate_schema
     ↓ END
```

HR can iterate multiple times (modifying fields) before saving.
Once saved, they can activate or create a new draft.

## Next: Phase 4

Once Phase 3 is verified:
1. Create FastAPI endpoints for HR schema chat
2. Implement SSE streaming for token-by-token response
3. Handle graph invocation from HTTP requests
4. Wire interrupt() between nodes for human approval
5. Create auth dependencies (HR user from bearer token)

See full plan: `/claude/plans/refactored-jingling-bubble.md` Phase 4 section.
