import base64
import io

from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from voice_agent.client.agent import VoiceAgentClient
from voice_agent.config import settings
from voice_agent.utils.logger_util import get_logger
from voice_agent.utils.openai_utils import get_openai_completion


class EmailSummaryBot:
    def __init__(self, telegram_token: str, openai_api_key: str, openai_model: str) -> None:
        self.voice_agent_client = VoiceAgentClient(
            openai_client=OpenAI(api_key=openai_api_key) if openai_api_key else None,
            model=openai_model,
        )
        self.telegram_token = telegram_token
        self.logger = get_logger("EmailSummaryBot")

    def _assert_openai_configured(self) -> None:
        if self.voice_agent_client.openai_client is None:
            raise RuntimeError("OpenAI is not configured. Set OPENAI_API_KEY.")

    async def _build_summary_prompt(self, timespan: str) -> str:
        return await self.voice_agent_client.get_summary_prompt(timespan)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Send a message when the command /start is issued.

        Args:
            update: Incoming update from Telegram.
            context: Context for the command handler.

        Returns:
            None
        """
        if update.message:
            await update.message.reply_text(

                "👋 Hello! I'm your Email Summary Bot!\n"
                "Commands:\n"
                "- /start - Show this message\n"
                "- /summary - Smart agent; decides timeframe & format (text/audio/both)\n"
                "- /summary_today - Quick text summary of today's emails\n"
                "- /audio_today - Quick audio summary of today's emails\n"
            )
            await update.message.reply_text(
                "Examples:\n"
                "- /summary summarize last 2 days with audio\n"
                "- /summary summarize emails of the last week\n"
            )
        else:
            self.logger.warning("No message found in update; cannot reply.")

    async def summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle the /summary command to run the agent with user instructions.

        Args:
            update: Incoming update from Telegram.
            context: Context for the command handler.

        Return:
            None

        """
        if context.args:
            user_text = " ".join(context.args).strip()
        else:
            if update.message:
                await update.message.reply_text(
                    """
                        What would you like me to do?
                        (e.g., 'summarize today' or
                        'summarize last 2 days with audio')
                    """
                )
            else:
                self.logger.warning("No message found in update; cannot reply.")
            return

        if not (context.chat_data and context.chat_data.get("already_notified", False)):
            if update.message:
                await update.message.reply_text("🧠 Running agent with your instruction... ⏳")
            else:
                self.logger.warning("No message found in update; cannot reply.")

        try:
            self._assert_openai_configured()
            self.logger.info(f"Running agentic query: {user_text}")
            answer, audio_b64 = await self.voice_agent_client.run_agentic_query(user_text)
            self.logger.info(
                f"Agent response: {len(answer) if answer else 0} chars, audio: {bool(audio_b64)}"
            )

            if answer and answer.strip():
                max_length = 4000
                if update.message:
                    if len(answer) <= max_length:
                        await update.message.reply_text(answer)
                    else:
                        for i in range(0, len(answer), max_length):
                            chunk = answer[i : i + max_length]
                            await update.message.reply_text(chunk)
                else:
                    self.logger.warning("No message found in update; cannot reply.")
            else:
                if update.message:
                    await update.message.reply_text("(No response from agent)")
                else:
                    self.logger.warning("No message found in update; cannot reply.")

            if audio_b64:
                try:
                    self.logger.info("Sending audio to user")
                    mp3_bytes = base64.b64decode(audio_b64)
                    bio = io.BytesIO(mp3_bytes)
                    bio.name = "summary.mp3"
                    if update.message:
                        await update.message.reply_audio(
                            audio=bio, filename="summary.mp3", caption="🎧 Audio summary"
                        )
                        self.logger.info("Audio sent successfully")
                    else:
                        self.logger.warning("No message found in update; cannot send audio.")
                except Exception as audio_error:
                    self.logger.error(f"Error sending audio: {str(audio_error)}")
                    if update.message:
                        await update.message.reply_text(
                            f"⚠️ Audio generation completed but failed to send: {str(audio_error)}"
                        )
                    else:
                        self.logger.warning("No message found in update; cannot reply.")

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            self.logger.error(f"Error in summary: {str(e)}\n{error_details}")
            error_msg = f"❌ Error running agent: {str(e)}"
            if update.message:
                if len(error_msg) < 4000:
                    await update.message.reply_text(error_msg)
                else:
                    await update.message.reply_text(f"❌ Error: {str(e)[:500]}...")
                if len(error_details) < 4000:
                    await update.message.reply_text(f"Details:\n{error_details}")
                else:
                    await update.message.reply_text(f"Details:\n{error_details[:3500]}...")
            else:
                self.logger.warning("No message found in update; cannot reply.")

    async def summary_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
         Summarize today's emails in text format.

         Args:
            update: Incoming update from Telegram.
            context: Context for the command handler.

         Return:
            None
         """

        if update.message:
            await update.message.reply_text("📧 Summarizing today's emails... ⏳")
        else:
            self.logger.warning("No message found in update; cannot reply.")
        try:
            self._assert_openai_configured()
            # Open a single MCP session for all calls
            async with self.voice_agent_client.mcp_host_initialized_session() as session:
                self.logger.info("Calling MCP tool: get_emails with days=0 (today)")
                emails_result = await session.call_tool("get_emails", {"days": 0})
                emails_json = (
                    emails_result.content[0].text
                    if hasattr(emails_result, "content")
                    else str(emails_result)
                )
                self.logger.info(f"Received {len(emails_json)} chars of email JSON")

                self.logger.info("Building summary prompt")
                prompt_result = await session.get_prompt(
                    "email_summary_format_prompt",
                    arguments={"timespan": "today"},
                )
                system_prompt = (
                    prompt_result.messages[0].content.text
                    if prompt_result.messages
                    else "Summarize today's emails."
                )

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": emails_json},
                ]

                self.logger.info("Calling OpenAI for summary")
                completion = get_openai_completion(
                    openai_client=self.voice_agent_client.openai_client,
                    model=(
                        self.voice_agent_client.model
                        if self.voice_agent_client.model is not None
                        else "gpt-4o-mini"
                    ),
                    messages=messages,
                    temperature=0.2,
                )

                summary = completion.choices[0].message.content # type: ignore
                self.logger.info(f"Generated summary: {len(summary)} chars")
                if update.message:
                    await update.message.reply_text(summary)
                else:
                    self.logger.warning("No message found in update; cannot reply.")
        except Exception as e:
            import traceback

            error_trace = traceback.format_exc()
            self.logger.error(f"Error in summary_today: {str(e)}\n{error_trace}")
            if update.message:
                await update.message.reply_text(f"❌ Error summarizing today: {str(e)}")
            else:
                self.logger.warning("No message found in update; cannot reply.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle incoming messages from users.

        Args:
            update: Incoming update from Telegram.
            context: Context for the command handler.

        Returns:
            None
        """
        user_message = (update.message.text or "").lower() if update.message else ""
        user_name = (
            update.message.from_user.first_name
            if update.message and update.message.from_user
            else "User"
        )
        agent_keywords = [
            "summary",
            "summarize",
            "audio",
            "email",
            "today",
            "yesterday",
            "last",
            "recent",
            "what",
            "show",
            "get",
            "fetch",
        ]
        should_use_agent = any(keyword in user_message for keyword in agent_keywords)
        if should_use_agent:
            if update.message:
                await update.message.reply_text(f"Okay {user_name}, processing your request... ⏳")
            else:
                self.logger.warning("No message found in update; cannot reply.")
            context.args = user_message.split()
            if context.chat_data is None:
                context.chat_data = {}
            context.chat_data["already_notified"] = True
            await self.summary(update, context)
        else:
            await self.start(update, context)

    async def audio_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle audio summary requests for today.

        Args:
            update: Incoming update from Telegram.
            context: Context for the command handler.

        Returns:
            None
        """
        if update.message:
            await update.message.reply_text("🎧 Creating audio summary for today... ⏳")
        else:
            self.logger.warning("No message found in update; cannot reply.")
        try:
            self._assert_openai_configured()
            # Open a single MCP session for all calls
            async with self.voice_agent_client.mcp_host_initialized_session() as session:
                self.logger.info("Calling MCP tool: get_emails with days=0 (today)")
                emails_result = await session.call_tool("get_emails", {"days": 0})
                emails_json = (
                    emails_result.content[0].text
                    if hasattr(emails_result, "content")
                    else str(emails_result)
                )
                self.logger.info(f"Received {len(emails_json)} chars of email JSON")

                self.logger.info("Building AUDIO-FRIENDLY summary prompt")
                prompt_result = await session.get_prompt(
                    "email_summary_audio_format_prompt",
                    arguments={"timespan": "today"},
                )
                system_prompt = (
                    prompt_result.messages[0].content.text
                    if prompt_result.messages
                    else "Summarize today's emails for audio."
                )

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": emails_json},
                ]

                self.logger.info("Calling OpenAI for conversational audio summary")
                completion = get_openai_completion(
                    openai_client=self.voice_agent_client.openai_client,
                    model=(
                        self.voice_agent_client.model
                        if self.voice_agent_client.model is not None
                        else "gpt-4o-mini"
                    ),
                    messages=messages,
                    temperature=0.2,
                )

                summary_text = completion.choices[0].message.content # type: ignore
                self.logger.info(f"Generated conversational summary: {len(summary_text)} chars")

                self.logger.info("Calling MCP tool: tts_instagram_audio")
                audio_result = await session.call_tool(
                    "tts_instagram_audio", {"text": summary_text}
                )
                b64 = (
                    audio_result.content[0].text
                    if hasattr(audio_result, "content")
                    else str(audio_result)
                )
                self.logger.info(f"Generated audio: {len(b64)} chars base64")

                mp3_bytes = base64.b64decode(b64)
                bio = io.BytesIO(mp3_bytes)
                bio.name = "summary_today.mp3"
                if update.message:
                    await update.message.reply_audio(
                        audio=bio, filename="summary_today.mp3", caption="Audio summary (today)"
                    )
                else:
                    self.logger.warning("No message found in update; cannot send audio.")
                self.logger.info("Audio sent successfully")
        except Exception as e:
            import traceback

            error_trace = traceback.format_exc()
            self.logger.error(f"Error in audio_today: {str(e)}\n{error_trace}")
            if update.message:
                await update.message.reply_text(f"❌ Error generating audio summary: {str(e)}")
            else:
                self.logger.warning("No message found in update; cannot reply.")

    def run(self) -> None:
        """
        Start the Telegram bot.

        Args:
            None

        Returns:
            None
        """
        if not self.telegram_token:
            raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")
        app = Application.builder().token(self.telegram_token).build()
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("summary", self.summary))
        app.add_handler(CommandHandler("summary_today", self.summary_today))
        app.add_handler(CommandHandler("audio_today", self.audio_today))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.run_polling(allowed_updates=Update.ALL_TYPES)


# Entrypoint
def run_bot() -> None:
    """
    Run the Telegram bot.

    Args:
        None

    Returns:
        None
    """
    telegram_token = settings.telegram.bot_token
    openai_api_key = settings.openai.api_key
    openai_model = settings.openai.model

    bot = EmailSummaryBot(telegram_token, openai_api_key, openai_model)
    bot.run()
