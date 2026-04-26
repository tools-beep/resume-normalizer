from __future__ import annotations

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle


def get_resume_styles() -> dict[str, ParagraphStyle]:
    """Return paragraph styles matching the resume template spec.

    All fonts are Times-Roman (ReportLab's built-in Times New Roman equivalent).
    """
    styles: dict[str, ParagraphStyle] = {}

    # Header: candidate name — centered, bold, 12pt, uppercase handled in renderer
    styles["Name"] = ParagraphStyle(
        "Name",
        fontName="Times-Bold",
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        spaceAfter=2,
    )

    # Contact info row — centered, 10pt
    styles["ContactInfo"] = ParagraphStyle(
        "ContactInfo",
        fontName="Times-Roman",
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    # Summary / short introduction — left aligned, 10pt
    styles["Summary"] = ParagraphStyle(
        "Summary",
        fontName="Times-Roman",
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
        spaceAfter=6,
    )

    # Section titles — left aligned, bold, 10pt, underline handled via XML tag in renderer
    styles["SectionTitle"] = ParagraphStyle(
        "SectionTitle",
        fontName="Times-Bold",
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        spaceBefore=6,
        spaceAfter=6,
    )

    # Company name + description (left) — bold for company name, regular for description
    styles["CompanyLeft"] = ParagraphStyle(
        "CompanyLeft",
        fontName="Times-Roman",
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
    )

    # Company location (right) — bold
    styles["CompanyRight"] = ParagraphStyle(
        "CompanyRight",
        fontName="Times-Bold",
        fontSize=10,
        leading=13,
        alignment=TA_RIGHT,
    )

    # Position/candidate_position (left) — italic
    styles["PositionLeft"] = ParagraphStyle(
        "PositionLeft",
        fontName="Times-Italic",
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
    )

    # Tenure date range (right) — italic
    styles["PositionRight"] = ParagraphStyle(
        "PositionRight",
        fontName="Times-Italic",
        fontSize=10,
        leading=13,
        alignment=TA_RIGHT,
    )

    # Bullet list items — justified, 10pt
    styles["Bullet"] = ParagraphStyle(
        "Bullet",
        fontName="Times-Roman",
        fontSize=10,
        leading=13,
        alignment=TA_JUSTIFY,
        leftIndent=0,
        spaceAfter=1,
    )

    # Institution name (left) — bold
    styles["InstitutionLeft"] = ParagraphStyle(
        "InstitutionLeft",
        fontName="Times-Bold",
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
    )

    # Institution location (right) — bold
    styles["InstitutionRight"] = ParagraphStyle(
        "InstitutionRight",
        fontName="Times-Bold",
        fontSize=10,
        leading=13,
        alignment=TA_RIGHT,
    )

    # Course name (left) — italic
    styles["CourseLeft"] = ParagraphStyle(
        "CourseLeft",
        fontName="Times-Italic",
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
    )

    # Completion date (right) — italic
    styles["CourseRight"] = ParagraphStyle(
        "CourseRight",
        fontName="Times-Italic",
        fontSize=10,
        leading=13,
        alignment=TA_RIGHT,
    )

    # Skills & interests — left aligned, 10pt
    styles["Skills"] = ParagraphStyle(
        "Skills",
        fontName="Times-Roman",
        fontSize=10,
        leading=13,
        alignment=TA_LEFT,
        spaceAfter=4,
    )

    return styles
