"""Update node: Claude modifies the schema based on HR's request."""

import json
from langchain_core.messages import AIMessage
from langchain_anthropic import ChatAnthropic

from app.graphs.hr_schema.state import HRSchemaState
from app.graphs.hr_schema.prompts import (
    UPDATE_SCHEMA_SYSTEM,
    UPDATE_SCHEMA_PROMPT,
    FORMAT_SCHEMA_PROMPT,
)


async def update_schema(state: HRSchemaState) -> dict:
    """
    Claude applies modifications to the current schema definition.

    Takes the HR's request (last message) and current_definition, then returns
    an updated definition.

    Returns:
        dict with updated current_definition and formatted summary
    """

    if not state["current_definition"]:
        return {
            "messages": [AIMessage(content="No schema to update. Please describe what you'd like to collect first.")]
        }

    if not state["messages"]:
        return {
            "messages": [AIMessage(content="I didn't receive your request. What would you like to change?")]
        }

    last_message = state["messages"][-1]
    hr_request = last_message.content

    # Call Claude to update schema
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

    update_messages = [
        ("system", UPDATE_SCHEMA_SYSTEM),
        ("user", UPDATE_SCHEMA_PROMPT.format(
            current_definition=json.dumps(state["current_definition"], indent=2),
            hr_message=hr_request,
        )),
    ]

    try:
        response = await llm.ainvoke(update_messages)
        schema_json_str = response.content

        # Parse updated definition
        updated_definition = json.loads(schema_json_str)

        # Format as summary
        format_messages = [
            ("system", "You are an expert at formatting schema definitions as human-readable lists."),
            ("user", FORMAT_SCHEMA_PROMPT.format(definition=json.dumps(updated_definition))),
        ]

        summary_response = await llm.ainvoke(format_messages)
        summary = summary_response.content

        response_text = f"""Done! Here's the updated schema:

{summary}

What would you like to do next?
- **Modify** further
- **Add/Remove** fields
- **Test** in sandbox
- **Save** it
- **Activate** it"""

        return {
            "current_definition": updated_definition,
            "phase": "iterating",
            "messages": [AIMessage(content=response_text)],
        }

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse updated schema: {str(e)[:100]}"
        return {
            "messages": [AIMessage(content=f"I had trouble updating the schema. {error_msg}")]
        }
    except Exception as e:
        error_msg = f"Error: {str(e)[:100]}"
        return {
            "messages": [AIMessage(content=f"I encountered an error updating the schema: {error_msg}")]
        }
