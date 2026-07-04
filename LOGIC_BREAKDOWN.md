# 📚 Code Logic & Architecture Guide

**For developers who want to understand or modify the bot.**

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│               CONFIGURATION & METADATA LAYER                     │
│  (CONFIG dict, VIRAL_STARTERS, THEMES, GENRE_TAGS)             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              CORE PIPELINE FUNCTIONS                             │
│  [1] generate_story()  → AI story + metadata                    │
│  [2] generate_voiceover() → MP3 audio file                      │
│  [3] make_thumbnail() → JPEG image                              │
│  [4] build_video() → MP4 video with effects                     │
│  [5] upload() → YouTube API upload                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              HELPER FUNCTIONS (Visual, Logging, Auth)            │
│  Visual: make_gradient(), add_orb(), add_smoke(), add_particles()│
│  Image: hf_generate_image(), make_frame_image()                 │
│  Auth: get_yt_service(), build_description(), build_tags()      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              EXECUTION (Main & Scheduler)                        │
│  run() → Execute pipeline once                                  │
│  scheduler() → Daily auto-execution                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📖 Step-by-Step Function Breakdown

### [1] STORY GENERATION

#### Function: `generate_story()`

**What it does:**
- Selects random story category from `CONFIG["STORY_CATEGORIES"]`
- Sends detailed prompt to Groq/Llama API
- Extracts story text and metadata (title, tags, chapters)

**Key Parameters in Prompt:**
```python
- Length: 650-900 words (viral sweet spot)
- Hook: Shocking first sentence
- Tension: Escalating throughout
- Ending: Twist or haunting conclusion
```

**Output:**
```python
{
    "story": "The night I died, I was wearing my favourite...",
    "meta": {
        "title": "She Didn't Know She Was Already Dead — [Original Story]",
        "description": "Warning: This story will keep you awake tonight...",
        "tags": "supernatural horror, ghost story, spirit encounter, ...",
        "hook_line": "The breathing stopped but she kept running.",
        "chapter_1": "0:00 — The Beginning",
        "chapter_2": "2:00 — Darkness Falls",
        "chapter_3": "4:00 — The Truth Revealed",
        "scene_images": "dark forest fog,abandoned house,storm clouds,...",
        "category": "supernatural horror"
    },
    "category": "supernatural horror"
}
```

**API Used:**
```
POST https://api.groq.com/openai/v1/chat/completions
Model: llama-3.3-70b-versatile
Temperature: 0.92 (creative/varied)
Max Tokens: 2800
```

---

#### Function: `parse_meta()`

**What it does:**
- Extracts metadata from AI response
- Uses regex to parse `TITLE:`, `DESCRIPTION:`, `TAGS:`, etc.
- Falls back to defaults if parsing fails

**Parsing Logic:**
```python
if line.startswith("TITLE:"):
    meta["title"] = line[6:].strip()
elif line.startswith("DESCRIPTION:"):
    meta["description"] = line[12:].strip()
# ... etc for each metadata field
```

**Fallback Defaults:**
```python
meta = {
    "title": f"{random.choice(VIRAL_STARTERS)} [Original Story]",
    "description": random.choice(VIRAL_HOOKS) + "\n\nOriginal narrated fiction.",
    "tags": ",".join(UNIVERSAL_TAGS[:25]),
    # ... other defaults
}
```

---

### [2] VOICEOVER GENERATION

#### Function: `generate_voiceover()`

**What it does:**
- Uses Microsoft Edge TTS (free neural voices)
- Converts story text to MP3 audio
- Returns file path and duration

**Implementation:**
```python
async def _tts(text, path, voice):
    await edge_tts.Communicate(text, voice).save(path)

def generate_voiceover(text, filename):
    path = os.path.join(CONFIG["AUDIO_DIR"], filename)
    asyncio.run(_tts(text, path, CONFIG["TTS_VOICE"]))
    
    # Get audio duration for video timing
    clip = AudioFileClip(path)
    duration = clip.duration
    clip.close()
    
    return path, duration
```

**Supported Voices:**
- `en-GB-RyanNeural` → British male (default)
- `en-US-GuyNeural` → US male
- `en-US-JennyNeural` → US female
- `en-AU-NatashaNeural` → Australian female

**Quality:**
- 44.1 kHz sample rate
- MP3 codec
- Natural prosody & emotion

---

### [3] THUMBNAIL GENERATION

#### Function: `make_thumbnail()`

**What it does:**
1. Tries to generate AI thumbnail (Hugging Face SDXL)
2. Falls back to procedural generation if AI unavailable
3. Adds text overlay with title + genre badge
4. Adds glowing orbs, corner brackets, color scheme

