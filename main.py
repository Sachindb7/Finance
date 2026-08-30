"""
Reel Generator — Main Entry Point
Automated Instagram Reel + YouTube Shorts generator.
Gemini -> Render -> (Optional: Upload -> Publish to YT/IG/Both)

Usage:
    python main.py generate                                     # Video only
    python main.py generate --topic "crypto scams"              # Custom topic
    python main.py publish --platform youtube                   # YT only
    python main.py publish --platform instagram                 # IG only
    python main.py publish --platform both                      # YT + IG
    python main.py publish --platform both --topic "startup"    # Custom + both
"""

import argparse
import sys
import os
from pathlib import Path

# Fix Windows terminal encoding for emoji/unicode output
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import config
from modules.script_generator import generate_story_slides
from modules.video_renderer import render_video


def cmd_generate(args) -> tuple:
    """Generate a reel video and save locally."""

    # Validate config
    errors = config.validate_for_generation()
    if errors:
        print("❌ Configuration errors:")
        for e in errors:
            print(f"   • {e}")
        print(f"\n💡 Copy .env.example to .env and fill in your keys.")
        print(f"   Add assets to: {config.ASSETS_DIR}")
        sys.exit(1)

    # Step 1: Generate story slides with Gemini
    print("\n" + "=" * 50)
    print("📝 STEP 1: Generating story script...")
    print("=" * 50)

    story = generate_story_slides(topic=args.topic)

    print(f"\n📖 Title: {story['title']}")
    for i, slide in enumerate(story["slides"], 1):
        print(f"   Slide {i}: {slide[:60]}...")

    # Step 2: Render video
    print("\n" + "=" * 50)
    print("🎬 STEP 2: Rendering video...")
    print("=" * 50)

    video_path = render_video(
        slides=story["slides"],
        slide_duration=args.slide_duration,
    )

    print(f"\n🎉 Video generated successfully!")
    print(f"   📁 File: {video_path}")

    # Save caption alongside video for later use
    caption_path = video_path.with_suffix(".txt")
    caption_path.write_text(story.get("caption", ""), encoding="utf-8")
    print(f"   📄 Caption: {caption_path}")

    return video_path, story


def _publish_to_youtube(video_path: Path, story: dict):
    """Publish video to YouTube Shorts."""
    print("\n" + "=" * 50)
    print("📺 Publishing to YouTube Shorts...")
    print("=" * 50)

    from modules.youtube_publisher import upload_short

    result = upload_short(
        video_path=str(video_path),
        title=story.get("yt_title", story["title"] + " #Shorts"),
        description=story.get("yt_description", story.get("caption", "")),
    )

    if result["success"]:
        print(f"\n✅ YouTube Short LIVE! {result['url']}")
    else:
        print(f"\n❌ YouTube upload failed: {result['message']}")

    return result


def _publish_to_instagram(video_path: Path, story: dict):
    """Upload to Cloudinary and publish to Instagram."""
    print("\n" + "=" * 50)
    print("☁️  Uploading to Cloudinary...")
    print("=" * 50)

    from modules.cloudinary_uploader import upload_video, delete_video

    upload_info = upload_video(str(video_path))
    video_url = upload_info["url"]

    print("\n" + "=" * 50)
    print("📸 Publishing to Instagram...")
    print("=" * 50)

    from modules.instagram_publisher import publish_reel

    result = publish_reel(
        video_url=video_url,
        caption=story.get("caption", ""),
    )

    if result["success"]:
        print(f"\n✅ Instagram Reel LIVE! Post ID: {result['post_id']}")
        # Cleanup Cloudinary
        print("🧹 Cleaning up Cloudinary...")
        delete_video(upload_info["public_id"])
    else:
        print(f"\n❌ Instagram publish failed: {result['message']}")
        print(f"   Video still available at: {video_url}")

    return result


def cmd_publish(args):
    """Generate a reel and publish to selected platform(s)."""
    platform = args.platform

    # Validate config based on platform
    if platform in ("instagram", "both"):
        errors = config.validate_for_publish()
        if errors:
            print("❌ Instagram configuration errors:")
            for e in errors:
                print(f"   • {e}")
            sys.exit(1)

    if platform in ("youtube", "both"):
        errors = config.validate_for_youtube()
        if errors:
            print("❌ YouTube configuration errors:")
            for e in errors:
                print(f"   • {e}")
            sys.exit(1)

    # Step 1 & 2: Generate video
    video_path, story = cmd_generate(args)

    results = {}

    # Publish to YouTube
    if platform in ("youtube", "both"):
        results["youtube"] = _publish_to_youtube(video_path, story)

    # Publish to Instagram
    if platform in ("instagram", "both"):
        results["instagram"] = _publish_to_instagram(video_path, story)

    # Summary
    print("\n" + "=" * 50)
    print("📊 PUBLISH SUMMARY")
    print("=" * 50)

    all_success = True
    for plat, res in results.items():
        status = "✅ SUCCESS" if res["success"] else "❌ FAILED"
        print(f"   {plat.upper()}: {status}")
        if not res["success"]:
            all_success = False

    if all_success:
        print("\n🎉🎉🎉 All platforms published successfully! 🎉🎉🎉")
    else:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="🎬 Automated Reel Generator — YouTube Shorts + Instagram Reels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py generate                                    Generate video only
  python main.py generate --topic "crypto scams"             Custom topic
  python main.py publish --platform youtube                  YouTube Short
  python main.py publish --platform instagram                Instagram Reel
  python main.py publish --platform both                     Both platforms
  python main.py publish --platform both --topic "startups"  Custom + both
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate reel video (save locally)")
    gen_parser.add_argument(
        "--topic", type=str, default=None,
        help=f"Story topic/niche (default: '{config.DEFAULT_TOPIC}')",
    )
    gen_parser.add_argument(
        "--slide-duration", type=float, default=config.SLIDE_DURATION,
        help=f"Duration per slide in seconds (default: {config.SLIDE_DURATION})",
    )

    # Publish command
    pub_parser = subparsers.add_parser("publish", help="Generate + publish to platform(s)")
    pub_parser.add_argument(
        "--platform", type=str, choices=["youtube", "instagram", "both"],
        required=True, help="Platform to publish to",
    )
    pub_parser.add_argument(
        "--topic", type=str, default=None,
        help=f"Story topic/niche (default: '{config.DEFAULT_TOPIC}')",
    )
    pub_parser.add_argument(
        "--slide-duration", type=float, default=config.SLIDE_DURATION,
        help=f"Duration per slide in seconds (default: {config.SLIDE_DURATION})",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        print("\n💡 Quick start:")
        print("   1. Copy .env.example to .env and add your GEMINI_API_KEY")
        print(f"   2. Add gameplay video to: {config.BACKGROUNDS_DIR}")
        print(f"   3. Add background music to: {config.MUSIC_DIR}")
        print(f"   4. Add a bold font (.ttf) to: {config.FONTS_DIR}")
        print("   5. Run: python main.py generate")
        print("\n🔑 Platform setup:")
        print("   YouTube:   python -m modules.youtube_publisher --auth")
        print("   Instagram: Set INSTAGRAM_* keys in .env")
        sys.exit(0)

    print("🎬 Reel Generator v2 — YouTube Shorts + Instagram Reels")
    print("=" * 50)

    if args.command == "generate":
        cmd_generate(args)
    elif args.command == "publish":
        cmd_publish(args)


if __name__ == "__main__":
    main()
