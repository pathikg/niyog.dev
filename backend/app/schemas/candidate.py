from __future__ import annotations

from pydantic import BaseModel


class Duration(BaseModel):
    value: float | None = None
    unit: str = "years"


class WorkHistoryItem(BaseModel):
    company: str | None = None
    role: str | None = None
    duration: Duration | None = None
    raw_description: str | None = None
    skills_used: list[str] = []


class Skill(BaseModel):
    raw: str
    normalized: str | None = None
    category: str | None = None
    proficiency: str | None = None
    years_used: float | None = None
    context: str | None = None


class CTC(BaseModel):
    value: int | None = None
    currency: str = "INR"
    includes_esop: bool | None = None


class CTCRange(BaseModel):
    min: int | None = None
    max: int | None = None
    currency: str = "INR"


class Location(BaseModel):
    current_city: str | None = None
    open_to: list[str] = []
    remote_preference: str | None = None
    willing_to_relocate: bool | None = None


class EducationParsed(BaseModel):
    degree: str | None = None
    field: str | None = None
    institution: str | None = None
    year: int | None = None


class Education(BaseModel):
    raw: str | None = None
    parsed: EducationParsed | None = None


class NoticePeriod(BaseModel):
    days: int | None = None
    negotiable: bool | None = None
    note: str | None = None


class JobSwitch(BaseModel):
    reason: str | None = None
    urgency: str | None = None
    actively_interviewing: bool | None = None
    offers_in_hand: int | None = None


class Preferences(BaseModel):
    looking_for: str | None = None
    dealbreakers: list[str] = []
    preferred_company_stage: list[str] = []
    preferred_team_size: str | None = None


class Extras(BaseModel):
    languages_spoken: list[str] = []
    certifications: list[str] = []
    open_source_contributions: str | None = None
    portfolio_url: str | None = None


class ProfileAttributes(BaseModel):
    current_role: str | None = None
    seniority: str | None = None
    total_experience: Duration | None = None
    work_history: list[WorkHistoryItem] = []
    skills: list[Skill] = []
    current_ctc: CTC | None = None
    expected_ctc: CTCRange | None = None
    location: Location | None = None
    education: Education | None = None
    notice_period: NoticePeriod | None = None
    job_switch: JobSwitch | None = None
    preferences: Preferences | None = None
    extras: Extras | None = None


class ResumeSection(BaseModel):
    heading: str
    content: str
    order: int


class ResumeSections(BaseModel):
    sections: list[ResumeSection] = []
    raw_text: str = ""
    file_hash: str = ""
    parsed_at: str | None = None


class ResumeUploadResponse(BaseModel):
    resume_sections: ResumeSections
    profile_attributes: ProfileAttributes
    message: str = "Resume processed successfully"
