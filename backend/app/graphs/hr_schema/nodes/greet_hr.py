"""Greet node: Check for existing draft schema or produce initial greeting."""

from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Schema
from app.graphs.hr_schema.state import HRSchemaState
from app.graphs.hr_schema.prompts import GREET_HR_SYSTEM, GREET_HR_WITH_EXISTING_DRAFT


async def greet_hr(state: HRSchemaState, session: AsyncSession) -> dict:
    """
    Greet HR user. Check for existing draft schema and load if found.

    If a draft exists, load its definition and version into state and ask if they want to continue.
    If no draft, produce a warm greeting and ask what fields they want to collect.

    Args:
        state: Current HRSchemaState
        session: Database session (dependency injected)

    Returns:
        dict with updated messages, current_definition, current_version, schema_id, phase
    """
    company_id = state["company_id"]

    # Query for existing draft schema
    result = await session.execute(
        select(Schema)
        .where(
            (Schema.company_id == company_id) &
            (Schema.status == "draft")
        )
        .order_by(Schema.version.desc())
        .limit(1)
    )
    existing_draft = result.scalar_one_or_none()

    updates = {
        "phase": "proposing",
    }

    if existing_draft:
        # Load existing draft
        updates["current_definition"] = existing_draft.definition
        updates["current_version"] = existing_draft.version
        updates["schema_id"] = str(existing_draft.id)

        # Format schema summary for the prompt
        fields_summary = "\n".join([
            f"- {field['label']} ({field['type']}, {'required' if field.get('required') else 'optional'})"
            for field in existing_draft.definition.get("fields", [])
        ])

        greeting = f"""Great! I found your existing draft schema (v{existing_draft.version}) with these fields:

{fields_summary}

Would you like to continue iterating on this schema, or would you prefer to start fresh?"""

        updates["messages"] = [AIMessage(content=greeting)]
    else:
        # No existing draft, produce fresh greeting
        greeting = """Hi! I'm here to help you design your talent intake form.

Tell me: what fields would you like to collect from candidates? For example, are you looking for:
- Basic info (name, email, phone)?
- Experience level and background?
- Salary expectations?
- Resume/portfolio links?
- Specific skills or qualifications?

Just describe what you need, and I'll structure it into a schema for you."""

        updates["messages"] = [AIMessage(content=greeting)]

    return updates
