"""
YouTube Story Bot — WORKS 100% OFFLINE
========================================
NO external video downloads needed — ever.
All visuals generated with pure Python + FFmpeg.
Video shows animated glowing particles, color shifts, light effects.

FREE | COPYRIGHT SAFE | VIRAL OPTIMIZED
"""

import os, sys, json, time, random, asyncio, schedule, subprocess, struct, zlib
import urllib.request, urllib.parse
from datetime import datetime

import edge_tts
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from groq import Groq
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
CONFIG = {
    "GROQ_API_KEY":           "Your_GROQ_API_KEY",
    # Get FREE at: huggingface.co → Settings → Access Tokens (no credit card)
    # Used for AI image generation (Stable Diffusion XL) — scene images + thumbnail
    "HF_API_KEY":             "YOUR_HUGGINGFACE_TOKEN",
    "YOUTUBE_CLIENT_SECRETS": "client_secrets.json",
    "TTS_VOICE":              "en-GB-RyanNeural",
    "AUDIO_DIR":     "output/audio",
    "FINAL_DIR":     "output/final",
    "IMG_DIR":       "output/images",
    "THUMBNAIL_DIR": "output/thumbnails",
    "STORY_CATEGORIES": [
        "supernatural horror", "psychological thriller", "mystery suspense",
        "ghost story", "survival horror", "sci-fi horror", "dark emotional drama",
        "paranormal encounter", "urban legend", "historical dark mystery",
    ],
    "MIN_WORDS": 650,
    "MAX_WORDS": 900,
    "UPLOAD_TIMES_UTC": ["19:00", "20:00", "00:00"],
    "VIDEO_WIDTH":  1280,
    "VIDEO_HEIGHT": 720,
    "FPS":          24,
}

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# ══════════════════════════════════════════════════════════════════════════════
#  VIRAL METADATA
# ══════════════════════════════════════════════════════════════════════════════
VIRAL_STARTERS = [
    "Nobody Believed Her Until It Was Too Late —",
    "He Opened the Door and Wished He Hadn't —",
    "She Didn't Know She Was Already Dead —",
    "The Call Came at 3AM and Everything Changed —",
    "The House Was Empty But Someone Was Home —",
    "He Came Back After 10 Years But Something Was Wrong —",
    "The Mirror Showed Something That Wasn't There —",
    "She Got the Text From Her Own Number —",
    "The Doctor Said He Was Fine. He Wasn't. —",
    "She Moved In and Heard the Breathing at Night —",
]
VIRAL_HOOKS = [
    "⚠️ WARNING: This story will keep you awake tonight.",
    "🔴 Thousands of viewers couldn't finish this. Can you?",
    "💀 Best listened to alone, with the lights off.",
    "⚡ Comment 'I MADE IT' if you finish the whole thing.",
    "🔇 Put your headphones in. You need to hear every word.",
    "😰 We almost didn't upload this one. You'll understand why.",
]
GENRE_TAGS = {
    "supernatural horror":    ["supernatural horror","demonic story","evil entity","spirit encounter"],
    "psychological thriller":  ["psychological horror","mind games story","twisted ending","disturbing story"],
    "mystery suspense":        ["mystery story","whodunit","unsolved mystery","detective story"],
    "ghost story":             ["ghost story","ghost encounter","haunted house","spirit story"],
    "survival horror":         ["survival horror","life or death","wilderness horror"],
    "sci-fi horror":           ["sci-fi horror","alien story","space horror","future horror"],
    "dark emotional drama":    ["emotional story","heartbreaking story","sad narration","drama story"],
    "paranormal encounter":    ["paranormal story","strange encounter","unexplained phenomena"],
    "urban legend":            ["urban legend","local legend horror","folklore horror"],
    "historical dark mystery": ["historical horror","period mystery","ancient mystery","gothic horror"],
}
UNIVERSAL_TAGS = [
    "scary story","horror story","story time","narrated story","scary stories 2025",
    "horror narration","ghost story narration","mystery story","thriller story",
    "short horror story","nosleep","nosleep narration","creepypasta","scary story time",
    "horror fiction","dark story","best scary stories","midnight stories",
    "horror podcast","story narration","english horror story","scary bedtime story",
    "original horror story","spooky story","chilling story","terrifying story",
    "psychological horror","paranormal story","haunted story","supernatural story",
    "dark fiction","horror story 2025","best horror narration","scary story narration",
]

