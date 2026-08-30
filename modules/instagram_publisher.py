"""
Instagram Publisher Module
Uses Meta Graph API to publish Reels to Instagram.
Requires: Business/Creator Instagram account linked to a Facebook Page.
"""

import time
import requests

import config


GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


def publish_reel(video_url: str, caption: str) -> dict:
    """
    Publish a Reel to Instagram using the Meta Graph API.

    3-step process:
    1. Create a media container with the video URL
    2. Poll until Meta finishes encoding the video
    3. Publish the container to your Instagram feed/reels

    Args:
        video_url: Publicly accessible HTTPS URL of the video.
        caption: Instagram caption (text + hashtags).

    Returns:
        dict with keys:
            - "post_id": Published Instagram post ID
            - "success": bool
            - "message": Status message
    """
    ig_user_id = config.INSTAGRAM_USER_ID
    access_token = config.INSTAGRAM_ACCESS_TOKEN

    if not ig_user_id or not access_token:
        return {
            "post_id": None,
            "success": False,
            "message": "Instagram credentials not configured. Set INSTAGRAM_USER_ID and INSTAGRAM_ACCESS_TOKEN in .env",
        }

    # ===== Step 1: Create Media Container =====
    print("📦 Step 1/3: Creating Reel container...")
    container_url = f"{GRAPH_API_BASE}/{ig_user_id}/media"
    container_payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": access_token,
    }

    res = requests.post(container_url, data=container_payload)
    container_data = res.json()

    if "id" not in container_data:
        error_msg = container_data.get("error", {}).get("message", str(container_data))
        return {
            "post_id": None,
            "success": False,
            "message": f"Failed to create container: {error_msg}",
        }

    container_id = container_data["id"]
    print(f"   Container ID: {container_id}")

    # ===== Step 2: Poll Until Encoding Finishes =====
    print("⏳ Step 2/3: Waiting for Meta to encode video...")
    status_url = f"{GRAPH_API_BASE}/{container_id}"
    max_wait = 300  # Max 5 minutes
    elapsed = 0
    poll_interval = 10  # Check every 10 seconds

    while elapsed < max_wait:
        status_res = requests.get(
            status_url,
            params={
                "fields": "status_code",
                "access_token": access_token,
            },
        ).json()

        status = status_res.get("status_code", "UNKNOWN")
        print(f"   Status: {status} ({elapsed}s elapsed)")

        if status == "FINISHED":
            break
        elif status == "ERROR":
            return {
                "post_id": None,
                "success": False,
                "message": "Video encoding failed on Meta's servers. Try re-uploading.",
            }

        time.sleep(poll_interval)
        elapsed += poll_interval

    if elapsed >= max_wait:
        return {
            "post_id": None,
            "success": False,
            "message": "Timed out waiting for video encoding (5 min limit).",
        }

    # ===== Step 3: Publish the Reel =====
    print("🚀 Step 3/3: Publishing Reel...")
    publish_url = f"{GRAPH_API_BASE}/{ig_user_id}/media_publish"
    publish_payload = {
        "creation_id": container_id,
        "access_token": access_token,
    }

    pub_res = requests.post(publish_url, data=publish_payload)
    pub_data = pub_res.json()

    if "id" in pub_data:
        post_id = pub_data["id"]
        print(f"✅ Reel Published Successfully! Post ID: {post_id}")
        return {
            "post_id": post_id,
            "success": True,
            "message": "Reel published successfully!",
        }
    else:
        error_msg = pub_data.get("error", {}).get("message", str(pub_data))
        return {
            "post_id": None,
            "success": False,
            "message": f"Publish failed: {error_msg}",
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m modules.instagram_publisher <video_url> <caption>")
        sys.exit(1)

    result = publish_reel(sys.argv[1], sys.argv[2])
    print(f"\nResult: {result}")
