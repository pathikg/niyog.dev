"""Thread ID constructors for LangGraph graphs."""

from uuid import UUID


def hr_schema_thread_id(company_id: str | UUID, hr_user_id: str | UUID, session_id: str) -> str:
    """
    Construct thread_id for HR Schema Graph.

    Format: hr-{company_id}-{hr_user_id}-{session_id}

    Each HR session gets a unique thread_id. If same HR returns to same session_id,
    they resume from the last checkpoint.

    Args:
        company_id: Company UUID
        hr_user_id: HR User UUID
        session_id: Browser/session UUID (generated fresh per login)

    Returns:
        str: Unique thread_id for LangGraph checkpointer
    """
    return f"hr-{company_id}-{hr_user_id}-{session_id}"


def talent_onboarding_thread_id(
    company_id: str | UUID,
    talent_id: str | UUID,
    onboarding_session_id: str | UUID,
) -> str:
    """
    Construct thread_id for Talent Onboarding Graph.

    Format: talent-{company_id}-{talent_id}-{onboarding_session_id}

    Each talent onboarding flow gets a unique thread_id. Corresponds to one row
    in the onboarding_sessions table.

    Args:
        company_id: Company UUID
        talent_id: Talent User UUID
        onboarding_session_id: OnboardingSession UUID (from DB)

    Returns:
        str: Unique thread_id for LangGraph checkpointer
    """
    return f"talent-{company_id}-{talent_id}-{onboarding_session_id}"
