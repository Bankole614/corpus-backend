"""
Corpus Vault Image Optimizer & Converter (with Smart-Skip).

Features:
1. Smart-Skip: Skips already-optimized JPEGs (<= 1200px and lightweight) to avoid
   repeated re-compression quality loss.
2. Auto-converts new external AI downloads (.png, .webp, .jpeg) into clean .jpg files.
3. Automatically deletes heavy raw .png files after conversion.
4. Downscales any oversized images (> 1200px) with high-fidelity Lanczos resampling.
5. Re-encodes with MozJPEG-style progressive compression and Huffman optimization.
6. Optional --force flag to re-optimize every image regardless of status.

Usage:
    python scripts/optimize_vault_images.py
    python scripts/optimize_vault_images.py --force
"""

import os
import argparse
from pathlib import Path
from PIL import Image

VAULT_DIR = Path("app/static/vault")

# Threshold: images under 260 KB and within 1200px are considered already optimized
OPTIMIZED_SIZE_THRESHOLD_KB = 260

def process_and_optimize(max_dim=1200, jpeg_quality=82, force=False):
    if not VAULT_DIR.exists():
        print(f"[!] Directory not found: {VAULT_DIR}")
        return

    all_files = sorted(
        [p for p in VAULT_DIR.glob("*") if p.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"] and p.is_file()]
    )
    print(f"Scanning {VAULT_DIR}... Found {len(all_files)} total images.")

    converted_pngs = 0
    resized_count = 0
    optimized_count = 0
    skipped_count = 0
    total_saved_bytes = 0

    for p in all_files:
        is_png = p.suffix.lower() == ".png"
        is_non_standard = p.suffix.lower() in [".png", ".jpeg", ".webp"]
        target_jpg = p.with_suffix(".jpg")
        orig_size = p.stat().st_size
        orig_kb = orig_size / 1024

        try:
            with Image.open(p) as img:
                w, h = img.size
                is_oversized = max(w, h) > max_dim

                # Smart-Skip check: If already a JPG, not oversized, and reasonably small
                if not force and not is_non_standard and not is_oversized and orig_kb <= OPTIMIZED_SIZE_THRESHOLD_KB:
                    skipped_count += 1
                    continue

                # Convert to RGB (handles transparency in PNGs)
                if img.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", img.size, (10, 10, 10))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    bg.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
                    img = bg
                else:
                    img = img.convert("RGB")

                # Downscale if oversized
                if is_oversized:
                    scale = max_dim / max(w, h)
                    new_w, new_h = int(w * scale), int(h * scale)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    resized_count += 1

                # Save as progressive optimized JPEG
                img.save(target_jpg, "JPEG", quality=jpeg_quality, optimize=True, progressive=True)

            new_size = target_jpg.stat().st_size
            optimized_count += 1

            # Delete original PNG/WEBP/JPEG after successful conversion to .jpg
            if is_non_standard and target_jpg.exists() and new_size > 0:
                p.unlink()
                if is_png:
                    converted_pngs += 1
                total_saved_bytes += (orig_size - new_size)
                print(f"  [CONVERTED] {p.name} ({orig_kb:.0f}KB) -> {target_jpg.name} ({new_size/1024:.0f}KB)")
            elif orig_size > new_size:
                total_saved_bytes += (orig_size - new_size)

        except Exception as e:
            print(f"  [!] Error processing {p.name}: {e}")

    # Summary
    final_jpgs = sorted(VAULT_DIR.glob("*.jpg"))
    total_mb = sum(f.stat().st_size for f in final_jpgs) / (1024 * 1024)
    avg_kb = sum(f.stat().st_size for f in final_jpgs) / len(final_jpgs) / 1024 if final_jpgs else 0

    print("\n" + "="*55)
    print("VAULT IMAGE OPTIMIZATION COMPLETE:")
    print(f"  Total JPG Assets in Vault : {len(final_jpgs)}")
    print(f"  Already Optimized (Skipped): {skipped_count}")
    print(f"  Newly Processed / Re-saved : {optimized_count}")
    print(f"  PNGs Converted & Cleaned   : {converted_pngs}")
    print(f"  Oversized Images Resized   : {resized_count}")
    print(f"  Current Total Folder Size  : {total_mb:.2f} MB")
    print(f"  Average Size Per Image     : {avg_kb:.1f} KB")
    print("="*55)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-dim", type=int, default=1200, help="Max width/height (default 1200)")
    parser.add_argument("--quality", type=int, default=82, help="JPEG quality (default 82)")
    parser.add_argument("--force", action="store_true", help="Force re-optimize all images regardless of size")
    args = parser.parse_args()

    process_and_optimize(max_dim=args.max_dim, jpeg_quality=args.quality, force=args.force)
