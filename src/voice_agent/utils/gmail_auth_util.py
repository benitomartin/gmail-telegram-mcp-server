import json
import os

import googleapiclient
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from voice_agent.config import settings
from voice_agent.utils.logger_util import get_logger

logger = get_logger(name="GmailService")


def save_token_to_env(token_json: str) -> None:
    """
    Save Gmail OAuth token to .env file.

    Args:
            token_json: The token JSON string to save.

    Returns:
            None
    """
    env_file = ".env"
    existing_lines = []
    if os.path.exists(env_file):
        with open(env_file) as f:
            existing_lines = [
                line
                for line in f.readlines()
                if not line.startswith("GOOGLE__GMAIL_TOKEN=")
            ]
    with open(env_file, "w") as f:
        f.writelines(existing_lines)
        if existing_lines and not existing_lines[-1].endswith("\n"):
            f.write("\n")
        f.write(f"GOOGLE__GMAIL_TOKEN={token_json}\n")
    logger.info("Saved GOOGLE__GMAIL_TOKEN to .env")


def get_gmail_service() -> googleapiclient.discovery.Resource:
    """
    Authenticates using OAuth2. If no valid token is found, initiates the OAuth flow.

    Args:
            None

    Returns:
            Authenticated Gmail API service instance.
    """
    creds: Credentials | None = None  # cspell:ignore creds
    token_json = settings.google.gmail_token
    if token_json:
        try:
            creds = Credentials.from_authorized_user_info(
                json.loads(token_json),
                settings.google.scopes
            )
        except Exception as e:
            logger.error(f"Error loading token: {e}")
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # creds is guaranteed to be non-None here due to the condition above
        save_token_to_env(creds.to_json())  # type: ignore[union-attr]
    if not creds or not creds.valid:
        client_id = settings.google.client_id
        client_secret = settings.google.client_secret
        redirect_uris = settings.google.redirect_uris
        auth_uri = settings.google.auth_uri
        token_uri = settings.google.token_uri

        if not client_id or not client_secret:
            raise ValueError("Missing GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET in .env")
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": redirect_uris,
                "auth_uri": auth_uri,
                "token_uri": token_uri,
            }
        }
        flow = InstalledAppFlow.from_client_config(
            client_config,
            scopes=settings.google.scopes
        )
        # Request offline access to get a refresh token
        creds = flow.run_local_server(port=0)
        # creds is guaranteed to be non-None after OAuth flow
        save_token_to_env(creds.to_json())  # type: ignore[union-attr]
        logger.info("Authentication successful. Token saved.")
    return build("gmail", "v1", credentials=creds)
