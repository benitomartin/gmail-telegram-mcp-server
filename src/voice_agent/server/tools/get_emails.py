import base64
import json
from datetime import datetime

from fastmcp import Context

from voice_agent.utils.email_parser_util import parse_email_from_raw
from voice_agent.utils.gmail_auth_util import get_gmail_service


async def get_emails(days: int = 1, max_results: int = 50, ctx: Context | None = None) -> str:
    """Fetch emails from the last N days with full body content.

    This is the main tool for fetching emails.
    The LLM should decide how many days based on user request:
    - "today" → days=0 (or days=1)
    - "yesterday" → days=1
    - "last 2 days" → days=2
    - "last week" → days=7
    - "last 3 weeks" → days=21
    - "last month" → days=30

    Args:
            days: Number of days to look back (0 for today only, 1+ for past days). Default: 1
            max_results: Maximum number of emails to fetch (1-100). Default: 50

    Returns:
            JSON array of emails with id, from, subject, date, and body fields
    """
    if ctx:
        await ctx.info(
            f"Fetching emails from last {days} day(s)",
            extra={"days": days, "max_results": max_results},
        )

    service = get_gmail_service()

    # Build query based on days
    if days == 0:
        # Today only
        today = datetime.now().strftime("%Y/%m/%d")
        query = f"after:{today}"
    else:
        # Last N days
        query = f"newer_than:{days}d"

    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max(1, min(max_results, 100)))
        .execute()
    )

    messages = results.get("messages", [])
    if ctx:
        await ctx.debug("Gmail list() returned messages", extra={"count": len(messages)})

    emails: list[dict] = []
    if not messages:
        if ctx:
            await ctx.info("No emails found for specified timeframe")
        return json.dumps(emails, ensure_ascii=False)

    for msg in messages:
        # Get raw email format - single API call gets everything
        raw_msg = service.users().messages().get(userId="me", id=msg["id"], format="raw").execute()
        raw_bytes = base64.urlsafe_b64decode(raw_msg["raw"])

        # Parse email to extract headers and body
        email_data = parse_email_from_raw(raw_bytes)
        emails.append(
            {
                "id": msg["id"],
                "from": email_data["from"],
                "subject": email_data["subject"],
                "date": email_data["date"],
                "body": email_data["body"],
            }
        )

    if ctx:
        await ctx.info(f"Prepared full JSON for {len(emails)} emails", extra={"count": len(emails)})
    return json.dumps(emails, ensure_ascii=False)
