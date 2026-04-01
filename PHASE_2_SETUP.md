# Phase 2: LangGraph Checkpointer + Minimal HR Graph

This phase sets up LangGraph persistence and builds a minimal HR Schema Graph for testing graph resumption.

## What We're Building

**Minimal Graph (Phase 2):**
```
START → greet_hr → END
         ↓
      (with AsyncPostgresSaver checkpointer)
```

**Full Graph (for reference, Phase 3+):**
```
START → greet_hr → propose_schema → [INTERRUPT] → classify_hr_input →
    ├── modify/add/remove → update_schema → [INTERRUPT] (loop)
    ├── test             → enter_sandbox  → [INTERRUPT] (loop)
    ├── save             → save_schema    → END
    └── activate         → activate_schema → END
```

## Architecture Overview

### LangGraph Components

1. **Checkpointer** (`app/graphs/checkpointer.py`)
   - Uses `AsyncPostgresSaver` from langgraph
   - Persists graph state to PostgreSQL (separate tables from our app schema)
   - Enables resumption with `thread_id`

2. **State Schema** (`app/graphs/hr_schema/state.py`)
   - `HRSchemaState` TypedDict with all fields
   - `messages` uses `add_messages` reducer (appends, never overwrites)
   - All required fields initialized on invocation

3. **Nodes** (`app/graphs/hr_schema/nodes/`)
   - `greet_hr`: Queries DB for existing draft schema, produces greeting or loads draft
   - Other nodes (Phase 3+): propose_schema, classify_hr_input, update_schema, etc.

4. **Graph Builder** (`app/graphs/hr_schema/graph.py`)
   - `build_hr_schema_graph()`: Wires nodes and edges
   - `create_hr_schema_graph()`: Convenience for scripts (creates checkpointer + builds graph)

5. **Thread IDs** (`app/utils/thread_ids.py`)
   - `hr_schema_thread_id()`: Construct thread_id for HR session
   - `talent_onboarding_thread_id()`: Construct thread_id for talent session
   - Format allows isolation per session and user

## Files Created

```
backend/
├── app/
│   ├── graphs/
│   │   ├── checkpointer.py                    # AsyncPostgresSaver factory
│   │   └── hr_schema/
│   │       ├── __init__.py
│   │       ├── state.py                       # HRSchemaState TypedDict
│   │       ├── prompts.py                     # Prompt templates (for Claude calls)
│   │       ├── graph.py                       # build_hr_schema_graph()
│   │       └── nodes/
│   │           ├── __init__.py
│   │           └── greet_hr.py                # First node
│   └── utils/
│       └── thread_ids.py                      # Thread ID constructors
└── scripts/
    └── test_graph_persistence.py              # Persistence test
```

## How It Works

### Checkpointer Setup

```python
from langgraph.checkpoint.postgres import aio as pg_checkpointer

# Create checkpointer (uses DATABASE_URL)
checkpointer = pg_checkpointer.AsyncPostgresSaver(
    conn_string=settings.DATABASE_URL,
)

# Initialize (creates checkpointer tables if needed)
await checkpointer.setup()

# Pass to graph.compile()
graph = builder.compile(checkpointer=checkpointer)
```

**Checkpointer creates its own tables:**
- `checkpoint_writes` — stores state snapshots at each step
- `checkpoint_blobs` — stores large values (messages, etc.)
- `checkpoint_tokens` — manages garbage collection

### Thread ID Isolation

```python
# HR session
thread_id = f"hr-{company_id}-{hr_user_id}-{session_id}"
# Example: "hr-12345-67890-abc123"

# Talent session
thread_id = f"talent-{company_id}-{talent_id}-{onboarding_session_id}"
# Example: "talent-12345-98765-session-id"
```

Each unique thread_id maintains independent checkpoint history.

### State Persistence Flow

```
1. Initial invocation:
   await graph.ainvoke(initial_state, config={"configurable": {"thread_id": "..."}})
   → greet_hr node executes
   → state checkpoint saved

2. Second invocation (same thread_id):
   await graph.ainvoke(new_state, config={"configurable": {"thread_id": "..."}})
   → LangGraph loads prior checkpoint
   → merges prior state with new state
   → continues execution
   → new checkpoint saved

3. Prior messages are preserved (add_messages reducer appends)
```

