import logging
from datetime import datetime, timezone

from pydantic import ValidationError

from app.prompts import extract_profile, extract_sections
from app.schemas.candidate import ProfileAttributes, ResumeSections
from app.services import llm
from app.services.resume_parser import (
    compute_file_hash,
    detect_file_type,
    parse_docx_to_text,
    parse_pdf_to_text,
)

logger = logging.getLogger(__name__)


async def extract_sections_from_resume(
    file_bytes: bytes, filename: str
) -> tuple[ResumeSections, str]:
    """Step 1: Extract structured sections from resume.

    Uses text extraction (pymupdf for PDF, python-docx for DOCX) then sends
    text to LLM for section parsing. This works with any LLM model.

    Returns (ResumeSections, file_hash)
    """
    file_hash = compute_file_hash(file_bytes)
    file_type = detect_file_type(filename)

    if file_type == "pdf":
        raw_text = parse_pdf_to_text(file_bytes)
    else:
        raw_text = parse_docx_to_text(file_bytes)

    result = await llm.complete_json(
        system_prompt=extract_sections.SYSTEM_PROMPT,
        user_message=f"Extract all sections from this resume text:\n\n{raw_text}",
    )

    sections = ResumeSections(
        sections=result.get("sections", []),
        raw_text=result.get("raw_text", raw_text),
        file_hash=file_hash,
        parsed_at=datetime.now(timezone.utc).isoformat(),
    )
    return sections, file_hash


async def extract_profile_from_sections(
    sections: ResumeSections,
) -> ProfileAttributes:
    """Step 2: Extract ProfileAttributes from structured sections."""
    sections_text = ""
    for s in sections.sections:
        sections_text += f"\n## {s.heading}\n{s.content}\n"

    user_msg = extract_profile.USER_PROMPT_TEMPLATE.format(
        sections_text=sections_text
    )

    result = await llm.complete_json(
        system_prompt=extract_profile.SYSTEM_PROMPT,
        user_message=user_msg,
    )

    try:
        profile = ProfileAttributes.model_validate(result)
    except ValidationError as e:
        logger.warning(f"Profile validation failed, using partial data: {e}")
        profile = ProfileAttributes.model_construct(**{
            k: v for k, v in result.items()
            if k in ProfileAttributes.model_fields
        })

    return profile


async def extract_from_resume(
    file_bytes: bytes, filename: str
) -> tuple[ResumeSections, ProfileAttributes]:
    """Full extraction pipeline: file -> sections -> profile attributes.

    This is synchronous from the candidate's perspective — they see results live.
    """
    sections, file_hash = await extract_sections_from_resume(file_bytes, filename)
    profile = await extract_profile_from_sections(sections)
    return sections, profile
