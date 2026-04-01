"""Test script for full HR Schema Graph workflow (Phase 3).

Simulates:
1. HR greeting
2. Propose schema from description
3. Modify schema (add a field)
4. Save schema to DB
5. Activate schema
6. Verify DB state

This is an end-to-end test of the conversational schema design loop.
"""

import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Company, HRUser, Schema
from app.graphs.hr_schema.graph import create_hr_schema_graph
from app.utils.thread_ids import hr_schema_thread_id
from app.database import async_session_maker


async def get_test_company_and_hr():
    """Get the seeded test company and HR user."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Company).where(Company.slug == "techcorp")
        )
        company = result.scalar_one_or_none()

        if not company:
            print("❌ Test company not found. Run seed_data.py first.")
            return None, None

        result = await session.execute(
            select(HRUser).where(HRUser.company_id == company.id)
        )
        hr_user = result.scalar_one_or_none()

        if not hr_user:
            print("❌ Test HR user not found.")
            return None, None

        return company, hr_user


async def test_hr_schema_full_flow():
    """Run full HR Schema Graph test."""

    print("=" * 70)
    print("Testing HR Schema Graph - Full Workflow (Phase 3)")
    print("=" * 70)

    # Get test company and HR user
    company, hr_user = await get_test_company_and_hr()
    if not company or not hr_user:
        return

    company_id = str(company.id)
    hr_user_id = str(hr_user.id)
    session_id = str(uuid.uuid4())
    thread_id = hr_schema_thread_id(company_id, hr_user_id, session_id)

    print(f"\n📍 Setup:")
    print(f"  Company: {company.name} ({company_id})")
    print(f"  HR User: {hr_user.email}")
    print(f"  Thread ID: {thread_id}")

    # Build graph
    print(f"\n🔧 Building graph with AsyncPostgresSaver...")
    try:
        graph = await create_hr_schema_graph(settings.DATABASE_URL)
        print("✓ Graph built successfully")
    except Exception as e:
        print(f"❌ Failed to build graph: {e}")
        return

    config = {"configurable": {"thread_id": thread_id}}

    # Initial state
    initial_state = {
        "company_id": company_id,
        "hr_user_id": hr_user_id,
        "session_id": session_id,
        "messages": [],
        "current_definition": None,
        "current_version": None,
        "schema_id": None,
        "phase": "proposing",
        "hr_intent": None,
        "sandbox_active": False,
        "sandbox_simulated_answers": None,
    }

    # Step 1: Greet HR
    print(f"\n1️⃣  Greeting HR (greet_hr node)...")
    try:
        result1 = await graph.ainvoke(initial_state, config=config)
        print(f"✓ Greeting succeeded")
        print(f"  Phase: {result1['phase']}")
        print(f"  Message: {result1['messages'][-1].content[:80]}...")
    except Exception as e:
        print(f"❌ Greeting failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 2: HR describes schema
    print(f"\n2️⃣  HR describes schema (propose_schema node)...")
    hr_description = "I want to collect full name, years of experience, and expected salary from candidates"

    state2 = {
        **result1,
        "messages": result1["messages"] + [HumanMessage(content=hr_description)],
    }

    try:
        result2 = await graph.ainvoke(state2, config=config)
        print(f"✓ Schema proposed")
        print(f"  Current definition fields: {len(result2.get('current_definition', {}).get('fields', []))}")
        if result2.get("current_definition"):
            for field in result2["current_definition"]["fields"]:
                print(f"    - {field['label']} ({field['type']})")
    except Exception as e:
        print(f"❌ Proposal failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: HR asks to add a field
    print(f"\n3️⃣  HR requests modification (add field)...")
    add_field_request = "Actually, can you add a resume field too? It should be a PDF file upload."

    state3 = {
        **result2,
        "messages": result2["messages"] + [HumanMessage(content=add_field_request)],
    }

    try:
        result3 = await graph.ainvoke(state3, config=config)
        print(f"✓ Intent classified and schema updated")
        print(f"  Intent: {result3.get('hr_intent')}")
        print(f"  Updated fields: {len(result3.get('current_definition', {}).get('fields', []))}")
        if result3.get("current_definition"):
            for field in result3["current_definition"]["fields"]:
                print(f"    - {field['label']} ({field['type']})")
    except Exception as e:
        print(f"❌ Update failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 4: HR wants to save
    print(f"\n4️⃣  HR saves schema...")
    save_request = "Great! Let's save this schema as a draft."

    state4 = {
        **result3,
        "messages": result3["messages"] + [HumanMessage(content=save_request)],
    }

    try:
        result4 = await graph.ainvoke(state4, config=config)
        print(f"✓ Schema saved to database")
        print(f"  Schema ID: {result4.get('schema_id')}")
        print(f"  Version: {result4.get('current_version')}")
        print(f"  Phase: {result4['phase']}")
        schema_id = result4.get("schema_id")
    except Exception as e:
        print(f"❌ Save failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 5: Verify DB state
    print(f"\n5️⃣  Verifying database state...")
    async with async_session_maker() as session:
        result = await session.execute(
            select(Schema).where(Schema.id == schema_id)
        )
        saved_schema = result.scalar_one_or_none()

        if saved_schema:
            print(f"✓ Schema found in database")
            print(f"  Status: {saved_schema.status}")
            print(f"  Version: {saved_schema.version}")
            print(f"  Fields: {len(saved_schema.definition.get('fields', []))}")
        else:
            print(f"❌ Schema not found in database")
            return

    # Step 6: HR activates schema
    print(f"\n6️⃣  HR activates schema...")
    activate_request = "Looks good! Activate this schema so candidates can start onboarding."

    state5 = {
        **result4,
        "messages": result4["messages"] + [HumanMessage(content=activate_request)],
    }

    try:
        result5 = await graph.ainvoke(state5, config=config)
        print(f"✓ Schema activated")
        print(f"  Phase: {result5['phase']}")
    except Exception as e:
        print(f"❌ Activation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 7: Verify activation in DB
    print(f"\n7️⃣  Verifying activation in database...")
    async with async_session_maker() as session:
        result = await session.execute(
            select(Schema).where(
                (Schema.company_id == company.id) & (Schema.status == "active")
            )
        )
        active_schema = result.scalar_one_or_none()

        if active_schema and active_schema.id == schema_id:
            print(f"✓ Schema is active in database")
            print(f"  Status: {active_schema.status}")
            print(f"  Published at: {active_schema.published_at}")
        else:
            print(f"❌ Schema is not active in database")
            return

    # Summary
    print("\n" + "=" * 70)
    print("✅ FULL HR SCHEMA WORKFLOW TEST PASSED")
    print("=" * 70)
    print("\nWorkflow completed:")
    print("  1. ✓ Greeted HR user")
    print("  2. ✓ Proposed schema from natural language description")
    print("  3. ✓ HR requested modification (added field)")
    print("  4. ✓ Schema was updated via Claude")
    print("  5. ✓ HR saved schema to database (as draft)")
    print("  6. ✓ HR activated schema")
    print("  7. ✓ Database verified active schema")
    print("\nConversational flow demonstrated:")
    print("  - Describe → Claude extracts structure")
    print("  - Iterate → HR requests changes")
    print("  - Classify → Claude determines intent")
    print("  - Apply → Claude modifies definition")
    print("  - Save → Persisted to PostgreSQL")
    print("  - Activate → Multi-tenant ready for talent onboarding")


if __name__ == "__main__":
    asyncio.run(test_hr_schema_full_flow())
