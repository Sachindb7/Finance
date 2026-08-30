"""
Cloudinary Uploader Module
Uploads generated video to Cloudinary for a public URL.
Instagram Graph API requires a publicly accessible video URL.
"""

import cloudinary
import cloudinary.uploader

import config


def _configure_cloudinary():
    """Initialize Cloudinary with credentials from config."""
    cloudinary.config(
        cloud_name=config.CLOUDINARY_CLOUD_NAME,
        api_key=config.CLOUDINARY_API_KEY,
        api_secret=config.CLOUDINARY_API_SECRET,
        secure=True,
    )


def upload_video(video_path: str) -> dict:
    """
    Upload a video file to Cloudinary.

    Args:
        video_path: Local path to the video file.

    Returns:
        dict with keys:
            - "url": Public HTTPS URL of the uploaded video
            - "public_id": Cloudinary public ID (for deletion)
            - "duration": Video duration in seconds
    """
    _configure_cloudinary()

    print(f"☁️  Uploading to Cloudinary: {video_path}")

    result = cloudinary.uploader.upload(
        video_path,
        resource_type="video",
        folder="reel-generator",
        overwrite=True,
        # Eager transformation: ensure MP4 format
        eager=[{"format": "mp4"}],
        eager_async=False,
    )

    public_url = result.get("secure_url", result.get("url", ""))
    public_id = result.get("public_id", "")
    duration = result.get("duration", 0)

    print(f"✅ Uploaded! URL: {public_url}")
    print(f"   Public ID: {public_id} | Duration: {duration}s")

    return {
        "url": public_url,
        "public_id": public_id,
        "duration": duration,
    }


def delete_video(public_id: str) -> bool:
    """
    Delete a video from Cloudinary (cleanup after publishing).

    Args:
        public_id: Cloudinary public ID of the video.

    Returns:
        True if deletion was successful.
    """
    _configure_cloudinary()

    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="video")
        success = result.get("result") == "ok"
        if success:
            print(f"🗑️  Deleted from Cloudinary: {public_id}")
        else:
            print(f"⚠️  Cloudinary deletion result: {result}")
        return success
    except Exception as e:
        print(f"⚠️  Failed to delete from Cloudinary: {e}")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m modules.cloudinary_uploader <video_path>")
        sys.exit(1)

    info = upload_video(sys.argv[1])
    print(f"\nPublic URL: {info['url']}")
