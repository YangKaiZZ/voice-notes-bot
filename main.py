"""Telegram voice-note logger.

Voice note -> Groq Whisper transcript -> Groq chat summary -> row in a Google Sheet.
"""

import os
import tempfile
from datetime import datetime

import gspread
import requests
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
SHEET_ID = os.environ["SHEET_ID"]

TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
WHISPER_MODEL = "whisper-large-v3"
CHAT_MODEL = "openai/gpt-oss-120b"

GOOGLE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheet():
    """Open the first worksheet of the target spreadsheet."""
    creds = Credentials.from_service_account_file("google-creds.json", scopes=GOOGLE_SCOPES)
    return gspread.authorize(creds).open_by_key(SHEET_ID).sheet1


def transcribe(audio_path):
    """Send the audio file to Groq Whisper and return the transcript text."""
    with open(audio_path, "rb") as audio:
        response = requests.post(
            TRANSCRIBE_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            files={"file": (os.path.basename(audio_path), audio, "audio/ogg")},
            data={"model": WHISPER_MODEL},
            timeout=120,
        )
    response.raise_for_status()
    return response.json()["text"].strip()


def summarize(transcript):
    """Ask Groq for a 1-2 sentence summary of the transcript."""
    response = requests.post(
        CHAT_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": CHAT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Summarize the user's voice note in 1-2 short sentences. "
                        "Reply with the summary only, no preamble."
                    ),
                },
                {"role": "user", "content": transcript},
            ],
            "temperature": 0.3,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice or update.message.audio
    print(f"\n[1] Voice note received from {update.effective_user.first_name} "
          f"({voice.duration}s)")

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, f"{voice.file_id}.ogg")
        telegram_file = await context.bot.get_file(voice.file_id)
        await telegram_file.download_to_drive(audio_path)
        print(f"[2] Downloaded to {audio_path} ({os.path.getsize(audio_path)} bytes)")

        try:
            transcript = transcribe(audio_path)
            print(f"[3] Transcript: {transcript}")

            summary = summarize(transcript)
            print(f"[4] Summary: {summary}")

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            get_sheet().append_row([timestamp, transcript, summary])
            print(f"[5] Appended row to sheet {SHEET_ID}")
        except Exception as error:
            print(f"[!] Failed: {error!r}")
            await update.message.reply_text(f"⚠️ Something broke: {error}")
            return

    await update.message.reply_text(f"✅ Logged: {summary}")
    print("[6] Replied to user\n")


def main():
    print("Starting bot...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    print("Bot is polling. Send it a voice note.")
    app.run_polling()


if __name__ == "__main__":
    main()
