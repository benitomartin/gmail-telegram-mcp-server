import json
import os

import googleapiclient
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from voice_agent.config import SCOPES
from voice_agent.utils.logger_util import get_logger

load_dotenv()

logger = get_logger(name="GmailService")


def save_token_to_env(token_json: str) -> None:
    """Save Gmail OAuth token to .env file."""
    env_file = ".env"
    existing_lines = []
    if os.path.exists(env_file):
        with open(env_file) as f:
            existing_lines = [line for line in f.readlines() if not line.startswith("GMAIL_TOKEN=")]
    with open(env_file, "w") as f:
        f.writelines(existing_lines)
        if existing_lines and not existing_lines[-1].endswith("\n"):
            f.write("\n")
        f.write(f"GMAIL_TOKEN='{token_json}'\n")
    logger.info("Saved GMAIL_TOKEN to .env")


def get_gmail_service() -> googleapiclient.discovery.Resource:
    """
    Authenticates using OAuth2. If no valid token is found, initiates the OAuth flow.

    Args:
            None

    Returns:
            Authenticated Gmail API service instance.
    """
    creds: Credentials | None = None  # cspell:ignore creds
    token_json = os.getenv("GMAIL_TOKEN")
    if token_json:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
        except Exception as e:
            logger.error(f"Error loading token: {e}")
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # creds is guaranteed to be non-None here due to the condition above
        save_token_to_env(creds.to_json())  # type: ignore[union-attr]
    if not creds or not creds.valid:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError("Missing GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET in .env")
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": ["http://localhost"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
        creds = flow.run_local_server(port=0)
        # creds is guaranteed to be non-None after OAuth flow
        save_token_to_env(creds.to_json())  # type: ignore[union-attr]
        logger.info("Authentication successful. Token saved.")
    return build("gmail", "v1", credentials=creds)