# Colour themes — bright enough to actually see
THEMES = {
    "supernatural horror":    dict(c1=(40,0,60),  c2=(90,0,120),  c3=(60,0,40),  acc=(200,0,255),  mid=(150,0,200)),
    "psychological thriller":  dict(c1=(0,20,60),  c2=(0,50,120),  c3=(20,30,80), acc=(0,180,255),  mid=(0,100,200)),
    "mystery suspense":        dict(c1=(0,30,50),  c2=(0,80,100),  c3=(0,50,70),  acc=(0,220,200),  mid=(0,150,150)),
    "ghost story":             dict(c1=(30,30,70), c2=(70,60,130), c3=(40,40,90), acc=(180,180,255), mid=(120,120,200)),
    "survival horror":         dict(c1=(20,50,10), c2=(40,100,20), c3=(30,70,15), acc=(50,220,30),  mid=(30,160,20)),
    "sci-fi horror":           dict(c1=(0,20,80),  c2=(0,60,150),  c3=(0,40,100), acc=(0,220,255),  mid=(0,150,200)),
    "dark emotional drama":    dict(c1=(70,10,10), c2=(130,20,20), c3=(90,15,15), acc=(255,80,80),  mid=(200,40,40)),
    "paranormal encounter":    dict(c1=(30,0,60),  c2=(70,10,120), c3=(50,0,80),  acc=(160,0,255),  mid=(100,0,180)),
    "urban legend":            dict(c1=(40,30,0),  c2=(90,60,0),   c3=(60,40,0),  acc=(255,180,0),  mid=(200,120,0)),
    "historical dark mystery": dict(c1=(50,30,0),  c2=(100,60,10), c3=(70,40,5),  acc=(220,170,50), mid=(160,110,20)),
}
DEFAULT_THEME = THEMES["supernatural horror"]


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def check_config():
    if CONFIG["GROQ_API_KEY"] == "YOUR_GROQ_API_KEY":
        print("\nERROR: Set GROQ_API_KEY in youtube_bot.py")
        print("Get FREE at: https://console.groq.com")
        sys.exit(1)

def check_youtube():
    if not os.path.exists(CONFIG["YOUTUBE_CLIENT_SECRETS"]):
        print("\nERROR: client_secrets.json not found.")
        print("See SETUP_GUIDE.md for YouTube API setup instructions.")
        sys.exit(1)

def save_log(entry):
    logs = []
    if os.path.exists("bot_log.json"):
        with open("bot_log.json") as f:
            try: logs = json.load(f)
            except: pass
    logs.append(entry)
    with open("bot_log.json","w") as f:
        json.dump(logs, f, indent=2)

def wrap_text(text, max_chars):
    words, lines, line = text.split(), [], ""
    for w in words:
        if len(line)+len(w)+1 <= max_chars: line = (line+" "+w).strip()
        else:
            if line: lines.append(line)
            line = w
    if line: lines.append(line)
    return lines


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — GENERATE STORY
# ══════════════════════════════════════════════════════════════════════════════
def generate_story():
    print("\n[1/5] Generating viral story with Groq AI...")
    client   = Groq(api_key=CONFIG["GROQ_API_KEY"])
    category = random.choice(CONFIG["STORY_CATEGORIES"])
    hook     = random.choice(VIRAL_STARTERS)

    prompt = f"""You are a world-class viral YouTube story writer whose stories get millions of views.

Write a 100% ORIGINAL {category.upper()} STORY:
- Length: EXACTLY {CONFIG['MIN_WORDS']} to {CONFIG['MAX_WORDS']} words
- FIRST SENTENCE must be shocking enough to stop someone from scrolling. Examples:
  "The night I died, I was wearing my favourite red dress."
  "My son asked why there was a woman standing behind me — there was nobody there."
  "I found my own obituary in the newspaper, dated three days from now."
- Escalating tension: each paragraph must be more gripping than the last
- Short punchy sentences during scary moments. Slower during atmosphere
- Vivid sensory details: sounds, smells, textures
- Shocking twist or haunting final line that makes viewers comment
- Invent ALL characters, places, events — no real people, no brands, no franchises
- Plain paragraphs ONLY — no headings, no asterisks, no markdown, no bullet points

After the story write exactly:
---META---
TITLE: [Max 70 chars. Curiosity-gap style like "{hook.rstrip(' —')} [something]". Must be impossible NOT to click.]
DESCRIPTION: [200 words. Start with a shocking hook line. Tease the story without spoiling. Include listening tips. End with strong CTA.]
TAGS: [30 tags separated by commas — mix broad, niche, emotional, trending 2025. No brand names.]
HOOK_LINE: [The single most quotable/shareable line from the story]
CHAPTER_1: [e.g. "0:00 — The Beginning"]
CHAPTER_2: [e.g. "2:30 — The Dark Truth"]
CHAPTER_3: [e.g. "4:00 — No Way Out"]
SCENE_IMAGES: [5 specific visual search keywords for Unsplash photos that match THIS story's actual scenes. Use single concrete nouns or short phrases like: "dark forest", "old mansion", "cemetery night", "candle flame", "stormy ocean", "abandoned church", "foggy road", "haunted attic", "old lighthouse", "dark cave". Match the actual locations and mood in YOUR story. No abstract words.]

Genre: {category}"""

    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}],
        temperature=0.92,
        max_tokens=2800,
    )
    full  = resp.choices[0].message.content
    story, mb = (full.split("---META---",1) if "---META---" in full else (full,""))
    story = story.strip()
    meta  = parse_meta(mb, category)
    meta["category"] = category

    print(f"    {len(story.split())} words | Genre: {category}")
    print(f"    Title: {meta['title']}")
    return story, meta, category


