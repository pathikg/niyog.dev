"""State definition for HR Schema Graph."""

from typing import TypedDict, Annotated, Optional, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class HRSchemaState(TypedDict):
    """
    State for the HR Schema Design conversation loop.

    Fields:
        - Identity: company_id, hr_user_id, session_id
        - Conversation: messages (with add_messages reducer for appending)
        - Schema: current_definition (working JSONB), current_version, schema_id (DB ID)
        - Control: phase (proposing|iterating|sandbox|done), hr_intent (action intent)
        - Sandbox: sandbox_active (bool), sandbox_simulated_answers (dict)
    """

    # ── Identity ──────────────────────────────────────────
    company_id: str
    hr_user_id: str
    session_id: str

    # ── Conversation ──────────────────────────────────────
    # add_messages reducer: appends new messages, never overwrites
    messages: Annotated[list[BaseMessage], add_messages]

    # ── Schema Under Construction ─────────────────────────
    # Mutable working draft; replaced on each update
    current_definition: Optional[dict[str, Any]]
    # Version number for display ("You're editing v3")
    current_version: Optional[int]
    # DB row ID once saved as draft
    schema_id: Optional[str]

    # ── Control Flow ──────────────────────────────────────
    # "proposing" | "iterating" | "sandbox" | "saving" | "done"
    phase: str
    # HR's last intent parsed from their message
    # "propose" | "modify" | "add_field" | "remove_field" |
    # "test" | "save" | "activate" | "other" | None
    hr_intent: Optional[str]

    # ── Sandbox ───────────────────────────────────────────
    # When HR tests, we simulate talent messages here
    sandbox_active: bool
    sandbox_simulated_answers: Optional[dict[str, Any]]