## Testing Graph Persistence

The test script verifies the full lifecycle:

```bash
cd backend
python scripts/test_graph_persistence.py
```

**What it tests:**
1. ✅ Checkpointer initializes with AsyncPostgresSaver
2. ✅ First invocation executes greet_hr node
3. ✅ Message is appended to state
4. ✅ Second invocation with same thread_id loads prior state
5. ✅ Prior greeting message is preserved
6. ✅ New messages are appended (not overwritten)
7. ✅ Checkpoint history is accessible

**Expected output:**
```
============================================================
Testing HR Schema Graph Persistence
============================================================

📍 Thread ID: hr-techcorp-test-hr-test-<uuid>

🔧 Building graph with AsyncPostgresSaver...
✓ Graph built successfully with checkpointer

1️⃣  First invocation (greet_hr node)...
   Config: {'configurable': {'thread_id': '...'}}
✓ First invocation succeeded
  Messages count: 1
  Phase: proposing
  Last message: Hi! I'm here to help you design your talent intake form...

2️⃣  Second invocation (resume with same thread_id)...
   Thread ID should load prior state from checkpointer
✓ Second invocation succeeded
  Messages count: 2
✓ Prior greeting message is preserved
  First message (greeting): Hi! I'm here to help you design your talent intake form...
  Latest message: ...

3️⃣  Checkpoint history...
✓ Retrieved 2 checkpoint(s)
  Checkpoint 1: 1 messages
  Checkpoint 2: 2 messages

============================================================
✅ GRAPH PERSISTENCE TEST PASSED
============================================================
```

## How to Run

### 1. Ensure Phase 1 is Complete

```bash
cd backend
alembic upgrade head
python scripts/seed_data.py
```

### 2. Install Dependencies (if not done)

```bash
pip install -e .
```

### 3. Run Persistence Test

```bash
python scripts/test_graph_persistence.py
```

## Key Design Decisions

### Message Reducer Pattern

```python
messages: Annotated[list[BaseMessage], add_messages]
```

The `add_messages` reducer ensures:
- Conversation history is preserved across interrupts and resumptions
- New messages are appended, not replacing prior ones
- Human and AI messages are properly merged
- Deduplication of identical consecutive messages

### Database Isolation

- App schema: companies, users, schemas, profiles, files (Phase 1)
- Checkpointer tables: checkpoint_writes, checkpoint_blobs, checkpoint_tokens (Phase 2)
- Both use same PostgreSQL, but separate tables
- Checkpointer tables are managed by LangGraph — we never query them directly

### Dependency Injection

In the full app (Phase 4), the FastAPI endpoint will:
1. Extract hr_user_id from auth token
2. Create or resume session_id
3. Construct thread_id
4. Create initial state
5. Invoke graph with config containing thread_id
6. Stream results back as SSE events

For Phase 2 testing, we use a simple script that:
1. Uses hardcoded test IDs
2. Calls graph.ainvoke() directly
3. Prints results

## State Field Reference

### HRSchemaState

```python
class HRSchemaState(TypedDict):
    # Identity
    company_id: str
    hr_user_id: str
    session_id: str

    # Conversation (add_messages reducer)
    messages: Annotated[list[BaseMessage], add_messages]

    # Schema Under Construction
    current_definition: Optional[dict]  # Working JSONB
    current_version: Optional[int]
    schema_id: Optional[str]  # DB row id

    # Control Flow
    phase: str  # "proposing" | "iterating" | "sandbox" | "saving" | "done"
    hr_intent: Optional[str]  # Parsed action

    # Sandbox
    sandbox_active: bool
    sandbox_simulated_answers: Optional[dict]
```

All fields must be initialized before `graph.ainvoke()`.

## Next: Phase 3

Once Phase 2 is verified:
1. Add `propose_schema` node (Claude extracts JSONB from HR description)
2. Add `classify_hr_intent` node (classify HR's next action)
3. Wire conditional edges for intent routing
4. Add `update_schema` node (Claude modifies definition)
5. Add `save_schema` and `activate_schema` nodes (DB writes)
6. Implement interrupt() after propose_schema and update_schema

See the full plan: `/claude/plans/refactored-jingling-bubble.md` Phase 3 section.
