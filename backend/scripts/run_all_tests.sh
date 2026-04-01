#!/bin/bash
# Run all Phase 1-3 tests in sequence

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           Testing Niyog: Phases 1, 2, and 3                      ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "❌ .env file not found!"
    echo "   Please create .env from .env.example:"
    echo "   cp .env.example .env"
    echo "   Then edit .env with your DATABASE_URL and ANTHROPIC_API_KEY"
    exit 1
fi

# Check ANTHROPIC_API_KEY
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "⚠️  ANTHROPIC_API_KEY not set in environment"
    echo "   Attempting to load from .env..."
    export $(grep ANTHROPIC_API_KEY .env | xargs)
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY not found in .env or environment!"
    exit 1
fi

echo ""
echo "✓ Configuration loaded"
echo "  DATABASE_URL: $(grep DATABASE_URL .env | cut -d= -f2)"
echo "  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:0:10}...***"

# Phase 1: Database
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "PHASE 1: Database Schema & Seed Data"
echo "═══════════════════════════════════════════════════════════════════"

echo ""
echo "Running migrations..."
alembic upgrade head

echo ""
echo "Seeding test data..."
python scripts/seed_data.py

# Phase 1: Schema Versioning Test
echo ""
echo "Testing schema versioning constraints..."
python scripts/test_schema_versioning.py

# Phase 2: Graph Persistence
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "PHASE 2: LangGraph Persistence"
echo "═══════════════════════════════════════════════════════════════════"

echo ""
python scripts/test_graph_persistence.py

# Phase 3: Full Workflow
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "PHASE 3: HR Schema Graph Full Workflow"
echo "═══════════════════════════════════════════════════════════════════"

echo ""
python scripts/test_hr_schema_graph.py

# Summary
echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                   ✅ ALL TESTS PASSED                            ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Summary:"
echo "  ✓ Phase 1: Database schema, seed data, versioning constraints"
echo "  ✓ Phase 2: LangGraph persistence, checkpointer, state resumption"
echo "  ✓ Phase 3: Full HR schema workflow, Claude integration"
echo ""
echo "Next: Phase 4 - FastAPI endpoints and SSE streaming"
echo "See: /claude/plans/refactored-jingling-bubble.md (Phase 4)"
echo ""
