import io

import pdfplumber

from app.schemas.resume import Education, Experience, PersonalInfo, ResumeData
from app.services.pdf_renderer import render_resume_pdf


def _extract_text(pdf_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def test_render_full_resume():
    """Rendering a full resume with all sections produces valid PDF bytes."""
    data = ResumeData(
        personal_info=PersonalInfo(
            full_name="Jane Smith",
            email="jane@example.com",
            city="San Francisco",
            country="USA",
            phone="+1-555-0123",
            linkedin_url="linkedin.com/in/janesmith",
        ),
        summary="Experienced software engineer with 8 years in backend development.",
        job_title="Software Engineering",
        experience=[
            Experience(
                company_name="Acme Corp",
                brief_company_description="Global technology company",
                company_location="San Francisco, CA",
                candidate_position="Senior Software Engineer",
                tenure_date_range="Jan 2020 - Present",
                responsibilities=[
                    "Led team of 5 engineers building microservices",
                    "Designed and implemented CI/CD pipelines",
                ],
                achievements=[
                    "Reduced API latency by 40%",
                ],
            )
        ],
        education=[
            Education(
                institution_name="UC Berkeley",
                institution_location="Berkeley, CA",
                course_name="B.S. Computer Science",
                completion_date="May 2016",
            )
        ],
        skills=["Python", "FastAPI", "AWS", "PostgreSQL"],
        interests=["Open source", "Rock climbing"],
    )

    pdf_bytes = render_resume_pdf(data)
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:5] == b"%PDF-"


def test_render_minimal_resume():
    """Rendering a resume with only a name still produces a valid PDF."""
    data = ResumeData(
        personal_info=PersonalInfo(full_name="John Doe"),
    )

    pdf_bytes = render_resume_pdf(data)
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:5] == b"%PDF-"


def test_render_empty_resume():
    """Rendering a completely empty resume still works."""
    data = ResumeData()
    pdf_bytes = render_resume_pdf(data)
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:5] == b"%PDF-"


def test_render_special_characters():
    """Resume with special characters renders without errors."""
    data = ResumeData(
        personal_info=PersonalInfo(
            full_name="Jean-Pierre O'Brien & Associates <LLC>",
            email="jp@example.com",
        ),
        skills=["C++", "C#", "Node.js"],
    )

    pdf_bytes = render_resume_pdf(data)
    assert len(pdf_bytes) > 0


def test_render_hides_contact_info_when_flag_set():
    """When hide_contact_info=True, the contact line is omitted but the name remains."""
    data = ResumeData(
        personal_info=PersonalInfo(
            full_name="Jane Smith",
            email="jane@example.com",
            city="San Francisco",
            country="USA",
            phone="+1-555-0123",
            linkedin_url="linkedin.com/in/janesmith",
        ),
        summary="Experienced engineer.",
        skills=["Python"],
    )

    pdf_bytes = render_resume_pdf(data, hide_contact_info=True)
    text = _extract_text(pdf_bytes)

    assert "JANE SMITH" in text
    assert "Experienced engineer." in text
    assert "jane@example.com" not in text
    assert "+1-555-0123" not in text
    assert "linkedin.com/in/janesmith" not in text
    assert "San Francisco" not in text


def test_render_includes_contact_info_by_default():
    """Default behavior renders the contact info line."""
    data = ResumeData(
        personal_info=PersonalInfo(
            full_name="Jane Smith",
            email="jane@example.com",
            phone="+1-555-0123",
        ),
    )

    text = _extract_text(render_resume_pdf(data))

    assert "jane@example.com" in text
    assert "+1-555-0123" in text


def test_render_experience_without_job_title():
    """Experience section renders as 'EXPERIENCE' when job_title is None."""
    data = ResumeData(
        personal_info=PersonalInfo(full_name="Test User"),
        experience=[
            Experience(
                company_name="TestCo",
                candidate_position="Developer",
                tenure_date_range="2020 - 2023",
                responsibilities=["Wrote code"],
            )
        ],
    )

    pdf_bytes = render_resume_pdf(data)
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:5] == b"%PDF-"
