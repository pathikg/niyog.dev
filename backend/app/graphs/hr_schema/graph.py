"""HR Schema Graph: Conversational schema design loop."""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import aio as pg_checkpointer

from app.graphs.hr_schema.state import HRSchemaState
from app.graphs.hr_schema.nodes.greet_hr import greet_hr


async def build_hr_schema_graph(checkpointer: pg_checkpointer.AsyncPostgresSaver):
    """
    Build and compile the HR Schema Graph.

    Minimal Phase 2 version: greet_hr → interrupt → END

    Full graph (for reference):
    greet_hr → propose_schema → [INTERRUPT] → classify_hr_input →
        ├── modify/add/remove → update_schema → [INTERRUPT] (loop)
        ├── test             → enter_sandbox  → [INTERRUPT] (loop)
        ├── save             → save_schema    → END
        └── activate         → activate_schema → END

    Args:
        checkpointer: AsyncPostgresSaver for state persistence

    Returns:
        Compiled StateGraph with checkpointer
    """
    graph = StateGraph(HRSchemaState)

    # Add nodes
    graph.add_node("greet_hr", greet_hr)

    # Add edges
    graph.add_edge(START, "greet_hr")
    graph.add_edge("greet_hr", END)  # For Phase 2, stop after greeting

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
