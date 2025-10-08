import pytest

from voice_agent.utils.email_parser_util import parse_email_from_raw


@pytest.mark.parametrize(
    "raw,expected_subject,expected_body",
    [
        (b"Subject: Hi\n\nTest", "Hi", "Test"),
        (b"Subject: Hello\n\nWorld", "Hello", "World"),
    ],
)
def test_parse_email_basic(raw: bytes, expected_subject: str, expected_body: str) -> None:
    """
    Test that parse_email_from_raw correctly extracts the subject and body from raw email input.

    Args:
        raw (bytes): The raw email input.
        expected_subject (str): The expected subject of the email.
        expected_body (str): The expected body of the email.

    Returns:
        None
    """
    result = parse_email_from_raw(raw)
    assert result["subject"] == expected_subject
    assert result["body"].strip() == expected_body
