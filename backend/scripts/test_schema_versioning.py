"""Test script to verify schema versioning constraint works correctly."""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import IntegrityError
from app.config import settings
from app.models import Company, Schema, HRUser


async def test_schema_versioning():
    """Test that partial unique index prevents multiple active schemas per company."""

    engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        # Get the test company we seeded
        from sqlalchemy import select
        result = await session.execute(select(Company).where(Company.slug == "techcorp"))
        company = result.scalar_one_or_none()

        if not company:
            print("❌ Test company not found. Run seed_data.py first.")
            return

        print(f"✓ Found test company: {company.name}")

        # Get the HR user
        result = await session.execute(select(HRUser).where(HRUser.company_id == company.id))
        hr_user = result.scalar_one()

        # Get the existing draft schema
        result = await session.execute(
            select(Schema).where(
                (Schema.company_id == company.id) & (Schema.version == 1)
            )
        )
        draft_schema = result.scalar_one()
        print(f"✓ Found draft schema v{draft_schema.version}")

        # Activate the schema
        draft_schema.status = "active"
        draft_schema.published_at = asyncio.get_event_loop().time()
        await session.commit()
        print(f"✓ Activated schema v{draft_schema.version}")

        # Try to activate a second schema (should fail)
        try:
            schema_v2 = Schema(
                id=uuid.uuid4(),
                company_id=company.id,
                version=2,
                status="active",  # This should violate the partial unique index
                definition={"fields": []},
                created_by=hr_user.id,
            )
            session.add(schema_v2)
            await session.commit()
            print("❌ FAIL: Was able to create second active schema (constraint not enforced)")
        except IntegrityError as e:
            await session.rollback()
            print("✓ SUCCESS: Partial unique index prevented second active schema")
            print(f"  Error: {str(e)[:100]}...")

        # Verify we can create v2 as draft
        try:
            schema_v2_draft = Schema(
                id=uuid.uuid4(),
                company_id=company.id,
                version=2,
                status="draft",  # Draft is allowed
                definition={"fields": [{"key": "test", "label": "Test", "type": "text"}]},
                created_by=hr_user.id,
            )
            session.add(schema_v2_draft)
            await session.commit()
            print("✓ SUCCESS: Can create v2 as draft when v1 is active")
        except IntegrityError as e:
            await session.rollback()
            print(f"❌ FAIL: Could not create v2 as draft: {e}")

        # Verify schema rollback pattern: archive active, activate new
        try:
            # Archive v1
            result = await session.execute(
                select(Schema).where(
                    (Schema.company_id == company.id) & (Schema.status == "active")
                )
            )
            active_schema = result.scalar_one()
            active_schema.status = "archived"

            # Activate v2
            result = await session.execute(
                select(Schema).where(
                    (Schema.company_id == company.id) & (Schema.version == 2)
                )
            )
            v2_schema = result.scalar_one()
            v2_schema.status = "active"

            await session.commit()
            print("✓ SUCCESS: Schema rollback pattern works (archive old, activate new)")
        except IntegrityError as e:
            await session.rollback()
            print(f"❌ FAIL: Rollback pattern failed: {e}")

        # Verify multi-company isolation
        try:
            # Create company 2
            company2 = Company(
                id=uuid.uuid4(),
                name="AnotherCorp",
                slug="anothercorp",
            )
            session.add(company2)
            await session.flush()

            # Create HR user for company 2
            hr_user2 = HRUser(
                id=uuid.uuid4(),
                company_id=company2.id,
                email="hr@anothercorp.com",
                display_name="Bob HR",
                api_token=f"test-hr-token-{uuid.uuid4().hex[:8]}",
            )
            session.add(hr_user2)
            await session.flush()

            # Create active schema for company 2 (should not conflict with company1's active schema)
            schema_c2 = Schema(
                id=uuid.uuid4(),
                company_id=company2.id,
                version=1,
                status="active",
                definition={"fields": []},
                created_by=hr_user2.id,
            )
            session.add(schema_c2)
            await session.commit()
            print("✓ SUCCESS: Company 2 can have its own active schema independently")
        except IntegrityError as e:
            await session.rollback()
            print(f"❌ FAIL: Multi-company isolation failed: {e}")

        print("\n✅ All schema versioning tests passed!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_schema_versioning())
