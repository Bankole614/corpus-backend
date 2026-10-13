"""
Download and optimize images for the 13 Art Movements in The Vault.
Saves all 39 images into app/static/vault/ with uniform high quality and dimensions.
"""

import io
import os
import shutil
import httpx
from PIL import Image

USER_AGENT = "CorpusArtBot/1.0 (https://corpus.art; contact@corpus.art) httpx/0.27.0"
WIKI_API = "https://commons.wikimedia.org/w/api.php"
OUTPUT_DIR = "app/static/vault"
MAX_DIM = 1200
JPEG_QUALITY = 85

os.makedirs(OUTPUT_DIR, exist_ok=True)

def resolve_wiki_query(query: str) -> str | None:
    headers = {"User-Agent": USER_AGENT}
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "prop": "imageinfo",
        "iiprop": "url",
        "iiurlwidth": str(MAX_DIM),
        "format": "json"
    }
    try:
        r = httpx.get(WIKI_API, params=params, headers=headers, timeout=20)
        if r.status_code == 200:
            pages = r.json().get("query", {}).get("pages", {})
            for _, val in pages.items():
                imageinfo = val.get("imageinfo", [{}])[0]
                thumb = imageinfo.get("thumburl") or imageinfo.get("url")
                if thumb and thumb.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    return thumb
    except Exception as e:
        print(f"  [!] Wiki search error for '{query}': {e}")
    return None

