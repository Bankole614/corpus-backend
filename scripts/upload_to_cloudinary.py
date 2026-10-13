"""
Utility script to batch upload all vault images from app/static/vault/ to Cloudinary.

Prerequisites:
  pip install cloudinary

Environment variables (or set in .env):
  CLOUDINARY_CLOUD_NAME=your_cloud_name
  CLOUDINARY_API_KEY=your_api_key
  CLOUDINARY_API_SECRET=your_api_secret

Usage:
  python scripts/upload_to_cloudinary.py
"""

import os
import glob
from pathlib import Path

def upload_all():
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")

    if not all([cloud_name, api_key, api_secret]):
        print("[!] Cloudinary credentials missing. Please set in your .env or environment:")
        print("    CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET")
        return

    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError:
        print("[!] cloudinary package not installed. Run: pip install cloudinary")
        return

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True
    )

    vault_dir = Path("app/static/vault")
    images = sorted(vault_dir.glob("*.jpg"))
    print(f"Found {len(images)} images in {vault_dir} to upload to Cloudinary...")

    url_mapping = {}
    for img_path in images:
        public_id = f"corpus/vault/{img_path.stem}"
        print(f"Uploading {img_path.name} as {public_id}...")
        try:
            res = cloudinary.uploader.upload(
                str(img_path),
                public_id=public_id,
                overwrite=True,
                resource_type="image"
            )
            url_mapping[img_path.name] = res.get("secure_url")
            print(f"  [OK] -> {res.get('secure_url')}")
        except Exception as e:
            print(f"  [X] Failed: {e}")

    print("\nUpload complete! You can copy the generated CDN URLs.")

if __name__ == "__main__":
    upload_all()
