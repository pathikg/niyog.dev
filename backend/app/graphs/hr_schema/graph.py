"""HR Schema Graph: Conversational schema design loop."""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import aio as pg_checkpointer

from app.graphs.hr_schema.state import HRSchemaState
from app.graphs.hr_schema.nodes.greet_hr import greet_hr
from app.graphs.hr_schema.nodes.propose_schema import propose_schema
from app.graphs.hr_schema.nodes.classify_hr_intent import classify_hr_intent
from app.graphs.hr_schema.nodes.update_schema import update_schema
from app.graphs.hr_schema.nodes.save_schema import save_schema
from app.graphs.hr_schema.nodes.activate_schema import activate_schema


def route_on_intent(state: HRSchemaState) -> Literal["update_schema", "save_schema", "activate_schema", "end"]:
    """
    Route next node based on hr_intent classification.

    - modify/add_field/remove_field → update_schema (loop back to classify after)
    - save → save_schema → END
    - activate → activate_schema → END
    - other → END
    """
    intent = state.get("hr_intent", "other")

    if intent in ["modify", "add_field", "remove_field"]:
        return "update_schema"
    elif intent == "save":
        return "save_schema"
    elif intent == "activate":
        return "activate_schema"
    else:
        return "end"


async def build_hr_schema_graph(checkpointer: pg_checkpointer.AsyncPostgresSaver):
    """
    Build and compile the HR Schema Graph.

    Phase 3 graph:
    greet_hr → propose_schema → [INTERRUPT] → classify_hr_intent →
        ├── modify/add/remove → update_schema → propose_schema (loop)
        ├── save             → save_schema    → END
        ├── activate         → activate_schema → END
        └── other            → END

    Args:
        checkpointer: AsyncPostgresSaver for state persistence

    Returns:
        Compiled StateGraph with checkpointer
    """
    graph = StateGraph(HRSchemaState)

    # Add nodes
    graph.add_node("greet_hr", greet_hr)
    graph.add_node("propose_schema", propose_schema)
    graph.add_node("classify_hr_intent", classify_hr_intent)
    graph.add_node("update_schema", update_schema)
    graph.add_node("save_schema", save_schema)
    graph.add_node("activate_schema", activate_schema)

    # Add edges
    graph.add_edge(START, "greet_hr")
    graph.add_edge("greet_hr", "propose_schema")
    graph.add_edge("propose_schema", "classify_hr_intent")

    # Conditional routing based on intent
    graph.add_conditional_edges(
        "classify_hr_intent",
        route_on_intent,
        {
            "update_schema": "update_schema",
            "save_schema": "save_schema",
            "activate_schema": "activate_schema",
            "end": END,
        },
    )

    # update_schema loops back to propose_schema (for iteration)
    graph.add_edge("update_schema", "propose_schema")

    # Terminal nodes
    graph.add_edge("save_schema", END)
    graph.add_edge("activate_schema", END)

    # Compile with checkpointer for persistence
    compiled = graph.compile(checkpointer=checkpointer)

    return compiled


# For testing/scripting convenience
async def create_hr_schema_graph(database_url: str):
    """
    Create checkpointer and build graph (for scripts).

    Args:
        database_url: PostgreSQL connection string

    Returns:
        Compiled graph ready to invoke
    """
    checkpointer = pg_checkpointer.AsyncPostgresSaver(
        conn_string=database_url,
    )
    await checkpointer.setup()
    return await build_hr_schema_graph(checkpointer)
