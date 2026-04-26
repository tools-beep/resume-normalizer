from unittest.mock import MagicMock, patch

import pytest

from app.schemas.resume import PersonalInfo, ResumeData
from app.services.llm_service import LLMService
from app.utils.exceptions import LLMRetryExhaustedError


def _make_mock_response(resume_data: ResumeData):
    """Create a mock OpenAI response with parsed data."""
    mock_message = MagicMock()
    mock_message.parsed = resume_data
    mock_message.refusal = None

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 100
    mock_usage.completion_tokens = 200
    mock_usage.total_tokens = 300

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    return mock_response


def test_extract_resume_data_success():
    """Successful extraction returns a ResumeData object."""
    expected = ResumeData(
        personal_info=PersonalInfo(full_name="Jane Smith", email="jane@test.com"),
        skills=["Python", "FastAPI"],
    )

    with patch("app.services.llm_service.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_client.beta.chat.completions.parse.return_value = _make_mock_response(expected)

        service = LLMService(api_key="sk-test")
        result = service.extract_resume_data("Jane Smith\nPython developer")

    assert result.personal_info.full_name == "Jane Smith"
    assert "Python" in result.skills


def test_extract_retries_on_missing_name():
    """LLM retries when name is missing from response."""
    bad_data = ResumeData(skills=["Python"])
    good_data = ResumeData(
        personal_info=PersonalInfo(full_name="Jane Smith"),
        skills=["Python"],
    )

    with patch("app.services.llm_service.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_client.beta.chat.completions.parse.side_effect = [
            _make_mock_response(bad_data),
            _make_mock_response(good_data),
        ]

        service = LLMService(api_key="sk-test", max_retries=2)
        result = service.extract_resume_data("Jane Smith\nPython developer")

    assert result.personal_info.full_name == "Jane Smith"
    assert mock_client.beta.chat.completions.parse.call_count == 2


def test_extract_exhausts_retries():
    """Raises LLMRetryExhaustedError when all retries fail semantic validation."""
    bad_data = ResumeData()  # empty — no name, no content

    with patch("app.services.llm_service.OpenAI") as MockOpenAI:
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client
        mock_client.beta.chat.completions.parse.return_value = _make_mock_response(bad_data)

        service = LLMService(api_key="sk-test", max_retries=2)

        with pytest.raises(LLMRetryExhaustedError):
            service.extract_resume_data("unreadable text")

    # 1 initial + 2 retries = 3 calls
    assert mock_client.beta.chat.completions.parse.call_count == 3
