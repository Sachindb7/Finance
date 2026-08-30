"""
Script Generator Module
Uses Gemini API to generate UNIQUE story slides for Instagram Reels / YouTube Shorts.
Tracks generation history to prevent repetitive content.
"""

import json
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

import config


def _load_history() -> list[dict]:
    """Load generation history from JSON file."""
    if config.HISTORY_FILE.exists():
        try:
            data = json.loads(config.HISTORY_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, Exception):
            return []
    return []


def _save_history(history: list[dict]):
    """Save generation history, keeping only last MAX_HISTORY entries."""
    # Keep only recent entries to avoid bloating the prompt
    trimmed = history[-config.MAX_HISTORY:]
    config.HISTORY_FILE.write_text(
        json.dumps(trimmed, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _get_past_titles(history: list[dict]) -> list[str]:
    """Extract past story titles from history."""
    return [entry.get("title", "") for entry in history if entry.get("title")]


def generate_story_slides(topic: str = None, num_slides: int = None) -> dict:
    """
    Generate UNIQUE story slides using Gemini API.
    Uses history tracking to prevent repetition.

    Args:
        topic: Story topic/niche (e.g., "Indian financial scams").
                Defaults to config.DEFAULT_TOPIC.
        num_slides: Number of slides to generate. Defaults to config.NUM_SLIDES.

    Returns:
        dict with keys:
            - "slides": List[str] — each string is one slide's text
            - "title": str — short title for the story
            - "caption": str — Instagram caption with hashtags
    """
    topic = topic or config.DEFAULT_TOPIC
    num_slides = num_slides or config.NUM_SLIDES

    # Load history to avoid repetition
    history = _load_history()
    past_titles = _get_past_titles(history)

    client = genai.Client(api_key=config.GEMINI_API_KEY)

    # Build anti-repetition instruction
    avoid_section = ""
    if past_titles:
        titles_list = "\n".join(f"  - {t}" for t in past_titles[-30:])  # Last 30
        avoid_section = f"""

CRITICAL — DO NOT REPEAT:
The following stories have already been generated. You MUST create a COMPLETELY DIFFERENT story
with different characters, different cities, different amounts, and a different plot:
{titles_list}

Pick a totally new angle, new scam type, new era, new location. Be creative and original."""

    prompt = f"""You are a viral Instagram Reels / YouTube Shorts storyteller for an Indian audience.
Your content covers TWO niches (randomly pick one for this video):
  1. DARK INDIAN SCAM STORIES: Financial frauds, Ponzi schemes, corporate scams, cyber crimes, dark money
  2. INDIAN BUSINESS ORIGIN STORIES: Rags-to-riches, ₹0 se empire, underdog founders, legendary hustlers

Topic/Niche hint: "{topic}"
{avoid_section}

LANGUAGE STYLE — Randomly pick ONE of these two styles for this video:
  Style A (HINGLISH): Full Hindi-English mix. Like a dost telling a story. Example:
    "Tu jo Zomato se khaana order karta hai na? Usmein se ₹87 ek scam mein jaata hai."
  Style B (ENGLISH + HINGLISH MIX): English base with Hindi emotional punches. Example:
    "You're sleeping right now and someone is taking a ₹30 lakh loan on YOUR Aadhaar card. Aaj 14,000 logon ke saath hua hai."

HOOK RULES (MOST IMPORTANT):
- Slide 1 MUST be a "MUST SEE" hook, not a "nice to see" hook.
- "Must see" means the viewer feels PERSONALLY attacked or involved. Create an information gap they NEED to close.
- BAD hook: "Ek aadmi ne ₹200 Crore loote" (interesting but skippable)
- GOOD hook: "Tu jo Zomato se khaana khaata hai, usmein scam hai" (PERSONAL, can't scroll past)
- GOOD hook: "Tere jeb mein jo cheez hai, wo ISI aadmi ne banayi" (CURIOSITY gap)
- The hook must make the viewer think "yeh toh mujhse related hai, dekhna padega"

SLIDE RULES:
- Total slides: exactly {num_slides}
- Each slide: 2-4 SHORT lines (max 12-15 words per line)
- Use SPECIFIC details: real-sounding names, exact amounts (₹ with Crore/Lakh), cities, years
- Don't overuse em dashes. Use periods and short punchy sentences instead.
- Build tension slide by slide. Middle slides should reveal shocking twists.
- Last slide MUST be a gut-punch ending: a thought-provoking line, a dark irony, or a call that hits emotionally.
- Vary the tone across videos: sometimes thriller, sometimes emotional, sometimes investigative, sometimes darkly funny.

OUTPUT FORMAT — Return a JSON object with this exact structure:
{{
    "title": "Short catchy title (5-8 words)",
    "slides": ["Slide 1 text...", "Slide 2 text...", ...],
    "caption": "Instagram/YouTube caption with emojis and 15-20 relevant hashtags. Mix of Hindi and English hashtags.",
    "yt_title": "YouTube Shorts title (catchy, under 70 chars, include #Shorts)",
    "yt_description": "YouTube description with relevant tags and 2-3 line summary"
}}"""

    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=1.0,  # Maximum creativity
        ),
    )

    result = json.loads(response.text)

    # Validate structure
    if not isinstance(result.get("slides"), list):
        raise ValueError("Gemini response missing 'slides' array")
    if len(result["slides"]) < 3:
        raise ValueError(f"Too few slides generated: {len(result['slides'])}")

    # Ensure yt_title and yt_description exist (backward compat)
    if "yt_title" not in result:
        result["yt_title"] = result.get("title", "Story Time") + " #Shorts"
    if "yt_description" not in result:
        result["yt_description"] = result.get("caption", "")

    # Save to history
    history.append({
        "title": result.get("title", "Untitled"),
        "topic": topic,
        "slides_count": len(result["slides"]),
        "generated_at": datetime.now().isoformat(),
    })
    _save_history(history)

    print(f"✅ Generated {len(result['slides'])} slides: \"{result.get('title', 'Untitled')}\"")
    print(f"   (History: {len(history)} unique stories generated so far)")
    return result


if __name__ == "__main__":
    # Quick test
    story = generate_story_slides("Indian startup scams that shocked everyone")
    for i, slide in enumerate(story["slides"], 1):
        print(f"\n--- Slide {i} ---")
        print(slide)
    print(f"\n📝 Caption: {story['caption'][:100]}...")
    print(f"🎬 YT Title: {story['yt_title']}")