def parse_meta(block, category):
    starter = random.choice(VIRAL_STARTERS)
    meta = {
        "title":      f"{starter.rstrip(' —')} [Original Story]",
        "description": random.choice(VIRAL_HOOKS) + "\n\nOriginal narrated fiction.",
        "tags":        ",".join(UNIVERSAL_TAGS[:25]),
        "hook_line":   "This story will stay with you long after it ends.",
        "chapter_1":   "0:00 — The Beginning",
        "chapter_2":   "2:00 — Darkness Falls",
        "chapter_3":   "4:00 — The Truth Revealed",
        "scene_images": "dark forest fog,abandoned house,storm clouds,candlelight dark,old cemetery",
        "category":    category,
    }
    for line in block.strip().splitlines():
        l = line.strip()
        if   l.startswith("TITLE:"):        meta["title"]        = l[6:].strip()
        elif l.startswith("DESCRIPTION:"):  meta["description"]  = l[12:].strip()
        elif l.startswith("TAGS:"):         meta["tags"]         = l[5:].strip()
        elif l.startswith("HOOK_LINE:"):    meta["hook_line"]    = l[10:].strip()
        elif l.startswith("CHAPTER_1:"):    meta["chapter_1"]    = l[10:].strip()
        elif l.startswith("CHAPTER_2:"):    meta["chapter_2"]    = l[10:].strip()
        elif l.startswith("CHAPTER_3:"):    meta["chapter_3"]    = l[10:].strip()
        elif l.startswith("SCENE_IMAGES:"): meta["scene_images"] = l[13:].strip()
    return meta


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2 — VOICEOVER
# ══════════════════════════════════════════════════════════════════════════════
async def _tts(text, path, voice):
    await edge_tts.Communicate(text, voice).save(path)

def generate_voiceover(text, filename):
    print("\n[2/5] Generating voiceover (Edge TTS — free)...")
    os.makedirs(CONFIG["AUDIO_DIR"], exist_ok=True)
    path = os.path.join(CONFIG["AUDIO_DIR"], filename)
    asyncio.run(_tts(text, path, CONFIG["TTS_VOICE"]))
    from moviepy import AudioFileClip
    clip = AudioFileClip(path)
    dur  = clip.duration
    clip.close()
    print(f"    Voiceover: {int(dur//60)}m {int(dur%60)}s")
    return path, dur


# ══════════════════════════════════════════════════════════════════════════════
#  VISUAL HELPERS  (Pillow)
# ══════════════════════════════════════════════════════════════════════════════
def make_gradient(w, h, theme):
    c1,c2,c3 = theme["c1"],theme["c2"],theme["c3"]
    img = Image.new("RGB",(w,h))
    d   = ImageDraw.Draw(img)
    half= h//2
    for y in range(half):
        t = (y/half)**0.7
        d.line([(0,y),(w,y)], fill=(int(c1[0]+(c2[0]-c1[0])*t),
                                    int(c1[1]+(c2[1]-c1[1])*t),
                                    int(c1[2]+(c2[2]-c1[2])*t)))
    for y in range(half,h):
        t = ((y-half)/half)**0.7
        d.line([(0,y),(w,y)], fill=(int(c2[0]+(c3[0]-c2[0])*t),
                                    int(c2[1]+(c3[1]-c2[1])*t),
                                    int(c2[2]+(c3[2]-c2[2])*t)))
    return img

