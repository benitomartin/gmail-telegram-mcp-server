import base64
import os

from fastmcp import Context
from google.cloud import texttospeech as tts

from voice_agent.server.gmail_mcp_instance import gmail_mcp


def _init_tts_client() -> tts.TextToSpeechClient:
    # GOOGLE_APPLICATION_CREDENTIALS must be set to a JSON key file path
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not creds_path or not os.path.exists(creds_path):
        raise ValueError(
            "GOOGLE_APPLICATION_CREDENTIALS env var must point to a valid service account JSON file"
        )
    return tts.TextToSpeechClient()


def _synthesize_chunks(text_chunks: list[str], language_code: str, voice_name: str) -> bytes:
    client = _init_tts_client()
    voice_params = tts.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name,
    )
    audio_config = tts.AudioConfig(
        audio_encoding=tts.AudioEncoding.MP3,
        sample_rate_hertz=24000,
    )

    # Concatenate chunks into one synthesis for a single output file (Instagram-friendly MP3)
    text = "".join(text_chunks)
    input_cfg = tts.SynthesisInput(text=text)
    response = client.synthesize_speech(
        request={
            "input": input_cfg,
            "voice": voice_params,
            "audio_config": audio_config,
        }
    )
    return response.audio_content


@gmail_mcp.tool()
async def tts_instagram_audio(
    text: str,
    language_code: str = "en-US",
    voice_name: str = "en-US-Chirp3-HD-Aoede",
    ctx: Context | None = None,
) -> str:
    """Generate audio (MP3) from text using Google Text-to-Speech.

    IMPORTANT: Only use this tool when the user explicitly requests audio output with keywords like:
    - "audio", "audio summary", "with audio", "read it to me", "voice", "spoken"

    When generating audio:
    1. First fetch the emails using appropriate tool
    2. Generate a text summary
    3. Then pass the summary text to this tool

    Args:
            text: Full text to synthesize (will be produced as a single MP3 file)
            language_code: Language code (default: 'en-US')
            voice_name: Voice to use (default: 'en-US-Chirp3-HD-Aoede')

    Returns:
            Base64-encoded MP3 audio string
    """
    if ctx:
        await ctx.info("Starting TTS synthesis for Instagram MP3")
    chunks = [text]
    mp3_bytes = _synthesize_chunks(chunks, language_code, voice_name)
    if ctx:
        await ctx.info("TTS synthesis complete", extra={"bytes": len(mp3_bytes)})
    return base64.b64encode(mp3_bytes).decode("ascii")
