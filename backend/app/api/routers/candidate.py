import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.profile import CandidateProfile
from app.models.user import User
from app.prompts import summarize_profile
from app.schemas.candidate import ProfileAttributes, ResumeSections
from app.services.extraction import (
    extract_profile_from_sections,
    extract_sections_from_resume,
)
from app.services.resume_parser import compute_file_hash
from app.services.llm import stream_complete
from app.services.onboarding_chat import get_or_init_state, process_message_streaming

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/candidates", tags=["candidates"])

ALLOWED_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
MAX_SIZE = 1 * 1024 * 1024  # 1MB


def sse_event(event: str, data: dict | str) -> str:
    payload = json.dumps(data) if isinstance(data, dict) else data
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/resume")
async def upload_resume(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        async def error_gen():
            yield sse_event("error", {"message": "That doesn't look like a PDF or DOCX file. Please upload your resume in PDF or DOCX format.", "retry": True})
        return StreamingResponse(error_gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"})

    # Check cache BEFORE size validation — if we already extracted this file, skip everything
    file_hash = compute_file_hash(file_bytes)
    result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user.id)
    )
    existing_profile = result.scalar_one_or_none()

    cached = False
    if existing_profile and existing_profile.resume_sections:
        existing_hash = existing_profile.resume_sections.get("file_hash", "")
        if existing_hash == file_hash:
            cached = True
            logger.info(f"[CACHE] Resume hash match — skipping extraction")

    # Only enforce size limit for new files (not cached)
    if not cached and len(file_bytes) > MAX_SIZE:
        size_mb = len(file_bytes) / (1024 * 1024)
        async def error_gen():
            yield sse_event("error", {"message": f"That file is {size_mb:.1f}MB — please keep it under 1MB. Try compressing your resume or removing embedded images.", "retry": True})
        return StreamingResponse(error_gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"})

    async def generate() -> AsyncGenerator[str, None]:
        nonlocal existing_profile
        t_start = time.time()

        if cached:
            # Use cached data — lenient parsing since DB data may not match schema strictly
            try:
                sections = ResumeSections.model_validate(existing_profile.resume_sections)
                profile = ProfileAttributes.model_validate(existing_profile.profile_attributes)
            except Exception:
                # Schema mismatch — construct from raw dicts without validation
                sections = ResumeSections.model_construct(**existing_profile.resume_sections)
                profile = ProfileAttributes.model_construct(**existing_profile.profile_attributes)

            yield sse_event("status", {"message": "Resume recognized — using cached extraction.", "phase": "extracting"})
            await asyncio.sleep(0)

            logger.info(f"[TIMING] Cache hit — 0s extraction")
        else:
            # Full extraction
            yield sse_event("status", {"message": "Reading your resume...", "phase": "extracting"})
            await asyncio.sleep(0)

            try:
                sections, _ = await extract_sections_from_resume(
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

            # Validate: does this look like a resume?
            profile_data = profile.model_dump() if hasattr(profile, 'model_dump') else dict(profile)
            has_role = bool(profile_data.get("current_role"))
            has_skills = bool(profile_data.get("skills"))
            has_work = bool(profile_data.get("work_history"))
            has_education = bool(profile_data.get("education"))

            if not has_role and not has_skills and not has_work and not has_education:
                yield sse_event("error", {
                    "message": "This doesn't look like a resume/CV — I couldn't find any work experience, skills, or education. Please upload your actual resume and try again.",
                    "retry": True,
                })
                return

            yield sse_event("status", {"message": "Saving your profile...", "phase": "extracting"})
            await asyncio.sleep(0)

            if existing_profile is None:
                existing_profile = CandidateProfile(
                    user_id=user.id,
                    resume_raw=sections.raw_text,
                    resume_sections=sections.model_dump(),
                    profile_attributes=profile.model_dump(),
                )
                db.add(existing_profile)
            else:
                existing_profile.resume_raw = sections.raw_text
                existing_profile.resume_sections = sections.model_dump()
                existing_profile.profile_attributes = profile.model_dump()

            await db.commit()

            t_db = time.time()
            logger.info(f"[TIMING] DB save: {t_db - t_profile:.1f}s")

        # Serialize safely — model_construct objects may not have model_dump
        def safe_dump(obj):
            try:
                return obj.model_dump()
            except Exception:
                return dict(obj) if hasattr(obj, '__iter__') else {}

        sections_data = safe_dump(sections)
        profile_data = safe_dump(profile)

        yield sse_event("extracted", {
            "resume_sections": sections_data,
            "profile_attributes": profile_data,
        })
        await asyncio.sleep(0)

        # Stream the conversational summary token by token
        from datetime import date
        today = date.today().isoformat()
        profile_summary = json.dumps(profile_data, indent=2)
        user_msg = f"Today's date is {today}.\n\nHere is the extracted profile data:\n\n{profile_summary}\n\nPresent this back to the candidate for review."

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
        if cached:
            logger.info(f"[TIMING] Total: {t_end - t_start:.1f}s (cache hit + stream={t_end-t_stream_start:.1f}s)")
        else:
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


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user.id)
    )
    candidate_profile = result.scalar_one_or_none()
    if candidate_profile is None:
        raise HTTPException(status_code=400, detail="Upload a resume first.")

    state = get_or_init_state(
        candidate_profile.conversation_state,
        candidate_profile.profile_attributes or {},
    )

    async def generate() -> AsyncGenerator[str, None]:
        async for event in process_message_streaming(body.message, state):
            if event["type"] == "token":
                yield sse_event("token", {"text": event["text"]})
                await asyncio.sleep(0)
            elif event["type"] == "state_update":
                # Save to DB using a fresh session (streaming generator outlives request session)
                import copy
                from app.database import async_session
                try:
                    async with async_session() as save_db:
                        from sqlalchemy import update
                        stmt = (
                            update(CandidateProfile)
                            .where(CandidateProfile.user_id == user.id)
                            .values(
                                conversation_state=copy.deepcopy(event["state"]),
                                profile_attributes=copy.deepcopy(event["profile"]),
                            )
                        )
                        await save_db.execute(stmt)
                        await save_db.commit()
                    msg_count = len(event["state"].get("messages", []))
                    logger.info(f"[DB] Saved state: {msg_count} messages")
                except Exception as e:
                    logger.error(f"[DB] Failed to save state: {e}")

                yield sse_event("state", {
                    "phase": event["state"].get("phase", ""),
                    "profile_attributes": event["profile"],
                })
                await asyncio.sleep(0)
            elif event["type"] == "done":
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
