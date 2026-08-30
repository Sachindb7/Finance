"""
Reel Generator — Configuration Module
Loads settings from .env file and provides centralized config.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")


# ===== Paths =====
ASSETS_DIR = PROJECT_ROOT / "assets"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
MUSIC_DIR = ASSETS_DIR / "music"
FONTS_DIR = ASSETS_DIR / "fonts"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Create directories if they don't exist
for d in [BACKGROUNDS_DIR, MUSIC_DIR, FONTS_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ===== API Keys =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Instagram (optional)
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID", "")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

# Cloudinary (optional)
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")


# ===== Video Settings =====
SLIDE_DURATION = float(os.getenv("SLIDE_DURATION", "5"))  # seconds per slide
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "30"))
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FONT_SIZE = int(os.getenv("FONT_SIZE", "46"))
FONT_COLOR = "white"
STROKE_COLOR = "black"
STROKE_WIDTH = 2
TEXT_MARGIN = 80  # px left/right padding
MUSIC_VOLUME = float(os.getenv("MUSIC_VOLUME", "0.15"))


# ===== Gemini Settings =====
GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_TOPIC = "Indian financial scams, dark money stories, and legendary Indian business origin stories"
NUM_SLIDES = 7  # Number of story slides to generate

# ===== History Tracking (for unique scripts) =====
HISTORY_FILE = PROJECT_ROOT / "generated_history.json"
MAX_HISTORY = 100  # Keep last N entries to avoid huge prompt

# ===== YouTube Settings =====
YOUTUBE_CLIENT_SECRET_FILE = PROJECT_ROOT / "client_secret.json"
YOUTUBE_TOKEN_FILE = PROJECT_ROOT / "token.json"
YOUTUBE_CATEGORY_ID = "22"  # "People & Blogs" (good for storytelling)
YOUTUBE_PRIVACY = os.getenv("YOUTUBE_PRIVACY", "public")  # public/private/unlisted


def validate_for_generation():
    """Validate that all required config for video generation is present."""
    errors = []

    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is not set. Add it to your .env file.")

    bg_files = list(BACKGROUNDS_DIR.glob("*.mp4"))
    if not bg_files:
        errors.append(
            f"No background videos found in {BACKGROUNDS_DIR}. "
            "Add at least one .mp4 gameplay video (9:16 vertical format)."
        )

    music_files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
    if not music_files:
        errors.append(
            f"No music files found in {MUSIC_DIR}. "
            "Add at least one .mp3 or .wav background music track."
        )

    font_files = list(FONTS_DIR.glob("*.ttf")) + list(FONTS_DIR.glob("*.otf"))
    if not font_files:
        errors.append(
            f"No font files found in {FONTS_DIR}. "
            "Add at least one .ttf or .otf bold font file (e.g., Montserrat-Bold.ttf)."
        )

    return errors


def validate_for_publish():
    """Validate that all required config for Instagram publishing is present."""
    errors = validate_for_generation()

    if not INSTAGRAM_USER_ID:
        errors.append("INSTAGRAM_USER_ID is not set.")
    if not INSTAGRAM_ACCESS_TOKEN:
        errors.append("INSTAGRAM_ACCESS_TOKEN is not set.")
    if not CLOUDINARY_CLOUD_NAME:
        errors.append("CLOUDINARY_CLOUD_NAME is not set.")
    if not CLOUDINARY_API_KEY:
        errors.append("CLOUDINARY_API_KEY (Cloudinary) is not set.")
    if not CLOUDINARY_API_SECRET:
        errors.append("CLOUDINARY_API_SECRET is not set.")

    return errors


def validate_for_youtube():
    """Validate that all required config for YouTube publishing is present."""
    errors = validate_for_generation()

    if not YOUTUBE_CLIENT_SECRET_FILE.exists():
        errors.append(
            f"YouTube client_secret.json not found at {YOUTUBE_CLIENT_SECRET_FILE}. "
            "Download it from Google Cloud Console > APIs & Services > Credentials."
        )
    if not YOUTUBE_TOKEN_FILE.exists():
        errors.append(
            f"YouTube token.json not found. Run: python -m modules.youtube_publisher --auth"
        )

    return errors
