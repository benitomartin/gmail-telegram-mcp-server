import base64
import io

from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from voice_agent.client.agent import VoiceAgentClient
from voice_agent.config import OPENAI_API_KEY, OPENAI_MODEL, TELEGRAM_BOT_TOKEN
from voice_agent.utils.logger_util import get_logger
from voice_agent.utils.openai_utils import get_openai_completion


class EmailSummaryBot:
    def __init__(self, telegram_token, openai_api_key, openai_model) -> None:
        self.voice_agent_client = VoiceAgentClient(
            openai_client=OpenAI(api_key=openai_api_key) if openai_api_key else None,
            model=openai_model,
        )
        self.telegram_token = telegram_token
        self.logger = get_logger("bot")

    def _assert_openai_configured(self):
        if self.voice_agent_client.openai_client is None:
            raise RuntimeError("OpenAI is not configured. Set OPENAI_API_KEY.")

    async def _build_summary_prompt(self, timespan: str) -> str:
        return await self.voice_agent_client.get_summary_prompt(timespan)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "👋 Hello! I'm your Email Summary Bot!\n\n"
            "Commands:\n"
            "/start - Show this message\n"
            "/summary <request> - Smart agent; decides timeframe & format (text/audio/both)\n"
            "/summary_today - Quick text summary of today's emails\n"
            "/audio_today - Quick audio summary of today's emails\n\n"
            "Examples:\n"
            "/summary summarize last 2 days with audio\n"
            "/summary summarize emails of the last week\n"
        )

    async def summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if context.args:
            user_text = " ".join(context.args).strip()
        else:
            await update.message.reply_text(
                "What would you like me to do? (e.g., 'summarize today' or 'summarize last 2 days with audio')"
            )
            return

        if not (hasattr(context, "_already_notified") and context._already_notified):
            await update.message.reply_text("🧠 Running agent with your instruction... ⏳")

        try:
            self._assert_openai_configured()
            self.logger.info(f"Running agentic query: {user_text}")
            answer, audio_b64 = await self.voice_agent_client.run_agentic_query(user_text)
            self.logger.info(
                f"Agent response: {len(answer) if answer else 0} chars, audio: {bool(audio_b64)}"
            )

            if answer and answer.strip():
                max_length = 4000
                if len(answer) <= max_length:
                    await update.message.reply_text(answer)
                else:
                    for i in range(0, len(answer), max_length):
                        chunk = answer[i : i + max_length]
                        await update.message.reply_text(chunk)
            else:
                await update.message.reply_text("(No response from agent)")

            if audio_b64:
                try:
                    self.logger.info("Sending audio to user")
                    mp3_bytes = base64.b64decode(audio_b64)
                    bio = io.BytesIO(mp3_bytes)
                    bio.name = "summary.mp3"
                    await update.message.reply_audio(
                        audio=bio, filename="summary.mp3", caption="🎧 Audio summary"
                    )
                    self.logger.info("Audio sent successfully")
                except Exception as audio_error:
                    self.logger.error(f"Error sending audio: {str(audio_error)}")
                    await update.message.reply_text(
                        f"⚠️ Audio generation completed but failed to send: {str(audio_error)}"
                    )

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            self.logger.error(f"Error in summary: {str(e)}\n{error_details}")
            error_msg = f"❌ Error running agent: {str(e)}"
            if len(error_msg) < 4000:
                await update.message.reply_text(error_msg)
            else:
                await update.message.reply_text(f"❌ Error: {str(e)[:500]}...")
            if len(error_details) < 4000:
                await update.message.reply_text(f"Details:\n{error_details}")
            else:
                await update.message.reply_text(f"Details:\n{error_details[:3500]}...")

    async def summary_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("📧 Summarizing today's emails... ⏳")
        try:
            self._assert_openai_configured()
            self.logger.info("Calling MCP tool: get_emails with days=0 (today)")
            emails_json = await self.voice_agent_client.call_mcp_tool("get_emails", {"days": 0})
            self.logger.info(f"Received {len(emails_json)} chars of email JSON")

            self.logger.info("Building summary prompt")
            system_prompt = await self._build_summary_prompt("today")

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": emails_json},
            ]

            self.logger.info("Calling OpenAI for summary")
            completion = get_openai_completion(
                openai_client=self.voice_agent_client.openai_client,
                model=self.voice_agent_client.model,
                messages=messages,
                temperature=0.2,
            )

            summary = completion.choices[0].message.content
            self.logger.info(f"Generated summary: {len(summary)} chars")
            await update.message.reply_text(summary)
        except Exception as e:
            import traceback

            error_trace = traceback.format_exc()
            self.logger.error(f"Error in summary_today: {str(e)}\n{error_trace}")
            await update.message.reply_text(f"❌ Error summarizing today: {str(e)}")

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            self.logger.error(f"Error in summary: {str(e)}\n{error_details}")
            error_msg = f"❌ Error running agent: {str(e)}"
            if len(error_msg) < 4000:
                await update.message.reply_text(error_msg)
            else:
                await update.message.reply_text(f"❌ Error: {str(e)[:500]}...")
            if len(error_details) < 4000:
                await update.message.reply_text(f"Details:\n{error_details}")
            else:
                await update.message.reply_text(f"Details:\n{error_details[:3500]}...")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_message = (update.message.text or "").lower()
        user_name = update.message.from_user.first_name
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
            await update.message.reply_text(f"Okay {user_name}, processing your request... ⏳")
            context.args = user_message.split()
            context._already_notified = True
            await self.summary(update, context)
        else:
            await self.start(update, context)

    async def audio_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("🎧 Creating audio summary for today... ⏳")
        try:
            self._assert_openai_configured()
            self.logger.info("Calling MCP tool: get_emails with days=0 (today)")
            emails_json = await self.voice_agent_client.call_mcp_tool("get_emails", {"days": 0})
            self.logger.info(f"Received {len(emails_json)} chars of email JSON")

            self.logger.info("Building AUDIO-FRIENDLY summary prompt")
            system_prompt = await self.voice_agent_client.get_summary_prompt(
                "today", for_audio=True
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": emails_json},
            ]

            self.logger.info("Calling OpenAI for conversational audio summary")
            completion = get_openai_completion(
                openai_client=self.voice_agent_client.openai_client,
                model=self.voice_agent_client.model,
                messages=messages,
                temperature=0.2,
            )

            summary_text = completion.choices[0].message.content
            self.logger.info(f"Generated conversational summary: {len(summary_text)} chars")

            self.logger.info("Calling MCP tool: tts_instagram_audio")
            b64 = await self.voice_agent_client.call_mcp_tool(
                "tts_instagram_audio", {"text": summary_text}
            )
            self.logger.info(f"Generated audio: {len(b64)} chars base64")

            mp3_bytes = base64.b64decode(b64)
            bio = io.BytesIO(mp3_bytes)
            bio.name = "summary_today.mp3"
            await update.message.reply_audio(
                audio=bio, filename="summary_today.mp3", caption="Audio summary (today)"
            )
            self.logger.info("Audio sent successfully")
        except Exception as e:
            import traceback

            error_trace = traceback.format_exc()
            self.logger.error(f"Error in audio_today: {str(e)}\n{error_trace}")
            await update.message.reply_text(f"❌ Error generating audio summary: {str(e)}")

    def run(self) -> None:
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
    bot = EmailSummaryBot(TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, OPENAI_MODEL)
    bot.run()
