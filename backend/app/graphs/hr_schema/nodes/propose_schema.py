"""Propose node: Claude extracts structured schema from HR's natural language."""

import json
from langchain_core.messages import AIMessage, HumanMessage
from langchain_anthropic import ChatAnthropic

from app.graphs.hr_schema.state import HRSchemaState
from app.graphs.hr_schema.prompts import (
    PROPOSE_SCHEMA_SYSTEM,
    PROPOSE_SCHEMA_PROMPT,
    FORMAT_SCHEMA_PROMPT,
)


async def propose_schema(state: HRSchemaState) -> dict:
    """
    Claude extracts a structured schema from HR's description.

    Assumes the HR's last message (in state["messages"]) describes what fields they want.
    Calls Claude to extract and structure the schema as JSONB.

    Returns:
        dict with current_definition set to extracted JSONB, plus formatted summary message
    """

    # Get HR's description from last message
    if not state["messages"]:
        return {
            "messages": [AIMessage(content="I didn't receive your description. Please tell me what fields you'd like to collect.")]
        }

    last_message = state["messages"][-1]
    hr_description = last_message.content

    # Call Claude to extract schema
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

    # System + user prompt
    extraction_messages = [
        ("system", PROPOSE_SCHEMA_SYSTEM),
        ("user", PROPOSE_SCHEMA_PROMPT.format(hr_description=hr_description)),
    ]

    try:
        response = await llm.ainvoke(extraction_messages)
        schema_json_str = response.content

        # Parse the JSON response
        extracted_definition = json.loads(schema_json_str)

        # Format the schema as a human-readable summary
        format_messages = [
            ("system", "You are an expert at formatting schema definitions as human-readable lists."),
            ("user", FORMAT_SCHEMA_PROMPT.format(definition=json.dumps(extracted_definition))),
        ]

        summary_response = await llm.ainvoke(format_messages)
        summary = summary_response.content

        response_text = f"""Great! I've designed the following schema based on your description:

{summary}

Does this look good? You can tell me to:
- **Modify** any field
- **Add** a new field
- **Remove** a field
- **Test** it in sandbox mode
- **Save** it as a draft
- **Activate** it when ready"""

        return {
            "current_definition": extracted_definition,
            "current_version": 1,  # New schema starts at v1
            "phase": "iterating",
            "messages": [AIMessage(content=response_text)],
        }

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse schema JSON from Claude: {str(e)[:100]}"
        return {
            "messages": [AIMessage(content=f"I had trouble structuring the schema. Could you provide more details? Error: {error_msg}")]
        }
    except Exception as e:
        error_msg = f"Error calling Claude: {str(e)[:100]}"
        return {
            "messages": [AIMessage(content=f"I encountered an error: {error_msg}")]
        }
