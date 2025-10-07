"""Email parsing and text processing utilities."""

import unicodedata
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime

from bs4 import BeautifulSoup

from voice_agent.utils.logger_util import get_logger

logger = get_logger(name="GmailUtils")


def parse_email_from_raw(raw_email_bytes: bytes) -> dict:
    """Parse raw RFC 2822 email and extract headers + body using Python's email library."""
    try:
        # Parse email using modern policy (handles Unicode properly)
        msg = BytesParser(policy=policy.default).parsebytes(raw_email_bytes)

        # Extract headers
        subject = msg.get("Subject", "No Subject")
        sender = msg.get("From", "Unknown")
        date_raw = msg.get("Date", None)

        # Format date to remove timestamp and timezone: "Fri, 03 Oct 2025"
        date_formatted = None
        if date_raw:
            try:
                dt = parsedate_to_datetime(date_raw)
                date_formatted = dt.strftime("%a, %d %b %Y")
            except Exception:
                date_formatted = date_raw  # Fallback to raw if parsing fails

        # Try to find plain text body first, fallback to HTML
        text_body = None
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain" and text_body is None:
                    text_body = part.get_content()
                    break
        else:
            if msg.get_content_type() == "text/plain":
                text_body = msg.get_content()

        # If no plain text found, try HTML
        if not text_body and msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    html_body = part.get_content()
                    text_body = _html_to_text(html_body)
                    break
        elif not text_body and msg.get_content_type() == "text/html":
            html_body = msg.get_content()
            text_body = _html_to_text(html_body)

        body = _clean_text(text_body) if text_body else ""

        return {"subject": subject, "from": sender, "date": date_formatted, "body": body}
    except Exception as e:
        logger.error(f"Error parsing email with email library: {e}")
        return {"subject": "Error", "from": "Unknown", "date": None, "body": ""}


def _clean_text(text: str) -> str:
    """Clean text by removing invisible characters and normalizing whitespace."""
    # Remove invisible Unicode characters
    # Cf = Format control (zero-width spaces, soft hyphens, etc.)
    # Mn = Mark, Nonspacing (combining characters like U+034F)
    # Cc = Control characters (except newline/tab which we handle separately)
    cleaned_chars = []
    for char in text:
        category = unicodedata.category(char)
        # Keep visible characters and basic whitespace
        if category not in ("Cf", "Mn") and (category != "Cc" or char in "\n\t"):
            cleaned_chars.append(char)
    text = "".join(cleaned_chars)

    # Replace various types of spaces with regular space
    text = text.replace("\u00a0", " ")  # Non-breaking space
    text = text.replace("\u202f", " ")  # Narrow no-break space
    text = text.replace("\u2007", " ")  # Figure space

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive whitespace but preserve paragraph breaks
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]

    return "\n".join(cleaned_lines)


def _html_to_text(html: str) -> str:
    """Convert HTML to clean plain text using BeautifulSoup."""
    try:
        soup = BeautifulSoup(html, "lxml")
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        # Get text with line breaks
        text = soup.get_text(separator="\n", strip=True)
        return _clean_text(text)
    except Exception:
        # Fallback to basic cleaning if BeautifulSoup fails
        return _clean_text(html)
