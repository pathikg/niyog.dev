import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.profile import CandidateProfile
from app.models.user import User
from app.prompts import summarize_profile
from app.services.extraction import (
    extract_profile_from_sections,
    extract_sections_from_resume,
)
from app.services.llm import stream_complete

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/candidates", tags=["candidates"])

ALLOWED_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


def sse_event(event: str, data: dict | str) -> str:
    payload = json.dumps(data) if isinstance(data, dict) else data
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/resume")
async def upload_resume(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum 10MB.")

    async def generate() -> AsyncGenerator[str, None]:
        t_start = time.time()

        yield sse_event("status", {"message": "Reading your resume...", "phase": "extracting"})
        await asyncio.sleep(0)

        try:
            sections, file_hash = await extract_sections_from_resume(
                file_bytes, file.filename or "resume.pdf"
            )
        except Exception as e:
            yield sse_event("error", {"message": f"Failed to read resume: {str(e)}"})
            return

        t_sections = time.time()
        logger.info(f"[TIMING] Section extraction: {t_sections - t_start:.1f}s")

        yield sse_event("status", {"message": "Analyzing your profile...", "phase": "extracting"})
        await asyncio.sleep(0)

        try:
            profile = await extract_profile_from_sections(sections)
        except Exception as e:
            yield sse_event("error", {"message": f"Failed to extract profile: {str(e)}"})
            return

        t_profile = time.time()
        logger.info(f"[TIMING] Profile extraction: {t_profile - t_sections:.1f}s")

        yield sse_event("status", {"message": "Saving your profile...", "phase": "extracting"})
        await asyncio.sleep(0)

        result = await db.execute(
            select(CandidateProfile).where(CandidateProfile.user_id == user.id)
        )
        candidate_profile = result.scalar_one_or_none()

        if candidate_profile is None:
            candidate_profile = CandidateProfile(
                user_id=user.id,
                resume_raw=sections.raw_text,
                resume_sections=sections.model_dump(),
                profile_attributes=profile.model_dump(),
            )
            db.add(candidate_profile)
        else:
            candidate_profile.resume_raw = sections.raw_text
            candidate_profile.resume_sections = sections.model_dump()
            candidate_profile.profile_attributes = profile.model_dump()

        await db.commit()

        t_db = time.time()
        logger.info(f"[TIMING] DB save: {t_db - t_profile:.1f}s")

        yield sse_event("extracted", {
            "resume_sections": sections.model_dump(),
            "profile_attributes": profile.model_dump(),
        })
        await asyncio.sleep(0)

        # Stream the conversational summary token by token
        profile_summary = json.dumps(profile.model_dump(), indent=2)
        user_msg = f"Here is the extracted profile data:\n\n{profile_summary}\n\nPresent this back to the candidate for review."

        t_stream_start = time.time()
        token_count = 0
        async for chunk in stream_complete(
            system_prompt=summarize_profile.SYSTEM_PROMPT,
            user_message=user_msg,
        ):
            token_count += 1
            if token_count == 1:
                logger.info(f"[TIMING] First stream token: {time.time() - t_stream_start:.1f}s")
            yield sse_event("token", {"text": chunk})
            await asyncio.sleep(0)  # Force flush each token

        t_end = time.time()
        logger.info(f"[TIMING] Summary stream: {t_end - t_stream_start:.1f}s ({token_count} chunks)")
        logger.info(f"[TIMING] Total: {t_end - t_start:.1f}s (sections={t_sections-t_start:.1f}s + profile={t_profile-t_sections:.1f}s + db={t_db-t_profile:.1f}s + stream={t_end-t_stream_start:.1f}s)")

        yield sse_event("done", {})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/me/profile")
async def get_my_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found. Upload a resume first.")

    return {
        "profile_attributes": profile.profile_attributes,
        "resume_sections": profile.resume_sections,
        "current_version": profile.current_version,
    }
