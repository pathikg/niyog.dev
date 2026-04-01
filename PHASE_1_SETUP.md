# Phase 1: Database Setup & Verification

This guide walks through setting up the PostgreSQL database, running migrations, seeding test data, and verifying the schema versioning constraint.

## Prerequisites

- PostgreSQL 14+ (local or Supabase)
- Python 3.11+
- Anthropic API key (not needed for Phase 1, but add to .env anyway)

## Setup Steps

### 1. Environment Setup

```bash
cd backend
cp .env.example .env
```

Edit `.env` and set:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/niyog_db
ANTHROPIC_API_KEY=sk-ant-...
```

For local PostgreSQL:
```bash
# Create database
createdb niyog_db

# Get connection string
DATABASE_URL=postgresql+asyncpg://$(whoami):@localhost:5432/niyog_db
```

For Supabase:
- Create project at https://supabase.com
- Get direct connection string (not pooler): `postgresql+asyncpg://postgres:password@...`
- Use that in DATABASE_URL

### 2. Install Dependencies

```bash
cd backend
pip install -e .
```

This installs all dependencies including:
- FastAPI, SQLAlchemy, Alembic
- LangChain, LangGraph (for later phases)
- AsyncPG for PostgreSQL async driver

### 3. Run Migrations

```bash
# From backend/
alembic upgrade head
```

This creates all tables:
- `companies`
- `hr_users`
- `talent_users`
- `schemas` (with partial unique index)
- `onboarding_sessions`
- `talent_profiles`
- `files`

**Key migration features:**
- All UUIDs are proper PostgreSQL UUID type
- Foreign keys with CASCADE delete
- JSONB columns for `schemas.definition` and `talent_profiles.data`
- GIN indexes on JSONB for efficient querying
- **Partial unique index** `idx_schemas_single_active` on schemas table enforces exactly one active schema per company
- Check constraints on status enums

### 4. Seed Test Data

```bash
python scripts/seed_data.py
```

This creates:
- **Company**: TechCorp (slug: `techcorp`)
- **HR User**: `hr@techcorp.com` (token: `test-hr-token-123`)
- **Talent User 1**: `alice.candidate@example.com` (token: `test-talent-token-1`)
- **Talent User 2**: `bob.candidate@example.com` (token: `test-talent-token-2`)
- **Draft Schema v1**: 4 fields (full_name, years_experience, expected_ctc, resume)

### 5. Verify Schema Versioning Constraint

```bash
python scripts/test_schema_versioning.py
```

This tests:
1. ✅ Activate draft schema v1
2. ✅ Attempt to activate second schema → should FAIL (partial unique index enforced)
3. ✅ Create v2 as draft while v1 is active → should SUCCEED
4. ✅ Rollback pattern (archive v1, activate v2) → should SUCCEED
5. ✅ Multi-company isolation (Company 2 can have its own active schema) → should SUCCEED

Expected output:
```
✓ Found test company: TechCorp
✓ Found draft schema v1
✓ Activated schema v1
✓ SUCCESS: Partial unique index prevented second active schema
✓ SUCCESS: Can create v2 as draft when v1 is active
✓ SUCCESS: Schema rollback pattern works (archive old, activate new)
✓ SUCCESS: Company 2 can have its own active schema independently

✅ All schema versioning tests passed!
```

## Database Structure

### companies
```sql
id UUID PK
name TEXT
slug TEXT UNIQUE
created_at, updated_at TIMESTAMP
```

### hr_users
```sql
id UUID PK
company_id UUID FK → companies
email TEXT UNIQUE
display_name TEXT
api_token TEXT UNIQUE
created_at TIMESTAMP
```

### talent_users
```sql
id UUID PK
company_id UUID FK → companies
email TEXT
display_name TEXT
api_token TEXT UNIQUE
created_at TIMESTAMP
UNIQUE(company_id, email)  -- per-company email uniqueness
```

### schemas (CORE: Schema Versioning)
```sql
id UUID PK
company_id UUID FK → companies
version INT (1, 2, 3, ...)
status TEXT: 'draft' | 'active' | 'archived'
definition JSONB              -- Field definitions
created_by UUID FK → hr_users
hr_thread_id TEXT            -- LangGraph thread_id that created it
created_at, published_at TIMESTAMP

UNIQUE(company_id, version)
UNIQUE INDEX idx_schemas_single_active
  ON schemas(company_id)
  WHERE status = 'active'    -- Enforces exactly 1 active per company
```

**Schema Definition Example:**
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

### onboarding_sessions
```sql
id UUID PK
company_id UUID FK → companies
talent_id UUID FK → talent_users
schema_id UUID FK → schemas (immutable: pinned to schema version)
thread_id TEXT UNIQUE        -- LangGraph thread_id for this conversation
status TEXT: 'in_progress' | 'completed' | 'abandoned'
created_at, completed_at TIMESTAMP
```

### talent_profiles
```sql
id UUID PK
company_id UUID FK → companies
talent_id UUID FK → talent_users
schema_id UUID FK → schemas  -- FK to immutable schema version
onboarding_session_id UUID FK → onboarding_sessions
data JSONB                   -- Collected field values
is_final BOOLEAN             -- true when submission complete
created_at, updated_at TIMESTAMP

-- Example data:
{
  "full_name": "Alice Johnson",
  "years_experience": 5,
  "expected_ctc": 120000,
  "resume": "file::<uuid>"   -- Reference to files table
}
```

### files
```sql
id UUID PK
company_id UUID FK → companies
uploaded_by UUID
uploader_type TEXT: 'talent' | 'hr'
storage_bucket TEXT          -- 'onboarding-files'
storage_key TEXT             -- Full S3/Supabase path
original_name, mime_type TEXT
size_bytes BIGINT
profile_id UUID FK → talent_profiles (nullable)
field_key TEXT              -- e.g. 'resume'
created_at TIMESTAMP
```

## SQL Queries for Manual Verification

List all schemas for a company:
```sql
SELECT version, status, created_at, published_at
FROM schemas
WHERE company_id = '<company_uuid>'
ORDER BY version DESC;
```

Get active schema for a company:
```sql
SELECT * FROM schemas
WHERE company_id = '<company_uuid>' AND status = 'active';
```

List talent profiles with their schema fields:
```sql
SELECT
  tp.id, tp.talent_id, tp.data,
  s.version, s.definition
FROM talent_profiles tp
JOIN schemas s ON tp.schema_id = s.id
WHERE tp.company_id = '<company_uuid>'
ORDER BY tp.created_at DESC;
```

Test the partial unique index (should fail):
```sql
INSERT INTO schemas (id, company_id, version, status, definition, created_by)
VALUES (uuid_generate_v4(), '<company_uuid>', 99, 'active', '{}', '<hr_user_uuid>');

-- Should error: duplicate key value violates unique constraint "idx_schemas_single_active"
```

## Next: Phase 2

Once Phase 1 is verified:
1. Set up LangGraph `AsyncPostgresSaver` checkpointer (uses same DATABASE_URL)
2. Build minimal HR schema graph (greet_hr → interrupt → END)
3. Test graph persistence with thread_id resumption

See `/claude/plans/refactored-jingling-bubble.md` Phase 2 section.
