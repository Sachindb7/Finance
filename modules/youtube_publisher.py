"""
YouTube Publisher Module
Uses Google YouTube Data API v3 to upload videos as YouTube Shorts.
Requires: Google Cloud project with YouTube Data API enabled + OAuth2 credentials.
"""

import json
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config

# YouTube API scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_authenticated_service():
    """
    Build an authenticated YouTube API service.
    Uses stored token.json, refreshes if expired, or runs OAuth flow if no token.
    """
    creds = None

    # Load existing token
    if config.YOUTUBE_TOKEN_FILE.exists():
        token_data = json.loads(config.YOUTUBE_TOKEN_FILE.read_text(encoding="utf-8"))
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)

    # Refresh or re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing YouTube access token...")
            creds.refresh(Request())
        else:
            if not config.YOUTUBE_CLIENT_SECRET_FILE.exists():
                raise FileNotFoundError(
                    f"client_secret.json not found at {config.YOUTUBE_CLIENT_SECRET_FILE}\n"
                    "Download it from Google Cloud Console > APIs & Services > Credentials."
                )
            print("🔐 Opening browser for YouTube authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.YOUTUBE_CLIENT_SECRET_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for future use
        config.YOUTUBE_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        print(f"✅ Token saved to {config.YOUTUBE_TOKEN_FILE}")

    return build("youtube", "v3", credentials=creds)


def upload_short(
    video_path: str,
    title: str,
    description: str,
    tags: list[str] = None,
    category_id: str = None,
    privacy: str = None,
) -> dict:
    """
    Upload a video as a YouTube Short.

    Args:
        video_path: Local path to the video file.
        title: Video title (should include #Shorts for discoverability).
        description: Video description.
        tags: List of tags/keywords.
        category_id: YouTube category ID. Defaults to config.
        privacy: Privacy status (public/private/unlisted). Defaults to config.

    Returns:
        dict with keys:
            - "video_id": YouTube video ID
            - "url": Full YouTube URL
            - "success": bool
            - "message": Status message
    """
    category_id = category_id or config.YOUTUBE_CATEGORY_ID
    privacy = privacy or config.YOUTUBE_PRIVACY

    # Ensure #Shorts is in the title for YouTube Shorts discovery
    if "#Shorts" not in title and "#shorts" not in title:
        title = f"{title} #Shorts"

    # Truncate title to YouTube's 100 char limit
    if len(title) > 100:
        title = title[:96] + "..."

    try:
        youtube = _get_authenticated_service()
    except Exception as e:
        return {
            "video_id": None,
            "url": None,
            "success": False,
            "message": f"YouTube authentication failed: {e}",
        }

    print(f"📤 Uploading to YouTube: {title}")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 5,  # 5MB chunks
    )

    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        # Upload with progress
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"   Upload progress: {progress}%")

        video_id = response["id"]
        video_url = f"https://youtube.com/shorts/{video_id}"

        print(f"✅ YouTube Short published! {video_url}")

        return {
            "video_id": video_id,
            "url": video_url,
            "success": True,
            "message": "YouTube Short published successfully!",
        }

    except Exception as e:
        return {
            "video_id": None,
            "url": None,
            "success": False,
            "message": f"YouTube upload failed: {e}",
        }


def authenticate():
    """Run the one-time OAuth2 authentication flow."""
    print("=" * 50)
    print("YouTube Authentication Setup")
    print("=" * 50)
    print(f"\nLooking for: {config.YOUTUBE_CLIENT_SECRET_FILE}")

    if not config.YOUTUBE_CLIENT_SECRET_FILE.exists():
        print(
            "\n❌ client_secret.json not found!\n"
            "\nTo set up YouTube API:\n"
            "1. Go to https://console.cloud.google.com/\n"
            "2. Create a project (or select existing)\n"
            "3. Enable 'YouTube Data API v3'\n"
            "4. Go to APIs & Services > Credentials\n"
            "5. Create OAuth 2.0 Client ID (Desktop Application)\n"
            "6. Download JSON and save as 'client_secret.json' in project root\n"
            "7. Run this command again"
        )
        sys.exit(1)

    try:
        service = _get_authenticated_service()
        print("\n✅ Authentication successful! token.json saved.")
        print("   You can now use: python main.py publish --platform youtube")
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if "--auth" in sys.argv:
        authenticate()
    else:
        print("Usage:")
        print("  python -m modules.youtube_publisher --auth    # One-time auth setup")
        print("  (Upload is handled via main.py)")
