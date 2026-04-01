# Testing All Phases (1-3) Locally

Complete guide to set up Niyog locally and run all tests end-to-end.

## Prerequisites

- PostgreSQL 14+ (local or Supabase)
- Python 3.11+
- Anthropic API key (for Claude calls)
- ~15 minutes

## Step 1: PostgreSQL Setup

### Option A: Local PostgreSQL

```bash
# Check if PostgreSQL is installed
psql --version

# Start PostgreSQL (macOS with Homebrew)
brew services start postgresql

# Or on Linux
sudo systemctl start postgresql

# Create database
createdb niyog_db

# Get connection string
# Format: postgresql+asyncpg://username:password@localhost:5432/niyog_db
# Default (no password): postgresql+asyncpg://$(whoami):@localhost:5432/niyog_db
```

### Option B: Supabase (Cloud)

1. Create project at https://supabase.com
2. Go to Settings → Database
3. Copy "Connection string" (not pooler)
4. Replace `[YOUR-PASSWORD]` with your password

Example:
```
postgresql+asyncpg://postgres:YOUR-PASSWORD@db.PROJ-ID.supabase.co:5432/postgres
```

## Step 2: Environment Setup

```bash
cd ~/Documents/niyog.dev/backend

# Copy template
cp .env.example .env

# Edit .env with your actual values
```

Edit `.env`:
```
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/niyog_db
ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE
```

Get your Anthropic API key from https://console.anthropic.com/

## Step 3: Install Dependencies

```bash
cd ~/Documents/niyog.dev/backend

# Install package
pip install -e .

# This installs:
# - FastAPI, SQLAlchemy, Alembic
# - LangChain, LangGraph, langgraph-checkpoint-postgres
# - Anthropic SDK
# - All database drivers
```

Verify installation:
```bash
python -c "import langgraph; import langchain_anthropic; print('✓ Deps OK')"
```

## Step 4: Run Database Migrations (Phase 1)

```bash
cd backend

# Run migrations
alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema creation
```

**What this creates:**
- companies, hr_users, talent_users tables
- schemas table (with partial unique index)
- onboarding_sessions, talent_profiles, files tables
- LangGraph checkpointer tables (checkpoint_writes, checkpoint_blobs, etc.)

Verify:
```bash
# List tables in psql
psql niyog_db -c "\dt"

# Should show ~10 tables
```

## Step 5: Seed Test Data (Phase 1)

```bash
python scripts/seed_data.py

# Expected output:
# ✓ Seeded database successfully!
#   Company: TechCorp (id=...)
#   HR User: hr@techcorp.com (token=test-hr-token-123)
#   Talent User 1: alice.candidate@example.com (token=test-talent-token-1)
#   Talent User 2: bob.candidate@example.com (token=test-talent-token-2)
#   Draft Schema: v1 with 4 fields
```

## Step 6: Verify Schema Versioning Constraint (Phase 1)

```bash
python scripts/test_schema_versioning.py

# Expected output:
# ============================================================
# ✓ Found test company: TechCorp
# ✓ Found draft schema v1
# ✓ Activated schema v1
# ✓ SUCCESS: Partial unique index prevented second active schema
# ✓ SUCCESS: Can create v2 as draft when v1 is active
# ✓ SUCCESS: Schema rollback pattern works (archive old, activate new)
# ✓ SUCCESS: Company 2 can have its own active schema independently
#
# ✅ All schema versioning tests passed!
```

**What it tests:**
- Partial unique index enforces 1 active schema per company
- Multi-schema drafts allowed
- Schema rollback pattern works
- Multi-tenant isolation

## Step 7: Test Graph Persistence (Phase 2)

