from __future__ import annotations

import io

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.resume import ResumeData
from app.templates.resume_template import get_resume_styles
from app.utils.exceptions import PDFRenderError
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _esc(text: str) -> str:
    """Escape XML special characters for ReportLab Paragraph."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _title_location(location: str) -> str:
    """Normalize location to 'Start Case' with comma separator.

    Handles inputs like 'sydney - Australia', 'Kota Baru - Singapore',
    'San Francisco, CA', etc.
    """
    # Split on common separators (dash or comma)
    parts = [p.strip() for p in location.replace(" - ", ",").replace(" – ", ",").split(",") if p.strip()]
    return ", ".join(p.title() for p in parts)


def _two_column_row(
    left_flowable: Paragraph,
    right_flowable: Paragraph,
    col_widths: tuple[float, float],
) -> Table:
    """Create a borderless two-column table row for left/right alignment."""
    table = Table(
        [[left_flowable, right_flowable]],
        colWidths=list(col_widths),
    )
    table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    return table


def render_resume_pdf(data: ResumeData, hide_contact_info: bool = False) -> bytes:
    """Render a ResumeData object into a standardized PDF matching the template spec."""
    try:
        buffer = io.BytesIO()
        styles = get_resume_styles()

        margin = 0.5 * inch
        page_width, page_height = LETTER
        content_width = page_width - margin * 2
        content_height = page_height - margin * 2
        left_col = content_width * 0.65
        right_col = content_width * 0.35

        frame = Frame(
            margin, margin, content_width, content_height,
            leftPadding=0, rightPadding=0,
            topPadding=0, bottomPadding=0,
        )
        doc = BaseDocTemplate(buffer, pagesize=LETTER)
        doc.addPageTemplates([PageTemplate(id="resume", frames=[frame])])

        story: list = []

        # ── HEADER SECTION ──────────────────────────────────────────────

        if data.personal_info:
            info = data.personal_info

            # Row 1: Candidate name — centered, bold, 12pt, uppercase
            story.append(
                Paragraph(_esc(info.full_name.upper()), styles["Name"])
            )

            # Row 2: email | city, country | phone | linkedin_url
            if not hide_contact_info:
                contact_parts: list[str] = []
                if info.email:
                    contact_parts.append(info.email)
                location_str = ", ".join(
                    p.title() for p in [info.city, info.country] if p
                )
                if location_str:
                    contact_parts.append(location_str)
                if info.phone:
                    contact_parts.append(info.phone)
                if info.linkedin_url:
                    contact_parts.append(info.linkedin_url)

                if contact_parts:
                    story.append(
                        Paragraph(
                            _esc(" | ".join(contact_parts)),
                            styles["ContactInfo"],
                        )
                    )

        # ── SUMMARY SECTION ─────────────────────────────────────────────

        if data.summary:
            story.append(
                Paragraph(_esc(data.summary), styles["Summary"])
            )

        # ── HORIZONTAL LINE ─────────────────────────────────────────────

        story.append(Spacer(1, 4))
        story.append(
            HRFlowable(
                width="100%",
                thickness=1,
                color="black",
                spaceBefore=2,
                spaceAfter=6,
            )
        )

        # ── EXPERIENCE SECTION ──────────────────────────────────────────

        if data.experience:
            # Section title: {JOB_TITLE} EXPERIENCE
            title_prefix = data.job_title.upper() + " " if data.job_title else ""
            story.append(
                Paragraph(
                    f"<u>{_esc(title_prefix)}EXPERIENCE</u>",
                    styles["SectionTitle"],
                )
            )

            for exp in data.experience:
                # Row 1: company_name - (brief_description)  |  company_location
                left_text = f"<b>{_esc(exp.company_name)}</b>"
                if exp.brief_company_description:
                    left_text += f" - ({_esc(exp.brief_company_description)})"

                right_text = ""
                if exp.company_location:
                    right_text = f"<b>{_esc(_title_location(exp.company_location))}</b>"

                story.append(
                    _two_column_row(
                        Paragraph(left_text, styles["CompanyLeft"]),
                        Paragraph(right_text, styles["CompanyRight"]),
                        (left_col, right_col),
                    )
                )

                # Row 2: candidate_position (italic)  |  tenure_date_range (italic)
                pos_text = _esc(exp.candidate_position)
                date_text = _esc(exp.tenure_date_range or "")

                story.append(
                    _two_column_row(
                        Paragraph(pos_text, styles["PositionLeft"]),
                        Paragraph(date_text, styles["PositionRight"]),
                        (left_col, right_col),
                    )
                )

                # Row 3: bullet list of responsibilities / achievements
                bullets = exp.responsibilities + exp.achievements
                for item in bullets:
                    story.append(
                        Paragraph(
                            f"\u2022  {_esc(item)}",
                            styles["Bullet"],
                        )
                    )

                story.append(Spacer(1, 6))

        # ── EDUCATION SECTION ───────────────────────────────────────────

        if data.education:
            story.append(
                Paragraph("<u>EDUCATION</u>", styles["SectionTitle"])
            )

            for edu in data.education:
                # Row 1: institution_name (bold, left)  |  institution_location (bold, right)
                left_text = _esc(edu.institution_name)
                right_text = _esc(_title_location(edu.institution_location)) if edu.institution_location else ""

                story.append(
                    _two_column_row(
                        Paragraph(left_text, styles["InstitutionLeft"]),
                        Paragraph(right_text, styles["InstitutionRight"]),
                        (left_col, right_col),
                    )
                )

                # Row 2: course_name (italic, left)  |  completion_date (italic, right)
                course_text = _esc(edu.course_name or "")
                date_text = _esc(edu.completion_date or "")

                story.append(
                    _two_column_row(
                        Paragraph(course_text, styles["CourseLeft"]),
                        Paragraph(date_text, styles["CourseRight"]),
                        (left_col, right_col),
                    )
                )

                story.append(Spacer(1, 4))

        # ── SKILLS & INTERESTS SECTION ──────────────────────────────────

        if data.skills or data.interests:
            story.append(
                Paragraph(
                    "<u>SKILLS &amp; INTERESTS</u>",
                    styles["SectionTitle"],
                )
            )

            all_items = data.skills + data.interests
            if all_items:
                story.append(
                    Paragraph(
                        _esc(", ".join(all_items)),
                        styles["Skills"],
                    )
                )

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        logger.info("PDF rendered", extra={"size_bytes": len(pdf_bytes)})
        return pdf_bytes

    except PDFRenderError:
        raise
    except Exception as e:
        raise PDFRenderError(f"Failed to render PDF: {e}") from e
