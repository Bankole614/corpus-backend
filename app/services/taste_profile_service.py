"""
Taste profile service.

Deliberately NOT an LLM call — this is a fixed, small quiz, and a templated
summary is faster, free, and fully predictable. Save the LLM budget for
features that actually need judgment (concierge, verification).
"""

from app.models.taste_profile import DescriptiveWord, StyleCardItem, TasteProfileRequest

_LINE_WEIGHT_PHRASES = {"fine": "fine linework", "bold": "bold, graphic lines"}
_COLOR_PHRASES = {"color": "full color", "black_grey": "black and grey"}
_COMPOSITION_PHRASES = {"symmetrical": "symmetrical, structured composition", "organic": "organic, flowing composition"}


_DEFAULT_STYLE_DECK: list[StyleCardItem] = [
    StyleCardItem(
        id="minimal-botanical-arm",
        title="Fine-Line Botanical Arm Tattoo",
        image_url="/static/deck/minimal_botanical_arm.jpg",
        word=DescriptiveWord.minimal,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),
    StyleCardItem(
        id="traditional-swallow-arm",
        title="American Traditional Swallow & Dagger",
        image_url="/static/deck/traditional_swallow_dagger_arm.jpg",
        word=DescriptiveWord.traditional,
        line_weight="bold",
        color_approach="color",
        composition="organic",
    ),
    StyleCardItem(
        id="geometric-mandala-shoulder",
        title="Sacred Geometry Mandala Shoulder",
        image_url="/static/deck/geometric_mandala_shoulder.jpg",
        word=DescriptiveWord.geometric,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),
    StyleCardItem(
        id="illustrative-serpent-forearm",
        title="Illustrative Blackwork Serpent & Peony",
        image_url="/static/deck/illustrative_serpent_forearm.jpg",
        word=DescriptiveWord.illustrative,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),
    StyleCardItem(
        id="bold-blackwork-armband",
        title="Bold Geometric Blackwork Armband",
        image_url="/static/deck/bold_blackwork_armband.jpg",
        word=DescriptiveWord.bold,
        line_weight="bold",
        color_approach="black_grey",
        composition="symmetrical",
    ),
    StyleCardItem(
        id="detailed-microrealism-statue",
        title="Microrealism Classical Statue",
        image_url="/static/deck/detailed_microrealism_statue.jpg",
        word=DescriptiveWord.detailed,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),
    StyleCardItem(
        id="minimal-flash-wildflower",
        title="Delicate Wildflower Sprig",
        image_url="/static/deck/minimal_flash_wildflower.jpg",
        word=DescriptiveWord.minimal,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),
    StyleCardItem(
        id="traditional-flash-dagger",
        title="Traditional Dagger & Roses Flash",
        image_url="/static/deck/traditional_flash_dagger.jpg",
        word=DescriptiveWord.traditional,
        line_weight="bold",
        color_approach="color",
        composition="symmetrical",
    ),
    StyleCardItem(
        id="geometric-flash-mandala",
        title="Dotwork Sacred Mandala Flash",
        image_url="/static/deck/geometric_flash_mandala.jpg",
        word=DescriptiveWord.geometric,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),
    StyleCardItem(
        id="illustrative-flash-serpent",
        title="Celestial Crescent Serpent Flash",
        image_url="/static/deck/illustrative_flash_serpent.jpg",
        word=DescriptiveWord.illustrative,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),
]


def get_default_style_deck(limit: int = 50) -> list[StyleCardItem]:
    if not isinstance(limit, int):
        limit = 50
    return _DEFAULT_STYLE_DECK[:limit]


def build_summary(req: TasteProfileRequest) -> str:
    words = ", ".join(w.value for w in req.descriptive_words)
    line = _LINE_WEIGHT_PHRASES[req.line_weight]
    color = _COLOR_PHRASES[req.color_approach]
    composition = _COMPOSITION_PHRASES[req.composition]
    return (
        f"Drawn to {words} work, leaning toward {line} in {color}, "
        f"with a {composition}."
    )


