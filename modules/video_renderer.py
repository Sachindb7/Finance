"""
Video Renderer Module
Uses MoviePy + Pillow to create Instagram Reels with text overlays on gameplay backgrounds.
Style: "Crores by Parth" — bold centered text slides over Minecraft/gameplay footage.

NOTE: Uses Pillow for text rendering (no ImageMagick dependency needed).
"""

import random
import shutil
import textwrap
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Fix Pillow 10+ compatibility with MoviePy 1.0.3
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import (
    VideoFileClip,
    ImageClip,
    CompositeVideoClip,
    AudioFileClip,
    ColorClip,
)

import config


def _check_ffmpeg():
    """Verify FFmpeg is accessible (system or bundled via imageio_ffmpeg)."""
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_path:
            return
    except Exception:
        pass

    if shutil.which("ffmpeg") is None:
        raise EnvironmentError(
            "FFmpeg not found! Install it:\n"
            "  Windows: winget install ffmpeg  OR  choco install ffmpeg\n"
            "  Or: pip install imageio-ffmpeg\n"
            "  Then restart your terminal."
        )


def _pick_random_file(directory: Path, extensions: list[str]) -> Path:
    """Pick a random file from directory matching given extensions."""
    files = []
    for ext in extensions:
        files.extend(directory.glob(f"*.{ext}"))
    if not files:
        raise FileNotFoundError(f"No files found in {directory} with extensions {extensions}")
    return random.choice(files)


def _get_font_path() -> str:
    """Get path to the first available font file."""
    font_file = _pick_random_file(config.FONTS_DIR, ["ttf", "otf"])
    return str(font_file)


def _render_text_image(
    text: str,
    width: int,
    height: int,
    font_path: str,
    font_size: int = 46,
    text_color: str = "white",
    stroke_color: str = "black",
    stroke_width: int = 2,
    margin: int = 80,
) -> np.ndarray:
    """
    Render text onto a transparent RGBA image using Pillow.
    Returns a numpy array (H, W, 4) suitable for MoviePy ImageClip.
    """
    # Create transparent image
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Load font
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()

    # Calculate available width for text
    available_width = width - 2 * margin

    # Word-wrap text to fit within available width
    lines = []
    for paragraph in text.split("\n"):
        # Try to wrap each paragraph
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            if line_width <= available_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

    # Calculate total text height
    line_spacing = int(font_size * 0.4)
    total_text_height = 0
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_text_height += h + line_spacing
    total_text_height -= line_spacing  # Remove last spacing

    # Start Y position (vertically centered)
    y = (height - total_text_height) // 2

    # Draw each line centered
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2

        # Draw stroke/outline
        if stroke_width > 0:
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), line, font=font, fill=stroke_color)

        # Draw main text
        draw.text((x, y), line, font=font, fill=text_color)

        y += line_heights[i] + line_spacing

    return np.array(img)


def render_video(
    slides: list[str],
    output_filename: str = None,
    slide_duration: float = None,
) -> Path:
    """
    Render a reel video with text slides over gameplay background.

    Args:
        slides: List of text strings, one per slide.
        output_filename: Custom output filename. Auto-generated if None.
        slide_duration: Seconds per slide. Defaults to config.SLIDE_DURATION.

    Returns:
        Path to the rendered video file.
    """
    _check_ffmpeg()

    slide_duration = slide_duration or config.SLIDE_DURATION
    total_duration = len(slides) * slide_duration

    # ===== 1. Load Background Video =====
    bg_path = _pick_random_file(config.BACKGROUNDS_DIR, ["mp4", "mkv", "webm"])
    print(f"🎮 Background: {bg_path.name}")

    bg_clip = VideoFileClip(str(bg_path))

    # If background is shorter than needed, loop it
    if bg_clip.duration < total_duration:
        loops_needed = int(total_duration / bg_clip.duration) + 1
        from moviepy.editor import concatenate_videoclips
        bg_clip = concatenate_videoclips([bg_clip] * loops_needed)

    bg_clip = bg_clip.subclip(0, total_duration)

    # Resize to 1080x1920 (9:16) if needed
    bg_clip = bg_clip.resize((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))

    # ===== 2. Create Text Overlays using Pillow =====
    text_clips = []
    font_path = _get_font_path()
    print(f"🔤 Font: {Path(font_path).name}")

    for i, slide_text in enumerate(slides):
        start_time = i * slide_duration

        # Semi-transparent dark overlay behind text for readability
        overlay = (
            ColorClip(
                size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
                color=(0, 0, 0),
            )
            .set_opacity(0.3)
            .set_start(start_time)
            .set_duration(slide_duration)
        )
        text_clips.append(overlay)

        # Render text as image using Pillow (no ImageMagick needed!)
        text_img = _render_text_image(
            text=slide_text,
            width=config.VIDEO_WIDTH,
            height=config.VIDEO_HEIGHT,
            font_path=font_path,
            font_size=config.FONT_SIZE,
            text_color=config.FONT_COLOR,
            stroke_color=config.STROKE_COLOR,
            stroke_width=config.STROKE_WIDTH,
            margin=config.TEXT_MARGIN,
        )

        txt_clip = (
            ImageClip(text_img, ismask=False, transparent=True)
            .set_start(start_time)
            .set_duration(slide_duration)
            .set_position(("center", "center"))
        )
        text_clips.append(txt_clip)

    # ===== 3. Composite Everything =====
    final_clip = CompositeVideoClip([bg_clip] + text_clips)

    # ===== 4. Add Background Music =====
    try:
        music_path = _pick_random_file(config.MUSIC_DIR, ["mp3", "wav", "m4a"])
        print(f"🎵 Music: {music_path.name}")

        music_clip = AudioFileClip(str(music_path))

        # Loop music if shorter than video
        if music_clip.duration < total_duration:
            from moviepy.editor import concatenate_audioclips
            loops_needed = int(total_duration / music_clip.duration) + 1
            music_clip = concatenate_audioclips([music_clip] * loops_needed)

        music_clip = music_clip.subclip(0, total_duration).volumex(config.MUSIC_VOLUME)
        final_clip = final_clip.set_audio(music_clip)
    except FileNotFoundError:
        print("⚠️  No background music found, rendering without music.")

    # ===== 5. Render Output =====
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"reel_{timestamp}.mp4"

    output_path = config.OUTPUT_DIR / output_filename
    print(f"🎬 Rendering video ({len(slides)} slides x {slide_duration}s = {total_duration}s)...")

    final_clip.write_videofile(
        str(output_path),
        fps=config.VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        logger="bar",
    )

    # Cleanup
    final_clip.close()
    bg_clip.close()

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"✅ Video saved: {output_path} ({file_size_mb:.1f} MB)")
    return output_path


if __name__ == "__main__":
    test_slides = [
        "In 2019, a 22-year-old boy\nfrom a small town in Bihar\nhad just ₹500 in his pocket...",
        "He created a fake fintech app\nthat promised 40% monthly returns.\nThousands invested blindly.",
        "Within 6 months,\nhe collected ₹47 Crore.\nNobody questioned him.",
        "The app had no real backend.\nJust a beautiful UI\nand fake transaction receipts.",
        "When investors tried to withdraw,\nthe app showed 'Server Maintenance'.\nFor 3 straight weeks.",
        "By the time police traced him,\nhe was living in Dubai\nunder a fake passport.",
        "₹47 Crore.\nZero accountability.\nAnd 12,000 families destroyed.\nThis happens every single day.",
    ]
    render_video(test_slides)
