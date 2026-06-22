# YouTube Story Bot — 100% FREE Setup Guide

## Total Cost: $0/month forever

| Tool         | Purpose              | Cost |
|--------------|----------------------|------|
| Groq API     | AI story generation  | FREE |
| Edge TTS     | Voice narration      | FREE |
| Pexels API   | Background videos    | FREE |
| MoviePy      | Video assembly       | FREE |
| YouTube API  | Auto upload          | FREE |

---

## STEP 1 — Install Python & Dependencies

Make sure Python 3.9+ is installed, then run:

```
pip install -r requirements.txt
```

Install ImageMagick (needed for title text on video):
- Download from: https://imagemagick.org/script/download.php#windows
- During install tick "Add to system PATH"

---

## STEP 2 — Get Free API Keys

### A) Groq API Key (FREE — no credit card)
1. Go to: https://console.groq.com
2. Sign up with Google or email
3. Click "API Keys" → "Create API Key"
4. Copy the key (starts with "gsk_...")
5. Paste into youtube_bot.py → CONFIG["GROQ_API_KEY"]

### B) Pexels API Key (FREE)
1. Go to: https://www.pexels.com/api/
2. Click "Get Started" → create free account
3. Your API key is shown in the dashboard
4. Paste into youtube_bot.py → CONFIG["PEXELS_API_KEY"]

---

## STEP 3 — Set Up YouTube API

### A) Create Google Cloud Project
1. Go to: https://console.cloud.google.com
2. Click "New Project" → name it anything → Create
3. Go to "APIs & Services" → "Library"
4. Search "YouTube Data API v3" → Enable it

### B) Create OAuth Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. App type: Desktop App → Create
4. Download the JSON file
5. Rename it to: client_secrets.json
6. Put it in the same folder as youtube_bot.py

### C) First-Time Login (one-time only)
- First run opens a browser window automatically
- Log in with your YouTube channel's Google account
- Click Allow
- Done! Token saved for future runs

---

## STEP 4 — Run the Bot

Open Command Prompt in the bot folder, then:

```
# Test only (generate story, no upload):
python youtube_bot.py test

# Run once (full pipeline + upload now):
python youtube_bot.py run

# Auto schedule (uploads daily at best times):
python youtube_bot.py schedule
```

---

## STEP 5 — Keep Bot Running 24/7 on Windows

Option A — Task Scheduler:
1. Search "Task Scheduler" in Start menu
2. Create Basic Task
3. Trigger: Daily
4. Action: Start a Program
5. Program: python.exe
6. Arguments: C:\path\to\youtube_bot.py schedule

Option B — Run minimised in background:
```
start /min python youtube_bot.py schedule
```

---

## Upload Schedule (Automatic)

| Time (UTC) | US Time     | UK Time  | Why                        |
|------------|-------------|----------|----------------------------|
| 19:00      | 3 PM EST    | 8 PM GMT | US afternoon + EU evening  |
| 20:00      | 4 PM EST    | 9 PM GMT | US peak hours              |
| 00:00      | 8 PM EST    | 1 AM GMT | US prime time              |

---

## Change the Narrator Voice

Edit CONFIG["TTS_VOICE"] in youtube_bot.py:

| Voice                  | Style                   |
|------------------------|-------------------------|
| en-GB-RyanNeural       | British male, dramatic  |
| en-US-GuyNeural        | US male, confident      |
| en-US-JennyNeural      | US female, warm         |
| en-GB-SoniaNeural      | British female, elegant |
| en-AU-NatashaNeural    | Australian female       |

---

## File Structure

```
youtube_story_bot/
├── youtube_bot.py          ← Main bot
├── requirements.txt        ← Python packages
├── client_secrets.json     ← Add this (YouTube credentials)
├── youtube_token.json      ← Auto-created after first login
├── bot_log.json            ← Auto-created upload history
└── output/
    ├── audio/              ← Generated voiceovers (.mp3)
    ├── video/              ← Downloaded Pexels clips (.mp4)
    └── final/              ← Final rendered videos (.mp4)
```
