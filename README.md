# Reel Generator — "Crores by Parth" Style

Automated Instagram Reel generator that creates text-slide storytelling videos over gameplay backgrounds.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

> **FFmpeg Required**: Install FFmpeg and add to PATH
> - Windows: `winget install ffmpeg` or `choco install ffmpeg`
> - Linux: `sudo apt install ffmpeg`

### 2. Configure

```bash
copy .env.example .env
```

Edit `.env` and add your **Gemini API Key** (required).
Instagram & Cloudinary keys are only needed for auto-publish.

### 3. Add Assets

| Folder | What to add |
|--------|-------------|
| `assets/backgrounds/` | 1+ gameplay videos (.mp4, 9:16 vertical) |
| `assets/music/` | 1+ background music tracks (.mp3) |
| `assets/fonts/` | 1+ bold font files (.ttf) |

### 4. Generate a Reel

```bash
# Generate video only (saved to output/)
python main.py generate

# Custom topic
python main.py generate --topic "crypto scams in India"

# Generate + publish to Instagram
python main.py publish
```

## 📁 Project Structure

```
reel-generator/
├── main.py                     # CLI entry point
├── config.py                   # Configuration & validation
├── modules/
│   ├── script_generator.py     # Gemini API → story slides
│   ├── video_renderer.py       # MoviePy → rendered video
│   ├── cloudinary_uploader.py  # Upload for public URL
│   └── instagram_publisher.py  # Meta Graph API → publish reel
├── assets/                     # Your media files
├── output/                     # Generated videos
└── .github/workflows/          # GitHub Actions automation
```

## 🔑 API Keys Needed

| Service | Required For | Get It |
|---------|-------------|--------|
| Gemini API | Script generation | [Google AI Studio](https://aistudio.google.com/apikey) |
| Instagram Graph API | Auto-publish | [Meta Developers](https://developers.facebook.com/) |
| Cloudinary | Video hosting | [Cloudinary](https://cloudinary.com/) (free tier) |

## 📸 Instagram Setup

1. Switch to Business/Creator account
2. Link to a Facebook Page
3. Create app at developers.facebook.com
4. Get `instagram_content_publish` permission
5. Generate long-lived access token
6. Get your IG Business Account ID
