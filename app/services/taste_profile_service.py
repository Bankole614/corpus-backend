"""
Taste profile service.

Deliberately NOT an LLM call — this is a fixed, small quiz, and a templated
summary is faster, free, and fully predictable. Save the LLM budget for
features that actually need judgment (concierge, verification).
"""

from app.models.taste_profile import TasteProfileRequest

_LINE_WEIGHT_PHRASES = {"fine": "fine linework", "bold": "bold, graphic lines"}
_COLOR_PHRASES = {"color": "full color", "black_grey": "black and grey"}
_COMPOSITION_PHRASES = {"symmetrical": "symmetrical, structured composition", "organic": "organic, flowing composition"}


def build_summary(req: TasteProfileRequest) -> str:
    words = ", ".join(w.value for w in req.descriptive_words)
    line = _LINE_WEIGHT_PHRASES[req.line_weight]
    color = _COLOR_PHRASES[req.color_approach]
    composition = _COMPOSITION_PHRASES[req.composition]
    return (
        f"Drawn to {words} work, leaning toward {line} in {color}, "
        f"with a {composition}."
    )
