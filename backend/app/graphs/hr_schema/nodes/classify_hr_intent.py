"""Classify node: LLM determines HR's intent from their message."""

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.graphs.hr_schema.state import HRSchemaState
from app.graphs.hr_schema.prompts import (
    CLASSIFY_HR_INTENT_SYSTEM,
    CLASSIFY_HR_INTENT_PROMPT,
)


async def classify_hr_intent(state: HRSchemaState) -> dict:
    """
    LLM classifies the HR user's intent.

    Parses the last human message and determines what action they want:
    - modify: change something in the schema
    - add_field: add a new field
    - remove_field: remove a field
    - test: test in sandbox
    - save: save as draft
    - activate: activate the schema
    - other: something else

    Returns:
        dict with hr_intent set to the classified action
    """

    if not state["messages"]:
        return {"hr_intent": "other"}

    last_message = state["messages"][-1]
    if not hasattr(last_message, "content"):
        return {"hr_intent": "other"}

    last_content = last_message.content

    # Call local LLM (LM Studio OpenAI-compatible)
    llm = ChatOpenAI(
        base_url=settings.LM_STUDIO_BASE_URL,
        api_key=settings.LM_STUDIO_API_KEY or "not-needed",
        model=settings.LM_STUDIO_MODEL,
        temperature=0.7,
    )

    classification_messages = [
        ("system", CLASSIFY_HR_INTENT_SYSTEM),
        ("user", CLASSIFY_HR_INTENT_PROMPT.format(last_message=last_content)),
    ]

    try:
        response = await llm.ainvoke(classification_messages)
        intent_str = response.content.strip().lower()

        # Validate the intent
        valid_intents = ["modify", "add_field", "remove_field", "test", "save", "activate", "other"]
        intent = intent_str if intent_str in valid_intents else "other"

        return {"hr_intent": intent}

    except Exception as e:
        print(f"Error classifying intent: {e}")
        return {"hr_intent": "other"}
