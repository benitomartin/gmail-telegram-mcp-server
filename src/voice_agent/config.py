from typing import ClassVar

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramBotConfig(BaseModel):
    bot_token: str = Field(default="", description="Telegram bot token")


class OpenAIConfig(BaseModel):
    api_key: str = Field(default="", description="OpenAI API key")
    model: str = Field(default="gpt-4o-mini", description="OpenAI model")


class GoogleConfig(BaseModel):
    client_id: str = Field(default="", description="Google client ID")
    client_secret: str = Field(default="", description="Google client secret")
    application_credentials: str = Field(
        default="", description="Path to Google application credentials JSON file"
    )
    scopes: list[str] = Field(
        default=["https://www.googleapis.com/auth/gmail.readonly"],
        description="OAuth2 scopes for Gmail API",
    )
    gmail_token: str | None = Field(default=None, description="Gmail OAuth token")
    redirect_uris: list[str] = Field(
        default=["http://localhost"], description="OAuth2 redirect URIs"
    )
    auth_uri: str = Field(
        default="https://accounts.google.com/o/oauth2/auth",
        description="OAuth2 authorization endpoint",
    )
    token_uri: str = Field(
        default="https://oauth2.googleapis.com/token", description="OAuth2 token endpoint"
    )


class ToolConfig(BaseModel):
    get_emails_tool: str = Field(
        default="get_emails",
        description=(
            "Fetch emails from Gmail for a specified number of days. "
            "Returns JSON array of emails with id, from, subject, date, and body fields."
        ),
    )
    tts_instagram_audio_tool: str = Field(
        default="tts_instagram_audio",
        description="Convert text to speech for Instagram audio messages.",
    )


class PromptConfig(BaseModel):
    assistant_prompt: str = Field(
        default="email_assistant_system_prompt",
        description="System prompt for the email assistant agent with automatic tool selection.",
    )
    summary_prompt: str = Field(
        default="email_summary_format_prompt",
        description="Prompt for formatting email summaries with a specific timespan.",
    )
    summary_audio_prompt: str = Field(
        default="email_summary_audio_format_prompt",
        description="Prompt for formatting email summaries specifically for audio/speech output.",
    )


class Settings(BaseSettings):
    telegram: TelegramBotConfig = Field(default_factory=TelegramBotConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    google: GoogleConfig = Field(default_factory=GoogleConfig)
    tools: ToolConfig = Field(default_factory=ToolConfig)
    prompts: PromptConfig = Field(default_factory=PromptConfig)

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=[".env"],
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
        case_sensitive=False,
        frozen=True,
    )


settings: Settings = Settings()