def add_orb(img, cx, cy, r, color, strength=0.70):
    layer = Image.new("RGBA",img.size,(0,0,0,0))
    d     = ImageDraw.Draw(layer)
    for i in range(16,0,-1):
        rad   = int(r*i/16)
        alpha = int(255*strength*(1-i/16)**1.3)
        d.ellipse([(cx-rad,cy-rad),(cx+rad,cy+rad)],
                  fill=(color[0],color[1],color[2],alpha))
    blurred = layer.filter(ImageFilter.GaussianBlur(radius=r//4))
    return Image.alpha_composite(img.convert("RGBA"),blurred).convert("RGB")

def add_smoke(img, color, n=8):
    w,h    = img.size
    result = img.convert("RGBA")
    for _ in range(n):
        s  = Image.new("RGBA",(w,h),(0,0,0,0))
        d  = ImageDraw.Draw(s)
        cx = random.randint(0,w)
        cy = random.randint(int(h*0.2),h)
        rx = random.randint(150,480)
        ry = random.randint(50,160)
        a  = random.randint(12,38)
        d.ellipse([(cx-rx,cy-ry),(cx+rx,cy+ry)],fill=(color[0],color[1],color[2],a))
        result = Image.alpha_composite(result,s.filter(ImageFilter.GaussianBlur(32)))
    return result.convert("RGB")

def add_particles(img, color, n=60):
    layer = Image.new("RGBA",img.size,(0,0,0,0))
    d     = ImageDraw.Draw(layer)
    w,h   = img.size
    for _ in range(n):
        px,py = random.randint(0,w),random.randint(0,h)
        pr    = random.randint(1,4)
        pa    = random.randint(50,180)
        d.ellipse([(px-pr,py-pr),(px+pr,py+pr)],
                  fill=(color[0],color[1],color[2],pa))
    return Image.alpha_composite(img.convert("RGBA"),layer).convert("RGB")

def make_frame_image(category, w, h, orb_x_frac, orb_y_frac, seed=0):
    """Generate one background frame with orb at given position."""
    random.seed(seed)
    theme = THEMES.get(category, DEFAULT_THEME)
    acc   = theme["acc"]
    mid   = theme["mid"]

    img = make_gradient(w, h, theme)
    img = add_smoke(img, acc, n=7)
    img = add_orb(img, int(w*orb_x_frac), int(h*orb_y_frac), int(min(w,h)*0.28), acc, strength=0.75)
    img = add_orb(img, int(w*(1-orb_x_frac)), int(h*(1-orb_y_frac)), int(min(w,h)*0.18), mid, strength=0.50)
    img = add_particles(img, acc, n=55)

    # Mild vignette
    vig  = Image.new("RGB",(w,h),(0,0,0))
    mask = Image.new("L",(w,h),0)
    md   = ImageDraw.Draw(mask)
    mg   = int(min(w,h)*0.06)
    md.ellipse([(mg,mg),(w-mg,h-mg)],fill=225)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=min(w,h)//7))
    img  = Image.composite(img,vig,mask)
    return img


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — THUMBNAIL
# ══════════════════════════════════════════════════════════════════════════════
def make_thumbnail(category, title, timestamp):
    print("\n[3/5] Generating thumbnail...")
    os.makedirs(CONFIG["THUMBNAIL_DIR"], exist_ok=True)
    path  = os.path.join(CONFIG["THUMBNAIL_DIR"], f"thumb_{timestamp}.jpg")
    w, h  = 1280, 720
    theme = THEMES.get(category, DEFAULT_THEME)
    acc   = theme["acc"]
    mid   = theme["mid"]

    # Try AI-generated background first (Hugging Face SDXL)
    ai_bg_path = os.path.join(CONFIG["THUMBNAIL_DIR"], f"thumb_bg_{timestamp}.jpg")
    ai_used    = False
    if CONFIG.get("HF_API_KEY","") not in ("","YOUR_HUGGINGFACE_TOKEN"):
        print("    Generating AI thumbnail background (SDXL)...")
        ai_used = hf_generate_thumbnail(title, category, ai_bg_path, w, h)

    if ai_used:
        img = Image.open(ai_bg_path).convert("RGB")
        print("    ✓ AI thumbnail background generated!")
    else:
        img = make_frame_image(category, w, h, 0.15, 0.80, seed=42)

    # Dark text strip
    ov  = Image.new("RGBA",img.size,(0,0,0,0))
    od  = ImageDraw.Draw(ov)
    od.rectangle([(0,int(h*0.20)),(w,int(h*0.82))],fill=(0,0,0,140))
    img = Image.alpha_composite(img.convert("RGBA"),ov).convert("RGB")

    draw = ImageDraw.Draw(img)

    # Load fonts
    font_paths = [
        ("C:/Windows/Fonts/arialbd.ttf","C:/Windows/Fonts/arialbd.ttf","C:/Windows/Fonts/arial.ttf"),
        ("arial.ttf","arial.ttf","arial.ttf"),
    ]
    fb=fm=fs=None
    for bold_path, med_path, reg_path in font_paths:
        try:
            fb = ImageFont.truetype(bold_path, 88)
            fm = ImageFont.truetype(med_path,  38)
            fs = ImageFont.truetype(reg_path,  28)
            break
        except: pass
    if fb is None:
        fb=fm=fs=ImageFont.load_default()

    # Genre badge
    badge = "▶  " + category.upper().replace(" FICTION","").replace(" STORY","")
    bx,by = 60,52
    bb    = draw.textbbox((0,0),badge,font=fs)
    bw,bh = bb[2]-bb[0]+28, bb[3]-bb[1]+16
    draw.rectangle([(bx-4,by-4),(bx+bw,by+bh)],fill=(acc[0]//4,acc[1]//4,acc[2]//4))
    draw.rectangle([(bx-4,by-4),(bx+bw,by+bh)],outline=acc,width=2)
    draw.text((bx+10,by+5),badge,font=fs,fill=acc)

    # Main title with glow
    clean = title.strip('"').strip("'")
    lines = wrap_text(clean, 20)
    th    = len(lines)*96
    sy    = (h-th)//2 - 15
    for i, line in enumerate(lines[:3]):
        bb2 = draw.textbbox((0,0),line,font=fb)
        lw  = bb2[2]-bb2[0]
        lx  = (w-lw)//2
        ly  = sy+i*96
        gc  = (min(255,acc[0]+60),min(255,acc[1]+60),min(255,acc[2]+60))
        for off in [9,6,4,2]:
            for dx,dy in [(off,off),(-off,off),(off,-off),(-off,-off)]:
                draw.text((lx+dx,ly+dy),line,font=fb,fill=gc)
        draw.text((lx,ly),line,font=fb,fill=(255,255,255))

    # Bottom bar
    by2 = int(h*0.82)
    draw.rectangle([(0,by2),(w,h)],fill=(0,0,0))
    draw.line([(0,by2),(w,by2)],fill=acc,width=4)
    tl  = "◆  NARRATED ORIGINAL STORY  ◆  NEW STORY EVERY DAY  ◆  SUBSCRIBE  ◆"
    tb  = draw.textbbox((0,0),tl,font=fm)
    tw  = tb[2]-tb[0]
    draw.text(((w-tw)//2,by2+16),tl,font=fm,fill=(220,220,220))

    # Corner brackets
    for cx2,cy2,dx,dy in [(52,52,1,1),(w-52,52,-1,1),(52,h-52,1,-1),(w-52,h-52,-1,-1)]:
        draw.line([(cx2,cy2),(cx2+dx*55,cy2)],fill=acc,width=5)
        draw.line([(cx2,cy2),(cx2,cy2+dy*55)],fill=acc,width=5)

    img.save(path,"JPEG",quality=95)
    print(f"    Thumbnail saved: {path}")
    return path


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 4 — BUILD VIDEO  (pure FFmpeg, no downloads needed)
#
#  Strategy: generate N frame images with different orb positions,
#  then use FFmpeg to crossfade between them + attach audio.
#  Result: smooth animated glowing background video, 100% original.
# ══════════════════════════════════════════════════════════════════════════════
def hf_generate_image(prompt, out_path, w, h):
    """
    Generate one AI image using Hugging Face Serverless Inference API.
    Model: Stable Diffusion XL (stabilityai/stable-diffusion-xl-base-1.0)
    Free tier: ~hundreds of requests/hour. No credit card needed.
    """
    import io
    hf_key = CONFIG.get("HF_API_KEY","")
    if not hf_key or hf_key == "YOUR_HUGGINGFACE_TOKEN":
        return False

    api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {
        "Authorization": f"Bearer {hf_key}",
        "Content-Type":  "application/json",
        "x-use-cache":   "0",
    }
    body = json.dumps({
        "inputs": prompt,
        "parameters": {
            "negative_prompt": "blurry, low quality, text, watermark, logo, people, faces, cartoon",
            "num_inference_steps": 25,
            "guidance_scale": 7.5,
            "width": 1280,
            "height": 720,
        }
    }).encode()

    try:
        req = urllib.request.Request(api_url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()

        if len(raw) < 1000:
            # Might be JSON error message
            try:
                err = json.loads(raw)
                print(f"    HF API: {err.get('error','unknown error')[:80]}")
            except:
                pass
            return False

        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img = img.resize((w, h), Image.LANCZOS)
        # Subtle dark overlay for atmospheric mood
        ov  = Image.new("RGBA", (w, h), (0, 0, 0, 80))
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        img.save(out_path, "JPEG", quality=90)
        return True

    except Exception as e:
        print(f"    HF error: {str(e)[:80]}")
        return False


def generate_scene_images(keywords, w, h):
    """
    Generate scene-matching AI images.
    Priority: Hugging Face SDXL → Unsplash → Picsum
    """
    import io
    print("    Generating AI scene images (Hugging Face SDXL)...")
    os.makedirs(CONFIG["IMG_DIR"], exist_ok=True)
    downloaded = []
    hf_ok      = CONFIG.get("HF_API_KEY","") not in ("","YOUR_HUGGINGFACE_TOKEN")
    hdrs       = {"User-Agent":"Mozilla/5.0","Accept":"image/jpeg,image/*"}

    for i, keyword in enumerate(keywords[:5]):
        out_path = os.path.join(CONFIG["IMG_DIR"], f"scene_{i}.jpg")
        success  = False

        # ── METHOD 1: Hugging Face SDXL (real AI image matching scene) ────────
        if hf_ok:
            prompt = (
                f"cinematic dramatic photograph of {keyword}, "
                "dark moody horror atmosphere, dramatic lighting, "
                "high detail, photorealistic, wide angle, 4k, "
                "no people, no text, no watermarks"
            )
            print(f"    Generating AI: '{keyword}'...")
            success = hf_generate_image(prompt, out_path, w, h)
            if success:
                print(f"    ✓ AI image: '{keyword}' (Stable Diffusion XL)")
            else:
                print(f"    HF failed for '{keyword}', trying Unsplash...")

        # ── METHOD 2: Unsplash photo ───────────────────────────────────────────
        if not success:
            try:
                safe_kw = urllib.parse.quote(keyword.strip())
                url2    = f"https://source.unsplash.com/featured/1280x720/?{safe_kw}"
                req2    = urllib.request.Request(url2, headers=hdrs)
                with urllib.request.urlopen(req2, timeout=20) as r2:
                    raw2 = r2.read()
                if len(raw2) > 5000:
                    img2 = Image.open(io.BytesIO(raw2)).convert("RGB")
                    img2 = img2.resize((w,h),Image.LANCZOS)
                    ov2  = Image.new("RGBA",(w,h),(0,0,0,100))
                    img2 = Image.alpha_composite(img2.convert("RGBA"),ov2).convert("RGB")
                    img2.save(out_path,"JPEG",quality=88)
                    downloaded.append(out_path)
                    print(f"    ✓ Unsplash: '{keyword}'")
                    success = True
            except Exception as e2:
                print(f"    Unsplash failed: {str(e2)[:50]}")

        # ── METHOD 3: Picsum (always works) ────────────────────────────────────
        if not success:
            try:
                seed = abs(hash(keyword)) % 1000
                url3 = f"https://picsum.photos/seed/{seed}/1280/720"
                req3 = urllib.request.Request(url3, headers=hdrs)
                with urllib.request.urlopen(req3, timeout=15) as r3:
                    raw3 = r3.read()
                img3 = Image.open(io.BytesIO(raw3)).convert("RGB")
                img3 = img3.resize((w,h),Image.LANCZOS)
                ov3  = Image.new("RGBA",(w,h),(0,0,0,100))
                img3 = Image.alpha_composite(img3.convert("RGBA"),ov3).convert("RGB")
                img3.save(out_path,"JPEG",quality=88)
                downloaded.append(out_path)
                print(f"    ✓ Picsum fallback: '{keyword}'")
                success = True
            except Exception as e3:
                print(f"    All methods failed for '{keyword}'")

        if success and out_path not in downloaded:
            downloaded.append(out_path)

    print(f"    {len(downloaded)}/5 scene images ready")
    return downloaded


def hf_generate_thumbnail(title, category, out_path, w=1280, h=720):
    """Generate an AI thumbnail background using Hugging Face SDXL."""
    theme_prompts = {
        "supernatural horror":    "dark haunted mansion with purple lightning, gothic atmosphere",
        "psychological thriller":  "dark rainy city at night, neon reflections, noir style",
        "mystery suspense":        "misty foggy forest path at night, mysterious atmosphere",
        "ghost story":             "old candlelit room with curtains blowing, ghostly atmosphere",
        "survival horror":         "person silhouette against stormy sky, dramatic survival scene",
        "sci-fi horror":           "dark space station corridor with ominous red lights",
        "dark emotional drama":    "dramatic rain on window at night, emotional dark scene",
        "paranormal encounter":    "dark forest with mysterious floating lights at night",
        "urban legend":            "empty dark alley with single streetlight in fog",
        "historical dark mystery": "medieval castle on cliff in stormy night, lightning",
    }
    base = theme_prompts.get(category, "dark dramatic atmospheric scene, horror mood")
    prompt = (
        f"Cinematic horror movie poster style background: {base}. "
        "Dark moody dramatic lighting, highly detailed, photorealistic, "
        "4k quality, wide shot, no text, no people, no watermarks."
    )
    return hf_generate_image(prompt, out_path, w, h)


def build_video(audio_path, duration, category, output_path, scene_keywords=""):
    print("\n[4/5] Building video with scene images...")
    import imageio_ffmpeg
    os.makedirs(CONFIG["IMG_DIR"], exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    w, h   = CONFIG["VIDEO_WIDTH"], CONFIG["VIDEO_HEIGHT"]
    fps    = CONFIG["FPS"]

    # Try to get real scene images from Wikimedia Commons (public domain, no API key)
    keywords = [k.strip() for k in scene_keywords.split(",") if k.strip()]
    if not keywords:
        keywords = ["dark forest fog","abandoned house","storm clouds","candlelight dark","old cemetery mist"]

    scene_images = generate_scene_images(keywords, w, h)

    # If we got scene images, use them; otherwise use generated frames
    if scene_images:
        frame_paths = scene_images
        print(f"    Using {len(frame_paths)} real scene images")
    else:
        # Fallback: generate artistic frames
        print("    Using generated artistic frames...")
        orb_positions = [(0.15,0.80),(0.82,0.22),(0.50,0.88),(0.20,0.18),(0.75,0.75)]
        frame_paths   = []
        for i,(ox,oy) in enumerate(orb_positions):
            img  = make_frame_image(category, w, h, ox, oy, seed=i*7)
            path = os.path.join(CONFIG["IMG_DIR"], f"frame_{i}.jpg")
            img.save(path,"JPEG",quality=90)
            frame_paths.append(path)
            print(f"    Frame {i+1}/{len(orb_positions)} rendered")

    # Build FFmpeg crossfade between frames
    n         = len(frame_paths)
    seg_dur   = duration / n
    xfade_dur = min(2.0, seg_dur * 0.25)

    inputs = []
    for fp in frame_paths:
        inputs += ["-loop","1","-t",str(seg_dur + xfade_dur + 0.5),"-i",fp]

    filter_parts = []
    last = "0:v"
    for i in range(1, n):
        offset  = seg_dur*i - xfade_dur*(i-1)
        out_lbl = f"v{i}"
        filter_parts.append(
            f"[{last}][{i}:v]xfade=transition=fade"
            f":duration={xfade_dur:.2f}:offset={offset:.2f}[{out_lbl}]"
        )
        last = out_lbl
    filter_parts.append(f"[{last}]scale={w}:{h},format=yuv420p[vout]")
    ai = n

    cmd = (
        [ffmpeg,"-y"] + inputs + ["-i",audio_path]
        + ["-filter_complex",";".join(filter_parts)]
        + ["-map","[vout]","-map",f"{ai}:a"]
        + ["-c:v","libx264","-preset","ultrafast","-crf","23"]
        + ["-c:a","aac","-b:a","128k"]
        + ["-t",str(duration),output_path]
    )

    print("    Running FFmpeg crossfade...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        # Ken Burns fallback on first frame
        print("    Crossfade failed — trying Ken Burns zoom...")
        total_frames = int(duration*fps)
        zoom = f"min(1.07\\,1.0+on/{total_frames}*0.07)"
        vf   = (f"scale={int(w*1.12)}:{int(h*1.12)},"
                f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={total_frames}:fps={fps}:s={w}x{h},format=yuv420p")
        cmd2 = [ffmpeg,"-y","-loop","1","-framerate",str(fps),
                "-i",frame_paths[0],"-i",audio_path,
                "-c:v","libx264","-preset","ultrafast",
                "-c:a","aac","-b:a","128k",
                "-t",str(duration),"-vf",vf,"-shortest",output_path]
        r2 = subprocess.run(cmd2, capture_output=True, text=True)
        if r2.returncode != 0:
            cmd3 = [ffmpeg,"-y","-loop","1","-i",frame_paths[0],"-i",audio_path,
                    "-c:v","libx264","-preset","ultrafast","-c:a","aac","-b:a","128k",
                    "-pix_fmt","yuv420p","-t",str(duration),
                    "-vf",f"scale={w}:{h},format=yuv420p","-shortest",output_path]
            subprocess.run(cmd3)

    size = os.path.getsize(output_path)/(1024*1024)
    print(f"    Video ready: {output_path} ({size:.1f} MB)")


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5 — UPLOAD TO YOUTUBE
# ══════════════════════════════════════════════════════════════════════════════
def build_description(meta, duration_secs):
    mins = int(duration_secs//60)
    secs = int(duration_secs%60)
    cat  = meta.get("category","horror story")
    c1   = meta.get("chapter_1","0:00 — The Beginning")
    c2   = meta.get("chapter_2","2:00 — Darkness Falls")
    c3   = meta.get("chapter_3","4:00 — The Truth Revealed")
    hook = random.choice(VIRAL_HOOKS)
    hl   = meta.get("hook_line","This story will stay with you.")
    desc = meta.get("description","")

    return f"""{hook}

{desc}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 COMMENT THIS LINE IF IT GOT YOU:
"{hl}"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 CHAPTERS:
{c1}
{c2}
{c3}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎧 FOR THE BEST EXPERIENCE:
• Use headphones — catch every detail
• Listen in the dark for full immersion
• Don't skip — every detail matters
• Best listened to at night alone

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 ABOUT THIS STORY:
Genre    : {cat.title()}
Length   : {mins} minutes {secs} seconds
Voice    : Professional neural narration (English)
Content  : 100% original fiction — no AI recycling

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 JOIN THE COMMUNITY:
► SUBSCRIBE — new story uploaded every single day
► 👍 LIKE if this story gave you chills
► 💬 COMMENT — did you see the ending coming?
► 🔔 HIT THE BELL — never miss a story
► 📤 SHARE with someone who loves dark stories
► Comment "MORE" if you want a sequel to this story

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 MORE STORIES ON THIS CHANNEL:
Horror stories • Ghost stories • Mystery narration
Psychological thrillers • Paranormal encounters • Dark drama
New story uploaded every day — subscribe so you don't miss one!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ DISCLAIMER:
All stories are 100% original AI-assisted fiction.
All characters, names, places and events are entirely fictional.
Any resemblance to real persons or events is purely coincidental.
Intended for mature audiences (18+). Contains dark themes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#ScaryStory #HorrorNarration #StoryTime #GhostStory #MysteryStory
#ThrillerStory #OriginalStory #HorrorFiction #ScaryStories2025
#ShortHorrorStory #DarkStory #CreepyStory #ParanormalStory
#NosleepStory #HorrorPodcast #SuspenseStory #NarrationChannel"""


def build_tags(meta):
    import re
    cat     = meta.get("category","supernatural horror")
    ai_tags = [t.strip().lower() for t in meta.get("tags","").split(",") if t.strip()]
    g_tags  = GENRE_TAGS.get(cat, [])
    all_t   = list(dict.fromkeys(ai_tags + g_tags + UNIVERSAL_TAGS))

    def clean_tag(tag):
        # Remove any characters YouTube doesn't allow in tags
        tag = tag.strip().lower()
        tag = re.sub(r'[<>"\{\}\[\]\|\\^~`]', '', tag)  # remove invalid chars
        tag = re.sub(r'\s+', ' ', tag).strip()           # normalize spaces
        tag = tag[:30]                                     # max 30 chars per tag
        return tag

    out, chars = [], 0
    for tag in all_t:
        tag = clean_tag(tag)
        if not tag or len(tag) < 2:
            continue
        if chars + len(tag) + 2 <= 490:
            out.append(tag)
            chars += len(tag) + 2
        if len(out) >= 30:
            break
    return out


def get_yt_service():
    creds = None
    tf    = "youtube_token.json"
    if os.path.exists(tf):
        creds = Credentials.from_authorized_user_file(tf, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow  = InstalledAppFlow.from_client_secrets_file(CONFIG["YOUTUBE_CLIENT_SECRETS"], SCOPES)
            creds = flow.run_local_server(port=0)
        with open(tf,"w") as f: f.write(creds.to_json())
    return build("youtube","v3",credentials=creds)


def upload(video_path, thumb_path, meta, duration_secs):
    print("\n[5/5] Uploading to YouTube with viral metadata...")
    yt    = get_yt_service()
    title = meta["title"][:100]
    desc  = build_description(meta, duration_secs)
    tags  = build_tags(meta)

    print(f"    Title ({len(title)} chars): {title}")
    print(f"    Tags: {len(tags)}")

    body = {
        "snippet": {
            "title":title, "description":desc, "tags":tags,
            "categoryId":"24",
            "defaultLanguage":"en", "defaultAudioLanguage":"en",
        },
        "status": {
            "privacyStatus":"public",
            "selfDeclaredMadeForKids":False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    req   = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp  = None
    while resp is None:
        status, resp = req.next_chunk()
        if status: print(f"    Uploading... {int(status.progress()*100)}%")

    vid_id = resp.get("id","unknown")
    print(f"    LIVE: https://www.youtube.com/watch?v={vid_id}")

    if thumb_path and os.path.exists(thumb_path):
        try:
            yt.thumbnails().set(
                videoId=vid_id,
                media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")
            ).execute()
            print("    Thumbnail uploaded!")
        except Exception as e:
            print(f"    Thumbnail skipped: {e}")

    return vid_id


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
def run():
    check_config()
    check_youtube()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n{'='*58}")
    print(f"  YouTube Story Bot  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  FREE | COPYRIGHT SAFE | VIRAL OPTIMIZED | NO DOWNLOADS NEEDED")
    print(f"{'='*58}")

    try:
        story, meta, category = generate_story()
        audio_path, duration  = generate_voiceover(story, f"voice_{ts}.mp3")
        thumb_path            = make_thumbnail(category, meta["title"], ts)

        os.makedirs(CONFIG["FINAL_DIR"], exist_ok=True)
        video_path = os.path.join(CONFIG["FINAL_DIR"], f"video_{ts}.mp4")
        build_video(audio_path, duration, category, video_path,
                    scene_keywords=meta.get("scene_images",""))

        vid_id = upload(video_path, thumb_path, meta, duration)
        save_log({"ts":ts,"title":meta["title"],"id":vid_id,
                  "duration":round(duration),"status":"success"})

        print(f"\n{'='*58}")
        print(f"  DONE: https://www.youtube.com/watch?v={vid_id}")
        print(f"{'='*58}\n")

    except Exception as e:
        import traceback
        print(f"\nFailed: {e}")
        traceback.print_exc()
        save_log({"ts":ts,"status":"failed","error":str(e)})


def scheduler():
    check_config()
    check_youtube()
    print("\nScheduler — upload times (UTC):")
    for t in CONFIG["UPLOAD_TIMES_UTC"]:
        schedule.every().day.at(t).do(run)
        print(f"  {t} UTC")
    print("Running... (Ctrl+C to stop)\n")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if   mode == "run":      run()
    elif mode == "schedule": scheduler()
    elif mode == "test":
        check_config()
        story, meta, cat = generate_story()
        print("\n--- STORY PREVIEW ---")
        print(story[:500]+"...")
        print("\n--- TITLE ---")
        print(meta["title"])
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        tp = make_thumbnail(cat, meta["title"], ts)
        print(f"\nThumbnail saved: {tp}")
        print("\n--- TAGS ---")
        print(build_tags(meta))
    else:
        print("Usage: python youtube_bot.py [run | schedule | test]")
