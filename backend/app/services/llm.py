import json
import logging
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=settings.OPENROUTER_BASE_URL,
            api_key=settings.OPENROUTER_API_KEY,
        )
    return _client


async def complete(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> str:
    """Text completion via OpenRouter."""
    client = get_client()
    response = await client.chat.completions.create(
        model=model or settings.OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
    )
    return response.choices[0].message.content or ""


async def stream_complete(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
) -> AsyncGenerator[str, None]:
    """Streaming text completion — yields chunks as they arrive."""
    client = get_client()
    stream = await client.chat.completions.create(
        model=model or settings.OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content


async def stream_chat(
    system_prompt: str,
    messages: list[dict],
    model: str | None = None,
) -> AsyncGenerator[str, None]:
    """Streaming chat with full message history — proper multi-turn conversation."""
    client = get_client()
    all_messages = [{"role": "system", "content": system_prompt}] + messages
    stream = await client.chat.completions.create(
        model=model or settings.OPENROUTER_MODEL,
        messages=all_messages,
        temperature=0.3,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content


async def complete_vision(
    system_prompt: str,
    images_b64: list[str],
    user_message: str = "Extract the information from this resume.",
    model: str | None = None,
) -> str:
    """Vision completion — send images + text to a vision-capable model."""
    client = get_client()

    content: list[dict] = [{"type": "text", "text": user_message}]
    for img_b64 in images_b64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_b64}"},
        })

    response = await client.chat.completions.create(
        model=model or settings.OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        temperature=0.1,
    )
    return response.choices[0].message.content or ""


def extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (```json and ```)
        lines = [l for l in lines[1:] if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)


async def complete_json(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    retry: bool = True,
) -> dict:
    """Complete and parse JSON response, with one retry on parse failure."""
    raw = await complete(system_prompt, user_message, model)
    try:
        return extract_json(raw)
    except (json.JSONDecodeError, ValueError) as e:
        if not retry:
            raise
        logger.warning(f"JSON parse failed, retrying. Error: {e}")
        retry_msg = (
            f"Your previous response was not valid JSON. Error: {e}\n"
            f"Please respond with ONLY valid JSON, no markdown or extra text.\n"
            f"Original request: {user_message}"
        )
        raw = await complete(system_prompt, retry_msg, model)
        return extract_json(raw)


async def complete_vision_json(
    system_prompt: str,
    images_b64: list[str],
    user_message: str = "Extract the information from this resume.",
    model: str | None = None,
    retry: bool = True,
) -> dict:
    """Vision completion that returns parsed JSON."""
    raw = await complete_vision(system_prompt, images_b64, user_message, model)
    try:
        return extract_json(raw)
    except (json.JSONDecodeError, ValueError) as e:
        if not retry:
            raise
        logger.warning(f"Vision JSON parse failed, retrying with text. Error: {e}")
        retry_msg = (
            f"Your previous response was not valid JSON. Error: {e}\n"
            f"Please respond with ONLY valid JSON, no markdown or extra text.\n"
            f"Original request: {user_message}"
        )
        raw = await complete(system_prompt, retry_msg, model)
        return extract_json(raw)