**Output Size:** 1280x720 JPEG (YouTube standard)

**Layers (bottom to top):**
```
1. Base: Gradient background (theme colors)
2. Effects: Smoke, orbs, particles
3. Overlay: Dark text strip
4. Text: Genre badge (top-left)
5. Text: Main title (center)
6. Text: Bottom bar with CTA
7. Decorations: Corner brackets with glow
```

**Color Themes:**
Each category has unique color palette:
```python
"supernatural horror": dict(
    c1=(40,0,60),    # Top gradient
    c2=(90,0,120),   # Middle gradient
    c3=(60,0,40),    # Bottom gradient
    acc=(200,0,255), # Purple accents (orbs)
    mid=(150,0,200)  # Secondary purple
)
```

---

#### Function: `hf_generate_image()`

**What it does:**
- Calls Hugging Face Serverless Inference API
- Uses Stable Diffusion XL model
- Returns PNG image bytes (decoded to JPEG)

**API Call:**
```python
POST https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0
Authorization: Bearer {HF_API_KEY}

Body:
{
    "inputs": "cinematic dramatic photograph of dark mansion...",
    "parameters": {
        "negative_prompt": "blurry, low quality, text, watermark",
        "num_inference_steps": 25,
        "guidance_scale": 7.5,
        "width": 1280,
        "height": 720
    }
}
```

**Fallback Chain:**
1. Hugging Face SDXL (best quality)
2. Unsplash API (free stock photos)
3. Picsum (always works as backup)

---

### [4] VIDEO BUILDING

#### Function: `build_video()`

**What it does:**
1. Generates or retrieves scene images (5 per video)
2. Uses FFmpeg to crossfade between images
3. Syncs audio with video
4. Outputs MP4 file

**Scene Image Generation:**
```python
keywords = meta["scene_images"].split(",")  # e.g., "dark forest,old house,..."

for keyword in keywords:
    # Try: Hugging Face SDXL → Unsplash → Picsum
    # Returns: image file path
```

**FFmpeg Pipeline:**

```bash
ffmpeg -y \
  -loop 1 -t 5 -i scene_0.jpg \
  -loop 1 -t 5 -i scene_1.jpg \
  -loop 1 -t 5 -i scene_2.jpg \
  ... \
  -i audio.mp3 \
  -filter_complex "
    [0:v][1:v]xfade=transition=fade:duration=2:offset=3[v1];
    [v1][2:v]xfade=transition=fade:duration=2:offset=6[v2];
    ...
    [vN]scale=1280:720,format=yuv420p[vout]
  " \
  -map "[vout]" -map "N:a" \
  -c:v libx264 -preset ultrafast -crf 23 \
  -c:a aac -b:a 128k \
  output.mp4
```

**Crossfade Logic:**
```python
n = len(frame_paths)  # e.g., 5 images
seg_dur = duration / n  # e.g., 600s / 5 = 120s per image
xfade_dur = min(2.0, seg_dur * 0.25)  # 2s crossfade

# Each image displayed for seg_dur, with xfade_dur overlap
```

**Fallback Methods:**
1. **Crossfade** (primary) → Smooth transitions between images
2. **Ken Burns Zoom** (fallback) → Zoom & pan effect on single image
3. **Simple Loop** (fallback) → Loop first image for duration

---

#### Visual Helper Functions

**`make_gradient(w, h, theme)`**
- Creates smooth color gradient (top to bottom)
- Uses theme colors from `THEMES` dict
- Returns PIL Image

**`add_orb(img, cx, cy, r, color, strength)`**
- Draws glowing circular orb at position (cx, cy)
- Creates layered circles for glow effect
- Blurs for smooth radiance

**`add_smoke(img, color, n=8)`**
- Adds atmospheric smoke/haze effect
- Random ellipses with high transparency
- Gaussian blur for organic look

**`add_particles(img, color, n=60)`**
- Scatters small glowing particles across image
- Creates magical/mystical atmosphere
- Theme-colored dots

---

### [5] YOUTUBE UPLOAD

#### Function: `upload()`

**What it does:**
1. Builds video metadata (title, description, tags)
2. Authenticates with YouTube OAuth
3. Uploads video file
4. Sets thumbnail
5. Returns video ID

**YouTube Metadata:**

```python
body = {
    "snippet": {
        "title": "She Didn't Know She Was Already Dead — [Original Story]",
        "description": "WARNING: This story will keep you awake...\n\n📖 CHAPTERS:\n0:00 — The Beginning\n...",
        "tags": ["scary story", "horror narration", "ghost story", ...],
        "categoryId": "24",  # Entertainment
        "defaultLanguage": "en",
        "defaultAudioLanguage": "en"
    },
    "status": {
        "privacyStatus": "public",
        "selfDeclaredMadeForKids": False
    }
}
```