```bash
python scripts/test_graph_persistence.py

# Expected output:
# ============================================================
# Testing HR Schema Graph Persistence
# ============================================================
#
# 📍 Thread ID: hr-techcorp-test-hr-test-...
#
# 🔧 Building graph with AsyncPostgresSaver...
# ✓ Graph built successfully with checkpointer
#
# 1️⃣  First invocation (greet_hr node)...
# ✓ First invocation succeeded
#   Messages count: 1
#   Phase: proposing
#   Last message: Hi! I'm here to help you design your talent intake form...
#
# 2️⃣  Second invocation (resume with same thread_id)...
# ✓ Second invocation succeeded
#   Messages count: 2
# ✓ Prior greeting message is preserved
#
# 3️⃣  Checkpoint history...
# ✓ Retrieved 2 checkpoint(s)
#   Checkpoint 1: 1 messages
#   Checkpoint 2: 2 messages
#
# ============================================================
# ✅ GRAPH PERSISTENCE TEST PASSED
# ============================================================
```

**What it tests:**
- AsyncPostgresSaver initializes correctly
- Graph persists state to PostgreSQL
- Same thread_id resumes prior state
- Message history is preserved (add_messages reducer)
- Checkpoint access works

## Step 8: Test Full HR Schema Workflow (Phase 3)

```bash
python scripts/test_hr_schema_graph.py

# Expected output (sample):
# ======================================================================
# Testing HR Schema Graph - Full Workflow (Phase 3)
# ======================================================================
#
# 📍 Setup:
#   Company: TechCorp (...)
#   HR User: hr@techcorp.com
#   Thread ID: hr-techcorp-...
#
# 🔧 Building graph with AsyncPostgresSaver...
# ✓ Graph built successfully
#
# 1️⃣  Greeting HR (greet_hr node)...
# ✓ Greeting succeeded
#   Phase: proposing
#   Message: Hi! I'm here to help you design your talent intake form...
#
# 2️⃣  HR describes schema (propose_schema node)...
# ✓ Schema proposed
#   Current definition fields: 3
#     - Full Name (text)
#     - Years of Experience (number)
#     - Expected Salary (number)
#
# 3️⃣  HR requests modification (add field)...
# ✓ Intent classified and schema updated
#   Intent: add_field
#   Updated fields: 4
#     - Full Name (text)
#     - Years of Experience (number)
#     - Expected Salary (number)
#     - Resume (file)
#
# 4️⃣  HR saves schema...
# ✓ Schema saved to database
#   Schema ID: ...
#   Version: 1
#   Phase: done
#
# 5️⃣  Verifying database state...
# ✓ Schema found in database
#   Status: draft
#   Version: 1
#   Fields: 4
#
# 6️⃣  HR activates schema...
# ✓ Schema activated
#   Phase: done
#
# 7️⃣  Verifying activation in database...
# ✓ Schema is active in database
#   Status: active
#   Published at: 2026-04-01 ...
#
# ======================================================================
# ✅ FULL HR SCHEMA WORKFLOW TEST PASSED
# ======================================================================
```

**What it tests:**
- Full conversational HR workflow
- Claude integration (schema extraction, intent classification, modification)
- Database persistence at each step
- Schema versioning and activation
- Multi-tenant isolation

## Summary: All Tests Pass

If you see all green checkmarks across all three tests, you have:

✅ **Phase 1 (Database):**
- PostgreSQL schema created correctly
- All 7 tables with proper constraints
- Partial unique index enforces 1 active schema per company
- Seed data loaded

✅ **Phase 2 (LangGraph Persistence):**
- AsyncPostgresSaver checkpointer working
- State persists across invocations
- Thread ID isolation functional
- Checkpoint history accessible

✅ **Phase 3 (HR Schema Graph):**
- Full conversational workflow operational
- Claude integration working (requires valid ANTHROPIC_API_KEY)
- All 6 nodes executing correctly
- Database persistence at each step
- Intent-based routing functional
- Schema activation enforces constraints

## Troubleshooting

### "Connection refused" error

PostgreSQL not running. Start it:
```bash
# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql

# Or connect to Supabase cloud instance instead
```

### "ANTHROPIC_API_KEY not set" or authentication error

