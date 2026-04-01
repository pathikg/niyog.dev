"""Activate node: Set schema to active (archive old active schema)."""

from datetime import datetime
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import AIMessage

from app.models import Schema
from app.graphs.hr_schema.state import HRSchemaState


async def activate_schema(state: HRSchemaState, session: AsyncSession) -> dict:
    """
    Activate the current schema and archive any previously active schema.

    Uses the partial unique index to enforce exactly one active schema per company.

    Args:
        state: Current HRSchemaState with schema_id
        session: Database session (dependency injected)

    Returns:
        dict with success message and phase='done'
    """

    if not state["schema_id"]:
        return {
            "messages": [AIMessage(content="No schema to activate. Please save one first.")]
        }

    try:
        company_id = UUID(state["company_id"])
        schema_id = UUID(state["schema_id"])

        # Archive currently active schema (if any)
        result = await session.execute(
            select(Schema).where(
                and_(
                    Schema.company_id == company_id,
                    Schema.status == "active"
                )
            )
        )
        active_schema = result.scalar_one_or_none()

        if active_schema:
            active_schema.status = "archived"
            await session.flush()

        # Activate the target schema
        result = await session.execute(
            select(Schema).where(Schema.id == schema_id)
        )
        target_schema = result.scalar_one()

        target_schema.status = "active"
        target_schema.published_at = datetime.utcnow()
        await session.flush()

        await session.commit()

        response_text = f"""🎉 Schema v{target_schema.version} is now active!

Your talent intake form is live. Candidates will see this schema when they start onboarding.

You can:
- View submitted profiles in your dashboard
- Make a new draft schema (doesn't affect current submissions)
- Archive or rollback if needed"""

        return {
            "phase": "done",
            "messages": [AIMessage(content=response_text)],
        }

    except Exception as e:
        await session.rollback()
        error_msg = f"Error activating schema: {str(e)[:100]}"
        return {
            "messages": [AIMessage(content=f"Failed to activate schema. {error_msg}")]
        }
