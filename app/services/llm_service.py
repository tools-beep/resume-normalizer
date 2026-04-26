from __future__ import annotations

import base64
import time

from openai import OpenAI

from app.schemas.resume import ResumeData
from app.utils.exceptions import LLMExtractionError, LLMRetryExhaustedError
from app.utils.logging import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a resume parser. Extract structured data from the provided resume text.

Fields to extract:
- personal_info: full_name, email, city, country, phone, linkedin_url
- summary: a short professional introduction (1-3 sentences)
- job_title: the candidate's primary professional title (e.g. "Software Engineering", "Marketing", "Finance"). This is used for the section heading "{job_title} EXPERIENCE".
- experience: for each role extract company_name, brief_company_description (a short phrase describing the company), company_location, candidate_position, tenure_date_range (e.g. "Jan 2020 - Present"), responsibilities (list), achievements (list)
- education: institution_name, institution_location, course_name (degree and field, e.g. "B.S. Computer Science"), completion_date
- skills: individual skill names (not categories)
- interests: personal or professional interests

Rules:
- Extract only information explicitly present in the text.
- Do NOT fabricate or infer missing information — use null for missing fields.
- For tenure_date_range, keep the format as found in the text (e.g. "Jan 2020 - Present", "2018 - 2022").
- For brief_company_description, write a very short phrase (5-10 words) if the company is well-known or if context is available, otherwise use null.
- Separate responsibilities and achievements into distinct lists where possible. If unclear, put all bullet points under responsibilities.
- If the resume text is garbled or unreadable, still extract whatever is clearly identifiable."""

USER_PROMPT_TEMPLATE = """Extract structured resume data from the following text:

---
{text}
---"""

RETRY_PROMPT_TEMPLATE = """The previous extraction was incomplete. The following issues were found:
{issues}

Please re-extract the resume data more carefully from this text:

---
{text}
---"""


class LLMService:
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4.1-mini",
        max_retries: int = 2,
        temperature: float = 0.2,
        timeout: float = 120.0,
    ):
        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.max_retries = max_retries
        self.temperature = temperature

    def extract_resume_data(self, raw_text: str) -> ResumeData:
        """Extract structured resume data from raw text using OpenAI Structured Outputs."""
        start = time.monotonic()
        user_prompt = USER_PROMPT_TEMPLATE.format(text=raw_text)

        resume_data = self._call_llm(user_prompt)

        # Semantic validation with retry
        issues = self._validate_semantics(resume_data)
        attempt = 0
        while issues and attempt < self.max_retries:
            attempt += 1
            logger.warning(
                "Semantic validation failed, retrying",
                extra={"attempt": attempt, "issues": issues},
            )
            retry_prompt = RETRY_PROMPT_TEMPLATE.format(
                issues="\n".join(f"- {i}" for i in issues),
                text=raw_text,
            )
            resume_data = self._call_llm(retry_prompt)
            issues = self._validate_semantics(resume_data)

        if issues:
            raise LLMRetryExhaustedError(
                f"LLM extraction failed after {self.max_retries} retries. "
                f"Remaining issues: {issues}"
            )

        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info(
            "LLM extraction complete",
            extra={"elapsed_ms": round(elapsed_ms, 1), "retries_used": attempt},
        )
        return resume_data

    def extract_resume_data_from_images(self, images: list[bytes], mime_type: str = "image/png") -> ResumeData:
        """Extract structured resume data from images using vision."""
        start = time.monotonic()

        b64_images = [base64.b64encode(img).decode("utf-8") for img in images]
        content: list[dict] = [{"type": "text", "text": "Extract structured resume data from this resume image."}]
        for b64 in b64_images:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{b64}"},
            })

        resume_data = self._call_llm_vision(content)

        # Semantic validation with retry
        issues = self._validate_semantics(resume_data)
        attempt = 0
        while issues and attempt < self.max_retries:
            attempt += 1
            logger.warning(
                "Vision semantic validation failed, retrying",
                extra={"attempt": attempt, "issues": issues},
            )
            retry_content: list[dict] = [{
                "type": "text",
                "text": (
                    "The previous extraction was incomplete. Issues:\n"
                    + "\n".join(f"- {i}" for i in issues)
                    + "\n\nPlease re-extract the resume data more carefully from this image."
                ),
            }]
            for b64 in b64_images:
                retry_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{b64}"},
                })
            resume_data = self._call_llm_vision(retry_content)
            issues = self._validate_semantics(resume_data)

        if issues:
            raise LLMRetryExhaustedError(
                f"Vision extraction failed after {self.max_retries} retries. "
                f"Remaining issues: {issues}"
            )

        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info(
            "Vision extraction complete",
            extra={"elapsed_ms": round(elapsed_ms, 1), "retries_used": attempt, "image_count": len(images)},
        )
        return resume_data

    def _call_llm_vision(self, content: list[dict]) -> ResumeData:
        """Make a single LLM call with vision input and structured output parsing."""
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
                response_format=ResumeData,
            )

            parsed = response.choices[0].message.parsed
            if parsed is None:
                refusal = response.choices[0].message.refusal
                raise LLMExtractionError(f"LLM refused to parse resume image: {refusal}")

            usage = response.usage
            if usage:
                logger.info(
                    "Vision LLM token usage",
                    extra={
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                    },
                )

            return parsed

        except LLMExtractionError:
            raise
        except Exception as e:
            raise LLMExtractionError(f"OpenAI Vision API error: {e}") from e

    def _call_llm(self, user_prompt: str) -> ResumeData:
        """Make a single LLM call with structured output parsing."""
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=ResumeData,
            )

            parsed = response.choices[0].message.parsed
            if parsed is None:
                refusal = response.choices[0].message.refusal
                raise LLMExtractionError(f"LLM refused to parse resume: {refusal}")

            usage = response.usage
            if usage:
                logger.info(
                    "LLM token usage",
                    extra={
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                    },
                )

            return parsed

        except LLMExtractionError:
            raise
        except Exception as e:
            raise LLMExtractionError(f"OpenAI API error: {e}") from e

    def _validate_semantics(self, data: ResumeData) -> list[str]:
        """Check that the extracted data is semantically meaningful."""
        issues: list[str] = []

        if data.personal_info is None or not data.personal_info.full_name:
            issues.append("Missing personal_info.full_name — every resume should have a name")

        has_content = bool(data.experience or data.education or data.skills)
        if not has_content:
            issues.append(
                "No experience, education, or skills found — "
                "at least one section should be present"
            )

        return issues
