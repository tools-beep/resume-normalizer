from __future__ import annotations

from pydantic import BaseModel


class PersonalInfo(BaseModel):
    full_name: str
    email: str | None = None
    city: str | None = None
    country: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None


class Experience(BaseModel):
    company_name: str
    brief_company_description: str | None = None
    company_location: str | None = None
    candidate_position: str
    tenure_date_range: str | None = None
    responsibilities: list[str] = []
    achievements: list[str] = []


class Education(BaseModel):
    institution_name: str
    institution_location: str | None = None
    course_name: str | None = None
    completion_date: str | None = None


class ResumeData(BaseModel):
    personal_info: PersonalInfo | None = None
    summary: str | None = None
    job_title: str | None = None
    experience: list[Experience] = []
    education: list[Education] = []
    skills: list[str] = []
    interests: list[str] = []
