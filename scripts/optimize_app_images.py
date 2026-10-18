"""
Corpus — Comprehensive Image Optimizer & Converter (with Smart-Skip).

Optimizes all newly generated images for Corpus across:
1. Onboarding & Home Screen Cards (`assets/images/` or `app/static/ui/`)
2. Taste Profile Deck (`app/static/deck/`)
3. The Vault (`app/static/vault/`)
4. Any custom directory provided via `--dir`

Features:
- Smart-Skip: Skips already-optimized JPEGs to prevent generational compression loss.
- Auto-converts AI downloads (.png, .webp, .jpeg) into standardized progressive .jpg files.
- Automatically cleans up heavy raw .png/.webp files after successful conversion.
- Intelligently scales while preserving native aspect ratios:
    * Vertical Onboarding (9:16): scaled to max height 1920px (width ~1080px).
    * Home Screen Landscape/Portrait (16:9, 4:3, 3:4): scaled to max dimension 1200px.
    * Square Cards / Deck / Vault (1:1): scaled to max dimension 1200px.
- Blends any transparency into Corpus ink-obsidian `#16151A` (or `#0a0a0a`).
- Re-encodes with progressive encoding and Huffman optimization for instant mobile loading.

Usage:
    python scripts/optimize_app_images.py
    python scripts/optimize_app_images.py --dir assets/images
    python scripts/optimize_app_images.py --dir app/static/deck
    python scripts/optimize_app_images.py --force
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image

DEFAULT_SCAN_DIRS = [
    Path("assets/images"),
    Path("app/static/ui"),
    Path("app/static/deck"),
    Path("app/static/vault"),
]

# Background fill for transparent PNGs (Corpus ink-obsidian #16151A)
OBSIDIAN_BG_COLOR = (22, 21, 26)

# Threshold: images under 280 KB and within bounds are considered already optimized
OPTIMIZED_SIZE_THRESHOLD_KB = 280


def optimize_directory(directory: Path, jpeg_quality: int = 83, force: bool = False):
    if not directory.exists():
        return None

    all_files = sorted(
        [
            p for p in directory.glob("*")
            if p.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"] and p.is_file()
        ]
    )

    if not all_files:
        return None

    print(f"\n========================================================")
    print(f"Scanning directory: {directory} ({len(all_files)} images found)")
    print(f"========================================================")

    converted_count = 0
    resized_count = 0
    optimized_count = 0
    skipped_count = 0
    total_saved_bytes = 0

    for p in all_files:
        suffix = p.suffix.lower()
        is_non_standard = suffix in [".png", ".jpeg", ".webp"]
        target_jpg = p.with_suffix(".jpg")
        orig_size = p.stat().st_size
        orig_kb = orig_size / 1024

        try:
            with Image.open(p) as img:
                w, h = img.size

                # Determine max dimension based on filename / aspect ratio
                is_onboarding = "onboarding" in p.name.lower() or (h > w * 1.5)
                max_w = 1080 if is_onboarding else 1200
                max_h = 1920 if is_onboarding else 1200

                is_oversized = w > max_w or h > max_h

                # Smart-Skip check: If already a JPG, within bounds, and lightweight
                if not force and not is_non_standard and not is_oversized and orig_kb <= OPTIMIZED_SIZE_THRESHOLD_KB:
                    skipped_count += 1
                    continue

                # Handle transparency (convert RGBA/LA/P to RGB on obsidian background)
                if img.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", img.size, OBSIDIAN_BG_COLOR)
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    mask = img.split()[-1] if "A" in img.mode else None
                    bg.paste(img, mask=mask)
                    img = bg
                else:
                    img = img.convert("RGB")

                # Downscale if oversized, preserving aspect ratio
                if is_oversized:
                    scale = min(max_w / w, max_h / h)
                    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    resized_count += 1

                # Save as progressive optimized JPEG
                img.save(
                    target_jpg,
                    "JPEG",
                    quality=jpeg_quality,
                    optimize=True,
                    progressive=True
                )

            new_size = target_jpg.stat().st_size
            optimized_count += 1

            # Clean up raw PNG/WEBP after successful JPEG creation
            if is_non_standard and target_jpg.exists() and new_size > 0:
                p.unlink()
                converted_count += 1
                saved = orig_size - new_size
                total_saved_bytes += saved
                print(f"  [CONVERTED] {p.name} ({orig_kb:.0f} KB) -> {target_jpg.name} ({new_size/1024:.0f} KB) [-{saved/1024:.0f} KB]")
            elif orig_size > new_size:
                saved = orig_size - new_size
                total_saved_bytes += saved
                print(f"  [OPTIMIZED] {p.name} ({orig_kb:.0f} KB -> {new_size/1024:.0f} KB) [-{saved/1024:.0f} KB]")

        except Exception as e:
            print(f"  [!] Error processing {p.name}: {e}")

    # Directory report
    final_jpgs = sorted(directory.glob("*.jpg"))
    total_mb = sum(f.stat().st_size for f in final_jpgs) / (1024 * 1024)
    avg_kb = sum(f.stat().st_size for f in final_jpgs) / len(final_jpgs) / 1024 if final_jpgs else 0

    print(f"\n[Summary for {directory}]:")
    print(f"  * Skipped (already optimized): {skipped_count}")
    print(f"  * Resized:                     {resized_count}")
    print(f"  * Converted from PNG/WEBP:     {converted_count}")
    print(f"  * Total Active JPEGs:          {len(final_jpgs)}")
    print(f"  * Total Directory Size:        {total_mb:.2f} MB (Average: {avg_kb:.1f} KB/image)")
    if total_saved_bytes > 0:
        print(f"  * Net Storage Saved:           {total_saved_bytes / (1024 * 1024):.2f} MB")

    return len(final_jpgs)


def main():
    parser = argparse.ArgumentParser(description="Corpus Image Optimizer with Smart-Skip.")
    parser.add_argument("--dir", type=str, help="Specific directory to optimize (e.g. assets/images or app/static/deck)")
    parser.add_argument("--quality", type=int, default=83, help="JPEG quality 1-100 (default: 83)")
    parser.add_argument("--force", action="store_true", help="Force re-compression even if already optimized")

    args = parser.parse_args()

    targets = [Path(args.dir)] if args.dir else DEFAULT_SCAN_DIRS

    found_any = False
    for target in targets:
        result = optimize_directory(target, jpeg_quality=args.quality, force=args.force)
        if result is not None:
            found_any = True

    if not found_any:
        print("[!] No matching directories or images found to optimize.")
        print(f"Checked: {[str(d) for d in targets]}")
        print("\nTip: Create your target folder (e.g. 'assets/images' or 'app/static/ui') and drop your raw AI downloads inside, then run:")
        print("    python scripts/optimize_app_images.py --dir <your_folder>")


if __name__ == "__main__":
    main()