def download_and_save(source: str, dest_path: str, fallback: str | None = None) -> bool:
    # Check if source is local file
    if os.path.exists(source):
        try:
            with Image.open(source) as img:
                img = img.convert("RGB")
                img.thumbnail((MAX_DIM, MAX_DIM), Image.Resampling.LANCZOS)
                img.save(dest_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
            print(f"  [OK] Copied & optimized local file: {source} -> {dest_path}")
            return True
        except Exception as e:
            print(f"  [!] Failed local file {source}: {e}")

    # Determine URL
    url = None
    if source.startswith("wiki:"):
        query = source.replace("wiki:", "", 1)
        url = resolve_wiki_query(query)
        if not url:
            print(f"  [?] Wiki search didn't resolve for '{query}', trying fallback...")
            url = fallback
    elif source.startswith("http://") or source.startswith("https://"):
        url = source
    else:
        url = fallback

    if not url:
        print(f"  [X] No valid URL for {dest_path}")
        return False

    # Download from URL
    headers = {"User-Agent": USER_AGENT}
    try:
        r = httpx.get(url, headers=headers, follow_redirects=True, timeout=30)
        if r.status_code != 200 and fallback and fallback != url:
            print(f"  [?] HTTP {r.status_code} for {url}, trying fallback {fallback}...")
            r = httpx.get(fallback, headers=headers, follow_redirects=True, timeout=30)
        
        if r.status_code == 200:
            with Image.open(io.BytesIO(r.content)) as img:
                img = img.convert("RGB")
                img.thumbnail((MAX_DIM, MAX_DIM), Image.Resampling.LANCZOS)
                img.save(dest_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
            size_kb = os.path.getsize(dest_path) // 1024
            print(f"  [OK] Downloaded {dest_path} ({img.size[0]}x{img.size[1]}, {size_kb} KB)")
            return True
        else:
            print(f"  [X] HTTP {r.status_code} fetching {url}")
            return False
    except Exception as e:
        print(f"  [X] Error downloading {url}: {e}")
        if fallback and fallback != url:
            try:
                r = httpx.get(fallback, headers=headers, follow_redirects=True, timeout=30)
                if r.status_code == 200:
                    with Image.open(io.BytesIO(r.content)) as img:
                        img = img.convert("RGB")
                        img.thumbnail((MAX_DIM, MAX_DIM), Image.Resampling.LANCZOS)
                        img.save(dest_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
                    print(f"  [OK] Fallback downloaded {dest_path}")
                    return True
            except Exception as e2:
                print(f"  [X] Fallback also failed: {e2}")
        return False

# 13 Movements Mapping: id -> list of 3 items (source, fallback, description)
MOVEMENTS = {
    "neoclassicism": [
        ("wiki:Athlete head Met 11.210.2", "https://images.unsplash.com/photo-1544717305-2782549b5136?w=1200&auto=format&fit=crop&q=85", "Greek marble bust"),
        ("https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=1200&auto=format&fit=crop&q=85", None, "Marble drapery shading"),
        ("app/static/deck/detailed_microrealism_statue.jpg", "https://images.unsplash.com/photo-1598371839696-5c5bb00bdc28?w=1200&auto=format&fit=crop&q=85", "Shoulder statue tattoo")
    ],
    "baroque": [
        ("wiki:Caravaggio Saint Thomas", "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=1200&auto=format&fit=crop&q=85", "Caravaggio oil painting"),
        ("https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1200&auto=format&fit=crop&q=85", None, "Chiaroscuro shadow detail"),
        ("https://images.unsplash.com/photo-1562962230-16e4623d36e6?w=1200&auto=format&fit=crop&q=85", None, "Chiaroscuro portrait sleeve tattoo")
    ],
    "irezumi": [
        ("wiki:1952.343 - Under the Wave off Kanagawa", "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=1200&auto=format&fit=crop&q=85", "Hokusai Great Wave print"),
        ("https://images.unsplash.com/photo-1579783928621-7a13d66a62d1?w=1200&auto=format&fit=crop&q=85", None, "Japanese dragon scale linework"),
        ("https://images.unsplash.com/photo-1568515045052-f9a854d70bfd?w=1200&auto=format&fit=crop&q=85", None, "Full Japanese backpiece tattoo")
    ],
    "anime_manga": [
        ("https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=1200&auto=format&fit=crop&q=85", None, "High-contrast manga panel"),
        ("https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=1200&auto=format&fit=crop&q=85", None, "G-pen speedlines & crosshatching"),
        ("https://images.unsplash.com/photo-1590246814883-578336ff3ee7?w=1200&auto=format&fit=crop&q=85", None, "Fine-line manga character tattoo")
    ],
    "bauhaus": [
        ("wiki:Composition IX.jpg", "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=1200&auto=format&fit=crop&q=85", "Kandinsky Bauhaus geometry"),
        ("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&auto=format&fit=crop&q=85", None, "Red & black grid lines"),
        ("app/static/deck/geometric_mandala_shoulder.jpg", "https://images.unsplash.com/photo-1598371839696-5c5bb00bdc28?w=1200&auto=format&fit=crop&q=85", "Minimalist geometric tattoo")
    ],
    "art_nouveau": [
        ("wiki:Alfons Mucha - 1896 - La Dame aux Camélias", "wiki:1897. Zodiac.jpg", "Alphonse Mucha poster illustration"),
        ("https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=1200&auto=format&fit=crop&q=85", None, "Botanical vine whiplash curves"),
        ("app/static/deck/minimal_botanical_arm.jpg", "https://images.unsplash.com/photo-1562962230-16e4623d36e6?w=1200&auto=format&fit=crop&q=85", "Floral whiplash ribcage/arm tattoo")
    ],
    "celtic_nordic": [
        ("wiki:Rökstenen östergötland", "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&auto=format&fit=crop&q=85", "Ancient Viking runestone"),
        ("wiki:Celtic knot", "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=1200&auto=format&fit=crop&q=85", "Endless ribbon knotwork"),
        ("app/static/deck/bold_blackwork_armband.jpg", "https://images.unsplash.com/photo-1611501275019-9b5cda994e8d?w=1200&auto=format&fit=crop&q=85", "Celtic armband wrap tattoo")
    ],
    "art_deco": [
        ("wiki:Art Deco architecture of New York City", "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=1200&auto=format&fit=crop&q=85", "Symmetrical 1920s golden arch"),
        ("https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1200&auto=format&fit=crop&q=85", None, "Sunburst ray geometric linework"),
        ("app/static/deck/geometric_flash_mandala.jpg", "https://images.unsplash.com/photo-1568515045052-f9a854d70bfd?w=1200&auto=format&fit=crop&q=85", "Art Deco geometric backpiece tattoo")
    ],
    "surrealism": [
        ("wiki:Hieronymus Bosch The Garden of Earthly Delights", "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&auto=format&fit=crop&q=85", "Surrealist dreamscape art"),
        ("wiki:Odilon Redon eye", "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1200&auto=format&fit=crop&q=85", "Levitating anatomical eye detail"),
        ("https://images.unsplash.com/photo-1598371839696-5c5bb00bdc28?w=1200&auto=format&fit=crop&q=85", None, "Surrealist forearm tattoo")
    ],
    "polynesian": [
        ("wiki:Marquesan tiki sculpture", "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&auto=format&fit=crop&q=85", "Traditional Polynesian wood carving"),
        ("wiki:Koru pattern", "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=1200&auto=format&fit=crop&q=85", "Korukoru spiral line detail"),
        ("https://images.unsplash.com/photo-1568515045052-f9a854d70bfd?w=1200&auto=format&fit=crop&q=85", None, "Full Polynesian shoulder sleeve tattoo")
    ],
    "american_traditional": [
        ("app/static/deck/traditional_flash_dagger.jpg", "wiki:traditional tattoo flash sheet", "Sailor Jerry vintage flash sheet"),
        ("https://images.unsplash.com/photo-1598371839696-5c5bb00bdc28?w=1200&auto=format&fit=crop&q=85", None, "Bold black 14RL contour line"),
        ("app/static/deck/traditional_swallow_dagger_arm.jpg", None, "Traditional eagle/anchor/dagger tattoo")
    ],
    "microrealism": [
        ("https://images.unsplash.com/photo-1544717305-2782549b5136?w=1200&auto=format&fit=crop&q=85", None, "Photographic miniature portrait"),
        ("https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1200&auto=format&fit=crop&q=85", None, "1RL needle stipple shading detail"),
        ("app/static/deck/detailed_microrealism_statue.jpg", None, "Fine-line miniature statue tattoo")
    ],
    "cyber_sigilism": [
        ("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200&auto=format&fit=crop&q=85", None, "Dark Y2K liquid chrome sigil"),
        ("https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=1200&auto=format&fit=crop&q=85", None, "Tapered sharp tendril tips"),
        ("https://images.unsplash.com/photo-1611501275019-9b5cda994e8d?w=1200&auto=format&fit=crop&q=85", None, "Cyber-sigil collarbone wrap tattoo")
    ],
}

def main():
    print("=" * 60)
    print("CORPUS VAULT — Downloading & Optimizing 13 Art Movements")
    print("=" * 60)
    
    total = len(MOVEMENTS) * 3
    success_count = 0
    results = []

    for mov_id, items in MOVEMENTS.items():
        print(f"\nProcessing [{mov_id}]...")
        for idx, (source, fallback, desc) in enumerate(items, start=1):
            filename = f"{mov_id}_{idx}.jpg"
            dest_path = os.path.join(OUTPUT_DIR, filename)
            print(f" -> Slide {idx}: {desc} ({filename})")
            ok = download_and_save(source, dest_path, fallback)
            if ok:
                success_count += 1
                size_kb = os.path.getsize(dest_path) // 1024
                results.append((filename, desc, "OK", f"{size_kb} KB"))
            else:
                results.append((filename, desc, "FAILED", "-"))

    print("\n" + "=" * 60)
    print(f"COMPLETED: {success_count}/{total} images successfully prepared in {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
