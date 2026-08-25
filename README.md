# Voice Notes Bot

A Telegram bot that turns voice notes into a searchable Google Sheets log, with AI transcription and summaries.

## How it works

1. You send a voice note to the bot on Telegram
2. The bot downloads the audio file
3. **Groq Whisper** (`whisper-large-v3`) transcribes it
4. **Groq chat** (`openai/gpt-oss-120b`) condenses the transcript into 1–2 sentences
5. A row is appended to your Google Sheet: `[timestamp, transcript, summary]`
6. The bot replies: `✅ Logged: <summary>`

Progress is printed to the console at every step, so you can watch a run as it happens.

## Tech stack

| Piece | Used for |
| --- | --- |
| [python-telegram-bot](https://python-telegram-bot.org/) | Receiving voice notes, replying |
| [Groq API](https://console.groq.com/) | Whisper transcription + LLM summarization |
| [gspread](https://docs.gspread.org/) + [google-auth](https://google-auth.readthedocs.io/) | Appending rows via a service account |
| [requests](https://requests.readthedocs.io/) | Raw HTTP calls to Groq |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Loading secrets from `.env` |

Everything lives in a single `main.py`.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create your `.env`

Copy the example and fill in the three values:

```bash
cp .env.example .env
```

| Variable | Where to get it |
| --- | --- |
| `TELEGRAM_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `GROQ_API_KEY` | [console.groq.com/keys](https://console.groq.com/keys) |
| `SHEET_ID` | The long ID in your sheet URL: `docs.google.com/spreadsheets/d/<SHEET_ID>/edit` |

### 3. Add a Google service account

1. In the [Google Cloud Console](https://console.cloud.google.com/), create a project and enable the **Google Sheets API**
2. Create a **service account**, then create a **JSON key** for it
3. Save that key as `google-creds.json` in this folder

### 4. Share the sheet with the service account

Open `google-creds.json`, copy the `client_email` value (it looks like
`something@your-project.iam.gserviceaccount.com`), and share your Google Sheet
with that address as an **Editor**.

> Skipping this step is the most common failure — the bot will transcribe and
> summarize fine, then fail with a `403` when it tries to write the row.

### 5. Run it

```bash
python main.py
```

Send the bot a voice note and watch the console.

## Notes

- Uploaded audio files work too, not just recorded voice notes.
- `.env` and `google-creds.json` are gitignored — keep them out of version control.
- Errors are reported back in the Telegram chat as well as the console.

---

Built with [Claude Code](https://claude.com/claude-code).