**Authentication Flow:**

```python
def get_yt_service():
    # 1. Check if token exists (youtube_token.json)
    if os.path.exists("youtube_token.json"):
        creds = Credentials.from_authorized_user_file(...)
    
    # 2. If not valid, refresh or re-auth
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(...)
            creds = flow.run_local_server(port=0)  # Opens browser!
    
    # 3. Save token for future runs
    with open("youtube_token.json", "w") as f:
        f.write(creds.to_json())
    
    # 4. Build YouTube service
    return build("youtube", "v3", credentials=creds)
```

**Upload Process:**

```python
yt = get_yt_service()
media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
req = yt.videos().insert(part="snippet,status", body=body, media_body=media)

# Resume until complete
while resp is None:
    status, resp = req.next_chunk()
    if status:
        print(f"Uploading... {int(status.progress()*100)}%")

video_id = resp.get("id")  # e.g., "dQw4w9WgXcQ"
print(f"LIVE: https://www.youtube.com/watch?v={video_id}")
```

---

#### Function: `build_description()`

**What it does:**
- Creates engaging, CTL-rich description
- Includes chapters with timestamps
- Adds listening tips, engagement CTAs
- Complies with YouTube guidelines

**Structure:**
```
1. HOOK LINE (viral attention grabber)
2. Description (tease story without spoiling)
3. COMMENT CTA (quotable line from story)
4. CHAPTERS (with timestamps)
5. LISTENING TIPS (headphones, dark room, etc.)
6. ABOUT THIS STORY (metadata)
7. JOIN COMMUNITY (subscribe, like, share CTAs)
8. MORE STORIES (related content preview)
9. DISCLAIMER (original content notice)
10. HASHTAGS (30+ hashtags)
```

---

#### Function: `build_tags()`

**What it does:**
- Combines: AI-generated + genre + universal tags
- Removes duplicates + invalid characters
- Limits to 30 tags (YouTube max)
- Ensures < 490 character total

**Tag Sources:**
```python
ai_tags = meta["tags"]  # Generated by AI
genre_tags = GENRE_TAGS[category]  # "supernatural horror" → [...]
universal_tags = UNIVERSAL_TAGS  # Generic tags for all videos

# Combine and deduplicate
all_tags = list(dict.fromkeys(ai_tags + genre_tags + universal_tags))

# Clean: remove invalid chars, limit length
cleaned = [clean_tag(t) for t in all_tags if len(clean_tag(t)) >= 2]

# Limit to 30 tags + 490 chars total
return cleaned[:30] if sum(len(t) for t in cleaned) <= 490
```

---

## 🔄 Execution Flow

### Mode 1: Single Run (`run`)

```
┌─ Main: run()
│
├─ [1] generate_story()
│    ├─ Call Groq API
│    └─ Return: story text + metadata
│
├─ [2] generate_voiceover()
│    ├─ Call Edge TTS
│    └─ Return: audio path + duration
│
├─ [3] make_thumbnail()
│    ├─ Try HF SDXL (if API key set)
│    ├─ Else: procedural generation
│    └─ Return: thumbnail path
│
├─ [4] build_video()
│    ���─ Generate/get scene images
│    ├─ Call FFmpeg
│    └─ Return: video path
│
├─ [5] upload()
│    ├─ Authenticate YouTube
│    ├─ Upload video
│    ├─ Set thumbnail
│    └─ Return: video ID
│
└─ save_log()
     └─ Log: timestamp, title, video ID, status
```

**Total Time:** ~15-20 minutes (depends on internet speed)

---

### Mode 2: Scheduler (`schedule`)

```
┌─ Main: scheduler()
│
├─ For each time in CONFIG["UPLOAD_TIMES_UTC"]:
│    ├─ schedule.every().day.at(time).do(run)
│    └─ Register job
│
├─ While True:
│    ├─ schedule.run_pending()
│    │  ├─ If current time matches: run()
│    │  └─ Execute full pipeline
│    │
│    └─ time.sleep(60)  # Check every minute
```

**Example Schedule:**
- 19:00 UTC → run() → upload ~19:15
- 20:00 UTC → run() → upload ~20:15
- 00:00 UTC → run() → upload ~00:15

---

## 🛠️ Key Configuration Options

### Story Categories

**Current Options:**
- `supernatural horror` → Demons, curses, possession
- `psychological thriller` → Mind games, unreliable narrators
- `mystery suspense` → Puzzles, whodunits
- `ghost story` → Spirits, hauntings
- `survival horror` → Life-or-death scenarios
- `sci-fi horror` → Aliens, space, dystopia
- `dark emotional drama` → Heartbreaking narratives
- `paranormal encounter` → Unexplained phenomena
- `urban legend` → Folklore, internet creepypasta
- `historical dark mystery` → Period horror

