"""LangGraph checkpointer setup for PostgreSQL persistence."""

from langgraph.checkpoint.postgres import aio as pg_checkpointer
from app.config import settings


async def get_checkpointer():
    """
    Create and initialize AsyncPostgresSaver checkpointer.

    The checkpointer uses the same PostgreSQL connection string as the app.
    It automatically creates its own tables (checkpoint_writes, checkpoint_blobs, etc.)
    on first setup().

    Returns:
        aio.AsyncPostgresSaver: Configured checkpointer for both HR and Talent graphs
    """
    checkpointer = pg_checkpointer.AsyncPostgresSaver(
        conn_string=settings.DATABASE_URL,
    )
    # Setup creates the checkpointer tables if they don't exist
    await checkpointer.setup()
    return checkpointer


def create_checkpointer_sync():
    """
    Synchronous wrapper for creating checkpointer in sync contexts.

    Note: This is for testing/scripting only. In FastAPI, use async context.
    """
    import asyncio
    return asyncio.run(get_checkpointer())
