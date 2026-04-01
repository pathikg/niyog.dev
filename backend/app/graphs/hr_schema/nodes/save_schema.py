"""Save node: Persist schema to database as draft."""

from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import AIMessage

from app.models import Schema
from app.graphs.hr_schema.state import HRSchemaState


async def save_schema(state: HRSchemaState, session: AsyncSession) -> dict:
    """
    Save the current schema definition to database as draft.

    Queries for the next version number, inserts a new Schema row with status='draft',
    and stores the schema_id in state.

    Args:
        state: Current HRSchemaState with current_definition
        session: Database session (dependency injected)

    Returns:
        dict with schema_id set, phase updated to 'done', success message
    """

    if not state["current_definition"]:
        return {
            "messages": [AIMessage(content="No schema to save. Please design one first.")]
        }

    try:
        company_id = UUID(state["company_id"])
        hr_user_id = UUID(state["hr_user_id"])

        # Get the next version number
        result = await session.execute(
            select(Schema)
            .where(Schema.company_id == company_id)
            .order_by(Schema.version.desc())
            .limit(1)
        )
        last_schema = result.scalar_one_or_none()
        next_version = (last_schema.version + 1) if last_schema else 1

        # Create new schema row
        new_schema = Schema(
            company_id=company_id,
            version=next_version,
            status="draft",
            definition=state["current_definition"],
            created_by=hr_user_id,
            hr_thread_id=f"hr-{state['company_id']}-{state['hr_user_id']}-{state['session_id']}",
        )

        session.add(new_schema)
        await session.flush()  # Get the ID
        schema_id = str(new_schema.id)

        await session.commit()

        response_text = f"""✅ Schema saved as draft (v{next_version})!

Your schema has been saved. You can:
- Continue editing this draft
- Test it in sandbox mode
- Activate it when ready

Share the activation link with your team when you're ready to go live."""

        return {
            "schema_id": schema_id,
            "current_version": next_version,
            "phase": "done",
            "messages": [AIMessage(content=response_text)],
        }

    except Exception as e:
        await session.rollback()
        error_msg = f"Error saving schema: {str(e)[:100]}"
        return {
            "messages": [AIMessage(content=f"Failed to save schema. {error_msg}")]
        }
