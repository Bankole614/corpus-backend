"""
Corpus Vault — Cloudflare R2 Batch Uploader

Uploads all optimized JPEG images from `app/static/vault/` to a Cloudflare R2 bucket
using the S3-compatible API (boto3).

Prerequisites:
    pip install boto3

Environment Variables (add to your .env or export in shell):
    R2_ACCOUNT_ID=your_cloudflare_account_id
    R2_ACCESS_KEY_ID=your_r2_access_key_id
    R2_SECRET_ACCESS_KEY=your_r2_secret_access_key
    R2_BUCKET_NAME=corpus-vault
    R2_PUBLIC_URL=https://pub-xxxxxxxx.r2.dev  (or https://vault.yourdomain.com)

Usage:
    python scripts/upload_to_r2.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

VAULT_DIR = Path("app/static/vault")

def get_r2_client():
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        print("[!] boto3 is not installed. Run: pip install boto3")
        sys.exit(1)

    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key = os.getenv("R2_ACCESS_KEY_ID")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("R2_BUCKET_NAME")

    missing = []
    if not account_id: missing.append("R2_ACCOUNT_ID")
    if not access_key: missing.append("R2_ACCESS_KEY_ID")
    if not secret_key: missing.append("R2_SECRET_ACCESS_KEY")
    if not bucket_name: missing.append("R2_BUCKET_NAME")

    if missing:
        print(f"[!] Missing required environment variables: {', '.join(missing)}")
        print("\nPlease add them to your .env file or environment:")
        print("  R2_ACCOUNT_ID=<Cloudflare Account ID>")
        print("  R2_ACCESS_KEY_ID=<R2 Access Key ID>")
        print("  R2_SECRET_ACCESS_KEY=<R2 Secret Access Key>")
        print("  R2_BUCKET_NAME=<Your R2 Bucket Name>")
        print("  R2_PUBLIC_URL=https://<your-public-r2-domain-or-custom-domain>")
        sys.exit(1)

    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

    s3_client = boto3.client(
        service_name="s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(signature_version="s3v4")
    )
    return s3_client, bucket_name

def get_existing_r2_objects(s3, bucket_name):
    """Retrieve a dictionary of {key: size} for all objects currently in the bucket under vault/."""
    existing = {}
    paginator = s3.get_paginator("list_objects_v2")
    try:
        for page in paginator.paginate(Bucket=bucket_name, Prefix="vault/"):
            for obj in page.get("Contents", []):
                existing[obj["Key"]] = obj.get("Size", 0)
    except Exception as e:
        print(f"[*] Note: Could not pre-fetch bucket list ({e}). Will perform standard upload.")
    return existing

def upload_images(force=False):
    if not VAULT_DIR.exists():
        print(f"[!] Directory not found: {VAULT_DIR}")
        return

    # Check for known filename typos before upload
    typo_file = VAULT_DIR / "dagger_hear_2.jpg"
    if typo_file.exists():
        fixed_file = VAULT_DIR / "dagger_heart_2.jpg"
        print(f"[*] Fixing filename typo: {typo_file.name} -> {fixed_file.name}")
        typo_file.rename(fixed_file)

    images = sorted(VAULT_DIR.glob("*.jpg"))
    if not images:
        print(f"[!] No .jpg files found in {VAULT_DIR}")
        return

    s3, bucket_name = get_r2_client()
    public_base_url = os.getenv("R2_PUBLIC_URL", "").rstrip("/")

    # Fetch existing objects to enable Smart-Skip
    existing_objects = {} if force else get_existing_r2_objects(s3, bucket_name)
    if existing_objects and not force:
        print(f"[*] Found {len(existing_objects)} existing files already on R2. Smart-Skip enabled.")

    print(f"\n========================================================")
    print(f"  Uploading images to Cloudflare R2 bucket: '{bucket_name}'")
    if force:
        print(f"  Mode: FORCE OVERWRITE (all {len(images)} images)")
    print(f"========================================================\n")

    uploaded_count = 0
    skipped_count = 0
    fail_count = 0

    for idx, img_path in enumerate(images, 1):
        object_key = f"vault/{img_path.name}"
        local_size = img_path.stat().st_size

        # Smart-Skip check: If already on R2 and identical size, skip upload!
        if not force and object_key in existing_objects:
            if existing_objects[object_key] == local_size:
                skipped_count += 1
                continue

        try:
            with open(img_path, "rb") as f:
                s3.put_object(
                    Bucket=bucket_name,
                    Key=object_key,
                    Body=f,
                    ContentType="image/jpeg",
                    CacheControl="public, max-age=31536000, immutable"
                )
            uploaded_count += 1
            if public_base_url:
                url_str = f"{public_base_url}/{object_key}"
            else:
                url_str = object_key
            print(f"[{idx}/{len(images)}] [UPLOADED] {img_path.name} -> {url_str}")
        except Exception as e:
            fail_count += 1
            print(f"[{idx}/{len(images)}] [FAILED] {img_path.name}: {e}")

    print("\n--------------------------------------------------------")
    print(f"Upload Complete!")
    print(f"  Uploaded : {uploaded_count}")
    print(f"  Skipped  : {skipped_count} (already on R2)")
    print(f"  Failed   : {fail_count}")
    if public_base_url:
        print(f"\nYour vault images CDN base URL is:")
        print(f"  {public_base_url}/vault/\n")
    print("--------------------------------------------------------")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Upload vault images to Cloudflare R2 with Smart-Skip.")
    parser.add_argument("--force", action="store_true", help="Re-upload all images even if already present on R2.")
    args = parser.parse_args()

    upload_images(force=args.force)