```bash
# Check if key is set
echo $ANTHROPIC_API_KEY

# If empty, set it
export ANTHROPIC_API_KEY=sk-ant-YOUR-KEY

# Or add to .env file
echo "ANTHROPIC_API_KEY=sk-ant-YOUR-KEY" >> .env
```

Get key from: https://console.anthropic.com/

### "Partial unique index prevents second active schema" error in Phase 3

This is actually expected behavior if a schema is already active. The test is designed to handle it. If you're seeing a failure, check:

```bash
# View active schemas
psql niyog_db -c "SELECT version, status FROM schemas WHERE status='active';"
```

If there's a stray active schema, archive it:
```sql
UPDATE schemas SET status='archived' WHERE status='active';
```

Then re-run the test.

### "Table 'schemas' does not exist"

Migrations didn't run. Do this:
```bash
cd backend
alembic upgrade head
python scripts/seed_data.py
```

### Claude calls failing ("No API key")

Make sure ANTHROPIC_API_KEY is in your environment:
```bash
# Verify it's set
printenv | grep ANTHROPIC_API_KEY

# If not, set it
export ANTHROPIC_API_KEY=sk-ant-YOUR-KEY

# Then re-run test
python scripts/test_hr_schema_graph.py
```

## What Happens Under the Hood

### Phase 1: Database Setup
```
.env (DATABASE_URL)
  ↓
alembic upgrade head (creates schema)
  ↓
seed_data.py (populates test company, HR user, schema)
  ↓
test_schema_versioning.py (verifies constraints)
```

### Phase 2: Graph Persistence
```
create_hr_schema_graph(DATABASE_URL)
  ↓
AsyncPostgresSaver connects to PostgreSQL
  ↓
graph.ainvoke() with thread_id
  ↓
State checkpoint saved to PostgreSQL
  ↓
Second invocation with same thread_id
  ↓
State loaded from checkpoint (message history preserved)
```

### Phase 3: Full Workflow
```
greet_hr (greeting)
  ↓
HR message: "I want name, salary, resume"
  ↓
propose_schema (Claude extracts JSONB)
  ↓
HR message: "add a resume field"
  ↓
classify_hr_intent (Claude classifies: "add_field")
  ↓
update_schema (Claude modifies JSONB)
  ↓
HR message: "save it"
  ↓
classify_hr_intent (Claude classifies: "save")
  ↓
save_schema (INSERT to schemas table)
  ↓
HR message: "activate it"
  ↓
classify_hr_intent (Claude classifies: "activate")
  ↓
activate_schema (UPDATE status='active', archive old)
  ↓
Verification: SELECT status FROM schemas WHERE company_id=?
```

## Performance Notes

- **Phase 1 tests:** <1 second
- **Phase 2 test:** ~2-3 seconds (checkpointer setup)
- **Phase 3 test:** ~10-15 seconds (Claude API calls)

Total runtime: ~20 seconds

## File Changes During Tests

### Phase 1:
- Creates PostgreSQL database schema
- Inserts 1 company, 1 HR user, 2 talent users, 1 draft schema

### Phase 2:
- Creates checkpointer tables in PostgreSQL
- Creates checkpoint entries for each invocation

### Phase 3:
- Creates new Schema row (v1, status='draft')
- Creates another Schema row (v2, status='active')
- Updates first schema to 'archived'

All changes are persisted to PostgreSQL.

## Next Steps (After All Tests Pass)

✅ Phases 1-3 complete and tested
→ Ready for Phase 4: FastAPI endpoints + SSE streaming

In Phase 4, you'll:
1. Create `/api/hr/schema/session` endpoint
2. Create `/api/hr/schema/chat` endpoint (SSE)
3. Add auth dependencies
4. Stream Claude responses in real-time
5. Handle interrupts (HR reviews schema before proceeding)

See: `/claude/plans/refactored-jingling-bubble.md` Phase 4 section
