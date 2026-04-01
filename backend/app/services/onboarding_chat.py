import json
import logging
from collections.abc import AsyncGenerator
from copy import deepcopy
from datetime import date

from app.prompts import gap_fill, review_correction
from app.services import llm

logger = logging.getLogger(__name__)


def _chunk_text(text: str, chunk_size: int = 6) -> list[str]:
    """Split text into small chunks for simulated streaming."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


CHAT_STEERING_PROMPT = """You are Niyog, a profile-building assistant. Your ONLY job is to help the candidate complete their hiring profile.

STRICT RULES:
- Rewrite the given message in a friendly, conversational tone
- NEVER answer general questions, give career advice, or chat about anything unrelated
- ALWAYS steer the conversation back to completing/correcting the profile
- If the user asks something off-topic, acknowledge briefly then redirect: "Let's focus on getting your profile right first!"
- Keep responses short — 1-3 sentences max
- Output ONLY the rewritten message, nothing else"""

# All fields we want to collect during gap-filling
GAP_FILL_FIELDS = [
    "current_ctc",
    "expected_ctc",
    "notice_period",
    "job_switch",
    "location.remote_preference",
    "location.open_to",
    "location.willing_to_relocate",
    "preferences.looking_for",
    "preferences.dealbreakers",
]


def _get_initial_state(profile_attributes: dict) -> dict:
    return {
        "phase": "reviewing_extraction",
        "extracted_profile": deepcopy(profile_attributes),
        "current_profile": deepcopy(profile_attributes),
        "corrections": [],
        "skipped_fields": [],
        "messages": [],
    }


def get_or_init_state(conversation_state: dict | None, profile_attributes: dict) -> dict:
    if conversation_state and conversation_state.get("messages"):
        return conversation_state
    return _get_initial_state(profile_attributes)


def _is_meaningfully_filled(val) -> bool:
    """Check if a value has actual meaningful data, not just empty/default structure."""
    if val is None or val == [] or val == "" or val == 0:
        return False
    if isinstance(val, dict):
        # A dict with all None/empty values is not meaningfully filled
        # But ignore known default keys like "currency"
        meaningful_values = [
            v for k, v in val.items()
            if k not in ("currency", "unit") and v is not None and v != [] and v != ""
        ]
        return len(meaningful_values) > 0
    return True


def _fields_already_filled(profile: dict, fields: list[str]) -> bool:
    """Check if all fields in a batch are already meaningfully filled."""
    for field in fields:
        parts = field.split(".")
        val = profile
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                val = None
                break
        if not _is_meaningfully_filled(val):
            return False
    return True


def _apply_corrections(profile: dict, corrections: list[dict]) -> dict:
    """Apply parsed corrections to the profile."""
    for corr in corrections:
        field = corr.get("field", "")
        new_val = corr.get("new_value")
        action = corr.get("action", "modified")

        if field == "skills" and action == "added" and isinstance(new_val, dict):
            if "skills" not in profile:
                profile["skills"] = []
            # Dedup: don't add if skill already exists
            raw_name = new_val.get("raw", "").lower()
            existing = [s.get("raw", "").lower() for s in profile["skills"]]
            if raw_name not in existing:
                profile["skills"].append(new_val)
        elif field == "skills" and action == "removed" and isinstance(new_val, dict):
            raw_name = new_val.get("raw", "").lower()
            profile["skills"] = [s for s in profile.get("skills", []) if s.get("raw", "").lower() != raw_name]
        elif "." in field:
            parts = field.split(".")
            obj = profile
            for p in parts[:-1]:
                if p not in obj or not isinstance(obj[p], dict):
                    obj[p] = {}
                obj = obj[p]
            obj[parts[-1]] = new_val
        else:
            profile[field] = new_val

    return profile


def _apply_gap_fields(profile: dict, parsed_fields: dict) -> dict:
    """Apply gap-fill parsed fields to the profile."""
    for field, value in parsed_fields.items():
        if "." in field:
            parts = field.split(".")
            obj = profile
            for p in parts[:-1]:
                if p not in obj or not isinstance(obj[p], dict):
                    obj[p] = {}
                obj = obj[p]
            obj[parts[-1]] = value
        else:
            profile[field] = value
    return profile


async def process_message_streaming(
    user_message: str,
    state: dict,
) -> AsyncGenerator[dict, None]:
    """One unified chat handler — no phases, just conversation.

    LLM sees full message history and decides what to do.
    Sends <EOS> when profile is complete, then we extract and save.
    """
    profile = state["current_profile"]
    state.setdefault("messages", [])

    # On first message, seed the conversation so LLM knows to start collecting info
    if len(state["messages"]) == 0:
        state["messages"].append({
            "role": "assistant",
            "content": "Great, your resume looks good! Now I just need a few more details to complete your profile. What's your current CTC? Feel free to break it down — base, variable, ESOP if applicable. And what range are you expecting in your next role?"
        })

    state["messages"].append({"role": "user", "content": user_message})

    logger.info(f"[CHAT] msg='{user_message[:50]}', history_len={len(state['messages'])}")

    # Stream response using proper multi-turn messages
    response_text = ""
    async for chunk in llm.stream_chat(
        system_prompt=gap_fill.CHAT_PROMPT,
        messages=state["messages"],
    ):
        if "<EOS>" in chunk:
            chunk = chunk.replace("<EOS>", "")
        response_text += chunk
        if chunk.strip():
            yield {"type": "token", "text": chunk}

    state["messages"].append({"role": "assistant", "content": response_text})

    # Check if LLM signaled done — via <EOS> or natural completion phrases
    completion_signals = ["<EOS>", "you're all set", "you're all done", "profile is complete", "good luck", "all the best", "wishing you"]
    is_complete = any(signal.lower() in response_text.lower() for signal in completion_signals)

    if is_complete:
        logger.info("[CHAT] Completion detected — extracting from full conversation")

        convo_text = "\n".join(f"{m['role']}: {m['content']}" for m in state["messages"])
        extracted = await llm.complete_json(
            system_prompt=gap_fill.EXTRACT_PROMPT,
            user_message=f"Extract all profile fields from this conversation:\n\n{convo_text}",
        )
        logger.info(f"[CHAT] Extracted: {json.dumps(extracted, default=str)[:500]}")

        for key, value in extracted.items():
            if value is not None:
                if isinstance(value, dict):
                    if key in profile and isinstance(profile[key], dict):
                        profile[key].update({k: v for k, v in value.items() if v is not None})
                    else:
                        profile[key] = value
                else:
                    profile[key] = value

        state["current_profile"] = profile
        state["phase"] = "complete"

    yield {"type": "state_update", "state": state, "profile": profile}
    yield {"type": "done"}


def _get_missing_fields(profile: dict, skipped: list[str]) -> list[str]:
    """Get list of gap-fill fields that are still missing and not skipped."""
    missing = []
    for field in GAP_FILL_FIELDS:
        if field in skipped:
            continue
        parts = field.split(".")
        val = profile
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                val = None
                break
        if not _is_meaningfully_filled(val):
            missing.append(field)
    return missing


def _transition_to_gap_filling(state: dict, profile: dict) -> str:
    """Transition to gap-filling phase."""
    state["phase"] = "gap_filling"

    missing = _get_missing_fields(profile, state.get("skipped_fields", []))
    if not missing:
        state["phase"] = "complete"
        return "Your profile is now complete! Head to the dashboard to view it."

    return f"Great! Now I have a few more questions to complete your profile. Let's start — what's your current CTC? Feel free to break it down (base, variable, ESOP). And what range are you expecting in your next role?"


async def _handle_review_streaming(
    user_message: str, state: dict, profile: dict
) -> AsyncGenerator[dict, None]:
    """Handle messages during the review phase."""
    # Track conversation history — stays in memory, saved to DB at end
    state.setdefault("messages", [])
    state["messages"].append({"role": "user", "content": user_message})

    today = date.today().isoformat()
    profile_summary = json.dumps(profile, indent=2)

    # Include recent conversation for context
    recent_messages = state["messages"][-8:]
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent_messages[:-1])

    user_prompt = (
        f"Today's date: {today}\n\n"
        f"Current extracted profile:\n{profile_summary}\n\n"
        f"Recent conversation:\n{history_text}\n\n"
        f"Candidate's latest message: {user_message}\n\n"
        f"Identify corrections or if they're done reviewing."
    )

    result = await llm.complete_json(
        system_prompt=review_correction.SYSTEM_PROMPT,
        user_message=user_prompt,
    )

    action = result.get("action", "general")
    corrections = result.get("corrections", [])

    # Apply corrections
    if corrections:
        _apply_corrections(profile, corrections)
        for corr in corrections:
            state["corrections"].append({
                "field": corr.get("field"),
                "action": corr.get("action", "modified"),
                "extracted_value": _get_field(state["extracted_profile"], corr.get("field")),
                "user_value": corr.get("new_value"),
                "user_reason": corr.get("reason"),
            })

    state["current_profile"] = profile

    if action == "done_reviewing":
        response = _transition_to_gap_filling(state, profile)
    else:
        response = result.get("response", "Got it!")

    # Track assistant response
    state["messages"].append({"role": "assistant", "content": response})

    # Stream response directly
    for chunk in _chunk_text(response, 6):
        yield {"type": "token", "text": chunk}

    yield {"type": "state_update", "state": state, "profile": profile}
    yield {"type": "done"}


async def _handle_gap_fill_streaming(
    user_message: str, state: dict, profile: dict
) -> AsyncGenerator[dict, None]:
    """Pure multi-turn chat. Messages kept in memory, DB write only at <EOS>."""
    state.setdefault("messages", [])
    state["messages"].append({"role": "user", "content": user_message})

    # Pass actual messages array to LLM — proper multi-turn, not text dump
    response_text = ""
    async for chunk in llm.stream_chat(
        system_prompt=gap_fill.CHAT_PROMPT,
        messages=state["messages"],
    ):
        if "<EOS>" in chunk:
            chunk = chunk.replace("<EOS>", "")
        response_text += chunk
        if chunk.strip():
            yield {"type": "token", "text": chunk}

    state["messages"].append({"role": "assistant", "content": response_text})

    # Check if LLM signaled done
    if "<EOS>" in response_text:
        logger.info("[GAP-FILL] <EOS> detected — extracting from full conversation")

        convo_text = "\n".join(f"{m['role']}: {m['content']}" for m in state["messages"])
        extracted = await llm.complete_json(
            system_prompt=gap_fill.EXTRACT_PROMPT,
            user_message=f"Extract all profile fields from this conversation:\n\n{convo_text}",
        )
        logger.info(f"[GAP-FILL] Extracted: {json.dumps(extracted, default=str)[:500]}")

        # Apply to profile
        for key, value in extracted.items():
            if value is not None:
                if isinstance(value, dict):
                    if key in profile and isinstance(profile[key], dict):
                        profile[key].update({k: v for k, v in value.items() if v is not None})
                    else:
                        profile[key] = value
                else:
                    profile[key] = value

        state["current_profile"] = profile
        state["phase"] = "complete"

    yield {"type": "state_update", "state": state, "profile": profile}
    yield {"type": "done"}


def _get_field(profile: dict, field: str):
    if not field:
        return None
    parts = field.split(".")
    val = profile
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p)
        else:
            return None
    return val
