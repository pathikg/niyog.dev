"""Seed script to populate initial test data."""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
from app.models import (
    Base, Company, HRUser, TalentUser, Schema
)


async def seed_database():
    """Populate database with test data."""

    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        # Create company
        company = Company(
            id=uuid.uuid4(),
            name="TechCorp",
            slug="techcorp",
        )
        session.add(company)
        await session.flush()  # Get company ID

        # Create HR user
        hr_user = HRUser(
            id=uuid.uuid4(),
            company_id=company.id,
            email="hr@techcorp.com",
            display_name="Alice Johnson",
            api_token="test-hr-token-123",
        )
        session.add(hr_user)
        await session.flush()

        # Create talent users
        talent_user_1 = TalentUser(
            id=uuid.uuid4(),
            company_id=company.id,
            email="alice.candidate@example.com",
            display_name="Alice Candidate",
            api_token="test-talent-token-1",
        )
        talent_user_2 = TalentUser(
            id=uuid.uuid4(),
            company_id=company.id,
            email="bob.candidate@example.com",
            display_name="Bob Candidate",
            api_token="test-talent-token-2",
        )
        session.add(talent_user_1)
        session.add(talent_user_2)
        await session.flush()

        # Create draft schema
        draft_schema = Schema(
            id=uuid.uuid4(),
            company_id=company.id,
            version=1,
            status="draft",
            definition={
                "fields": [
                    {
                        "key": "full_name",
                        "label": "Full Name",
                        "type": "text",
                        "required": True,
                        "question_hint": "What is your full legal name?",
                    },
                    {
                        "key": "years_experience",
                        "label": "Years of Experience",
                        "type": "number",
                        "required": True,
                        "question_hint": "How many years of experience do you have?",
                    },
                    {
                        "key": "expected_ctc",
                        "label": "Expected CTC",
                        "type": "number",
                        "required": True,
                        "question_hint": "What is your expected annual salary in INR?",
                    },
                    {
                        "key": "resume",
                        "label": "Resume",
                        "type": "file",
                        "required": True,
                        "accepted_mime_types": ["application/pdf"],
                    },
                ],
                "greeting_message": "Hi! Welcome to TechCorp. I'll guide you through onboarding.",
                "completion_message": "Great! Your profile is complete.",
            },
            created_by=hr_user.id,
            hr_thread_id=f"hr-{company.id}-{hr_user.id}-test-session",
        )
        session.add(draft_schema)

        await session.commit()

        print("✓ Seeded database successfully!")
        print(f"  Company: {company.name} (id={company.id})")
        print(f"  HR User: {hr_user.email} (token={hr_user.api_token})")
        print(f"  Talent User 1: {talent_user_1.email} (token={talent_user_1.api_token})")
        print(f"  Talent User 2: {talent_user_2.email} (token={talent_user_2.api_token})")
        print(f"  Draft Schema: v{draft_schema.version} with {len(draft_schema.definition['fields'])} fields")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
