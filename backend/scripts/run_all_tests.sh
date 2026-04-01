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

# Check LM Studio connection
echo ""
echo "Checking LM Studio connection..."
if ! curl -s http://localhost:1234/v1/models > /dev/null 2>&1; then
    echo "❌ LM Studio not running at http://localhost:1234"
    echo "   Start LM Studio before running tests"
    echo "   Or set LM_STUDIO_BASE_URL in .env if running elsewhere"
    exit 1
fi
echo "✓ LM Studio is running"

echo ""
echo "✓ Configuration loaded"
echo "  DATABASE_URL: $(grep DATABASE_URL .env | cut -d= -f2)"
echo "  LM_STUDIO_BASE_URL: $(grep LM_STUDIO_BASE_URL .env | cut -d= -f2)"
echo "  LM_STUDIO_MODEL: $(grep LM_STUDIO_MODEL .env | cut -d= -f2)"

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