**To Add New Category:**
1. Add to `CONFIG["STORY_CATEGORIES"]`
2. Create theme in `THEMES` dict:
   ```python
   THEMES["new_category"] = dict(
       c1=(r1,g1,b1), c2=(r2,g2,b2), c3=(r3,g3,b3),
       acc=(ar,ag,ab), mid=(mr,mg,mb)
   )
   ```
3. Add to `GENRE_TAGS`:
   ```python
   GENRE_TAGS["new_category"] = ["tag1", "tag2", ...]
   ```

---

### Viral Metadata

**Tested & Optimized:**

```python
VIRAL_STARTERS = [
    "Nobody Believed Her Until It Was Too Late —",
    "He Opened the Door and Wished He Hadn't —",
    "She Didn't Know She Was Already Dead —",
    # ... 7 more
]

VIRAL_HOOKS = [
    "⚠️ WARNING: This story will keep you awake tonight.",
    "🔴 Thousands of viewers couldn't finish this.",
    # ... 4 more
]
```

These are A/B tested for:
- **Curiosity gap** (makes you click)
- **Emotional trigger** (fear, sadness)
- **Urgency** (limited/exclusive feeling)

---

## 📊 Data Formats

### bot_log.json

```json
[
  {
    "ts": "20250703_142530",
    "title": "He Opened the Door and Wished He Hadn't — [Original Story]",
    "id": "dQw4w9WgXcQ",
    "duration": 487,
    "status": "success"
  },
  {
    "ts": "20250703_190045",
    "title": "Nobody Believed Her Until It Was Too Late — [Original Story]",
    "id": "jNQXAC9IVRw",
    "duration": 512,
    "status": "success"
  },
  {
    "ts": "20250704_013050",
    "status": "failed",
    "error": "FFmpeg not found in PATH"
  }
]
```

---

## 🐛 Common Issues & Fixes

### Issue: "API rate limit exceeded"

**Cause:** Groq/Hugging Face free tier has rate limits

**Solution:**
```python
# Add retry logic with exponential backoff
import time

def retry_api_call(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            wait = 2 ** attempt  # 1s, 2s, 4s
            print(f"Rate limited. Waiting {wait}s...")
            time.sleep(wait)
    raise Exception("Max retries exceeded")
```

### Issue: "FFmpeg crossfade not working"

**Cause:** Complex filter chain syntax error

**Solution:**
```python
# Fallback to Ken Burns zoom (line 654)
# Then fallback to simple loop (line 667)
# Handles most edge cases gracefully
```

---

## 🚀 Optimization Tips

### Speed Up Video Generation
```python
# Reduce FFmpeg preset (faster, larger file)
"-preset", "ultrafast",  # Current: fastest encoding
# "-preset", "fast",     # Medium speed/quality
# "-preset", "medium",   # Slower but better quality

# Reduce CRF (lower quality, faster)
"-crf", "23",  # Current: good quality
# "-crf", "28",  # Lower quality, faster
```

### Reduce AI Image Generation Time
```python
# Reduce inference steps (faster, lower quality)
"num_inference_steps": 25,  # Current
# "num_inference_steps": 15,  # Faster

# Use smaller guidance scale (faster)
"guidance_scale": 7.5,  # Current: good adherence to prompt
# "guidance_scale": 5.0,  # Less adherent, faster
```

---

## 📚 External APIs Used

| API | Endpoint | Purpose | Auth |
|-----|----------|---------|------|
| **Groq** | `api.groq.com/openai/v1/chat/completions` | Story generation | API Key |
| **Edge TTS** | `edge-tts` library | Voiceover | None (free) |
| **Hugging Face** | `api-inference.huggingface.co` | SDXL images | API Token |
| **Unsplash** | `source.unsplash.com/featured` | Stock photos (fallback) | None (free) |
| **Picsum** | `picsum.photos/seed/{seed}/1280/720` | Random images (fallback) | None (always works) |
| **YouTube** | `youtube.googleapis.com/v3` | Upload + metadata | OAuth 2.0 |

---

## 🎓 Learning Resources

If you want to extend this bot:

1. **Groq API:** https://console.groq.com/docs/quickstart
2. **Edge TTS:** https://github.com/rany2/edge-tts
3. **Hugging Face:** https://huggingface.co/docs/api-inference
4. **FFmpeg:** https://ffmpeg.org/documentation.html
5. **YouTube API:** https://developers.google.com/youtube/v3

---

**Questions? Check the main README or SETUP_GUIDE for more help!**
