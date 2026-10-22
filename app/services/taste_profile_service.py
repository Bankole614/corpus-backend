"""
Taste profile service.

Deliberately NOT an LLM call — this is a fixed, curated swipe deck, and a templated
summary is faster, free, and fully predictable. Save the LLM budget for
features that actually need judgment (concierge, verification).
"""

import logging

from app.core.config import settings
from app.models.taste_profile import (
    DescriptiveWord,
    StyleCardItem,
    TasteAestheticTraits,
    TasteConsultationAdvice,
    TastePlacementInsights,
    TasteProfileRequest,
    TasteProfileResult,
)

logger = logging.getLogger(__name__)

_LINE_WEIGHT_PHRASES = {
    "fine": "fine linework",
    "bold": "bold, graphic lines",
    "medium": "balanced linework",
}
_COLOR_PHRASES = {
    "color": "full color",
    "black_grey": "black and grey",
}
_COMPOSITION_PHRASES = {
    "symmetrical": "symmetrical, structured composition",
    "organic": "organic, flowing composition",
    "flowing": "flowing, dynamic composition",
    "radial": "radial, centered composition",
    "framed": "framed, architectural composition",
    "asymmetrical": "asymmetrical, balanced composition",
}


def _card_img(filename: str) -> str:
    """Resolve card image URL to Cloudflare R2 CDN or fallback to local static."""
    base = (getattr(settings, "r2_public_url", "") or "").rstrip("/")
    if base:
        return f"{base}/deck/{filename}"
    return f"/static/deck/{filename}"


_DEFAULT_STYLE_DECK: list[StyleCardItem] = [

    StyleCardItem(
        id="geometric-mandala-shoulder",
        title="Sacred Geometry Mandala Shoulder",
        image_url=_card_img("geometric_mandala_shoulder.jpg"),
        word=DescriptiveWord.geometric,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="text-japanese-kanji-shodo",
        title="Japanese Shodo Sumi Brush Kanji",
        image_url=_card_img("text_japanese_kanji_shodo.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="bold",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="full-back-woodcut-danse-macabre",
        title="Renaissance Woodcut Danse Macabre Backpiece",
        image_url=_card_img("full_back_woodcut_danse_macabre.jpg"),
        word=DescriptiveWord.illustrative,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="full-sleeve-biomechanical-giger",
        title="Biomechanical H.R. Giger Full Sleeve",
        image_url=_card_img("full_sleeve_biomechanical_giger.jpg"),
        word=DescriptiveWord.detailed,
        line_weight="medium",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="leg-shin-traditional-dagger-serpent",
        title="Traditional Dagger & Serpent Shin Piece",
        image_url=_card_img("leg_shin_traditional_dagger_serpent.jpg"),
        word=DescriptiveWord.traditional,
        line_weight="bold",
        color_approach="color",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="minimal-script-cursive",
        title="Fine-Line Cursive Script & Quote",
        image_url=_card_img("minimal_script_cursive.jpg"),
        word=DescriptiveWord.minimal,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="bold-blackwork-armband",
        title="Bold Geometric Blackwork Armband",
        image_url=_card_img("bold_blackwork_armband.jpg"),
        word=DescriptiveWord.bold,
        line_weight="bold",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="ornamental-art-deco-sunburst",
        title="Art Deco Sunburst & Moth",
        image_url=_card_img("ornamental_art_deco_sunburst.jpg"),
        word=DescriptiveWord.ornamental,
        line_weight="fine",
        color_approach="black_grey",
        composition="radial",
    ),

    StyleCardItem(
        id="realism-portrait-study",
        title="Black-and-Grey Portrait Study",
        image_url=_card_img("realism_portrait_study.jpg"),
        word=DescriptiveWord.realism,
        line_weight="medium",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="text-greek-epigraphy",
        title="Ancient Greek Lapidary Inscription",
        image_url=_card_img("text_greek_epigraphy.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="full-sleeve-illustrative-serpent",
        title="Illustrative Botanical & Serpent Full Sleeve",
        image_url=_card_img("full_sleeve_illustrative_serpent.jpg"),
        word=DescriptiveWord.illustrative,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="traditional-flash-dagger",
        title="Traditional Dagger & Roses Flash",
        image_url=_card_img("traditional_flash_dagger.jpg"),
        word=DescriptiveWord.traditional,
        line_weight="bold",
        color_approach="color",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="detailed-microrealism-statue",
        title="Microrealism Classical Statue",
        image_url=_card_img("detailed_microrealism_statue.jpg"),
        word=DescriptiveWord.detailed,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="bold-gothic-lettering",
        title="Bold Gothic Old English Lettering",
        image_url=_card_img("bold_gothic_lettering.jpg"),
        word=DescriptiveWord.bold,
        line_weight="bold",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="japanese-phoenix-windbars",
        title="Phoenix & Wind Bars",
        image_url=_card_img("japanese_phoenix_windbars.jpg"),
        word=DescriptiveWord.japanese,
        line_weight="bold",
        color_approach="color",
        composition="flowing",
    ),

    StyleCardItem(
        id="geometric-optical-armband",
        title="Optical Geometric Armband",
        image_url=_card_img("geometric_optical_armband.jpg"),
        word=DescriptiveWord.geometric,
        line_weight="bold",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="surrealist-classical-bloom",
        title="Classical Bust with Blooming Branch",
        image_url=_card_img("surrealist_classical_bloom.jpg"),
        word=DescriptiveWord.surrealist,
        line_weight="mixed",
        color_approach="black_grey",
        composition="asymmetrical",
    ),

    StyleCardItem(
        id="text-cyberpunk-digital-font",
        title="Cyberpunk Monospaced Terminal Data",
        image_url=_card_img("text_cyberpunk_digital_font.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="illustrative-serpent-forearm",
        title="Illustrative Blackwork Serpent & Peony",
        image_url=_card_img("illustrative_serpent_forearm.jpg"),
        word=DescriptiveWord.illustrative,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="neo-traditional-sacred-heart",
        title="Sacred Heart & Roses",
        image_url=_card_img("neo_traditional_sacred_heart.jpg"),
        word=DescriptiveWord.neo_traditional,
        line_weight="bold",
        color_approach="color",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="japanese-irezumi-dragon-wave",
        title="Irezumi Dragon & Waves",
        image_url=_card_img("japanese_irezumi_dragon_wave.jpg"),
        word=DescriptiveWord.japanese,
        line_weight="bold",
        color_approach="color",
        composition="flowing",
    ),

    StyleCardItem(
        id="text-collegiate-block-numbers",
        title="Vintage Collegiate Athletic Numbers",
        image_url=_card_img("text_collegiate_block_numbers.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="bold",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="traditional-swallow-arm",
        title="American Traditional Swallow & Dagger",
        image_url=_card_img("traditional_swallow_dagger_arm.jpg"),
        word=DescriptiveWord.traditional,
        line_weight="bold",
        color_approach="color",
        composition="organic",
    ),

    StyleCardItem(
        id="ornamental-jain-emblem",
        title="Jain Cosmological Emblem",
        image_url=_card_img("ornamental_jain_emblem.jpg"),
        word=DescriptiveWord.ornamental,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="bold-tribal-totem",
        title="Heavy Graphic Blackwork Totem",
        image_url=_card_img("bold_tribal_totem.jpg"),
        word=DescriptiveWord.bold,
        line_weight="bold",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="text-ambigram-calligraphy",
        title="Symmetrical Rotational Ambigram Word",
        image_url=_card_img("text_ambigram_calligraphy.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="full-back-japanese-dragon",
        title="Japanese Irezumi Dragon Full Backpiece",
        image_url=_card_img("full_back_japanese_dragon.jpg"),
        word=DescriptiveWord.japanese,
        line_weight="bold",
        color_approach="color",
        composition="flowing",
    ),

    StyleCardItem(
        id="leg-knee-ornamental-spiderweb-mandala",
        title="Spiderweb & Mandala Kneecap Piece",
        image_url=_card_img("leg_knee_ornamental_spiderweb_mandala.jpg"),
        word=DescriptiveWord.geometric,
        line_weight="bold",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="illustrative-woodcut-skull",
        title="Renaissance Woodcut Etched Skull",
        image_url=_card_img("illustrative_woodcut_skull.jpg"),
        word=DescriptiveWord.illustrative,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="text-gothic-fraktur",
        title="German Fraktur Blackletter Calligraphy",
        image_url=_card_img("text_gothic_fraktur.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="bold",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="full-sleeve-botanical-garden",
        title="Fine-Line Wild Botanical Garden Full Sleeve",
        image_url=_card_img("full_sleeve_botanical_garden.jpg"),
        word=DescriptiveWord.minimal,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="full-sleeve-gothic-cathedral",
        title="Gothic Cathedral Architecture Full Sleeve",
        image_url=_card_img("full_sleeve_gothic_cathedral.jpg"),
        word=DescriptiveWord.detailed,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="surrealist-floating-key",
        title="Antique Key & Floating Landscape",
        image_url=_card_img("surrealist_floating_key.jpg"),
        word=DescriptiveWord.surrealist,
        line_weight="fine",
        color_approach="black_grey",
        composition="asymmetrical",
    ),

    StyleCardItem(
        id="text-medieval-illuminated-letter",
        title="Medieval Lombardic Illuminated Drop-Cap",
        image_url=_card_img("text_medieval_illuminated_letter.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="bold",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="illustrative-lunar-moth",
        title="Illustrative Lunar Moth & Florals",
        image_url=_card_img("illustrative_lunar_moth.jpg"),
        word=DescriptiveWord.illustrative,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="traditional-crawling-panther",
        title="Traditional Crawling Black Panther",
        image_url=_card_img("traditional_crawling_panther.jpg"),
        word=DescriptiveWord.traditional,
        line_weight="bold",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="geometric-platonic-chest",
        title="Metatron's Cube & Platonic Solids",
        image_url=_card_img("geometric_platonic_chest.jpg"),
        word=DescriptiveWord.geometric,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="text-micro-cursive-script",
        title="Literary Cursive Micro-Script",
        image_url=_card_img("text_micro_cursive_script.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="realism-full-back-lion",
        title="Solitary Classical Lion Full Backpiece",
        image_url=_card_img("realism_full_back_lion.jpg"),
        word=DescriptiveWord.realism,
        line_weight="medium",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="ornamental-islamic-geometry",
        title="Islamic Geometric Medallion",
        image_url=_card_img("ornamental_islamic_geometry.jpg"),
        word=DescriptiveWord.ornamental,
        line_weight="fine",
        color_approach="black_grey",
        composition="radial",
    ),

    StyleCardItem(
        id="watercolor-hummingbird-blossoms",
        title="Hummingbird & Blossoms",
        image_url=_card_img("watercolor_hummingbird_blossoms.jpg"),
        word=DescriptiveWord.watercolor,
        line_weight="mixed",
        color_approach="color",
        composition="organic",
    ),

    StyleCardItem(
        id="text-baroque-ornamental-monogram",
        title="Baroque Royal Monogram Initial",
        image_url=_card_img("text_baroque_ornamental_monogram.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="full-sleeve-greek-mythology",
        title="Classical Greek Mythology Full Sleeve",
        image_url=_card_img("full_sleeve_greek_mythology.jpg"),
        word=DescriptiveWord.detailed,
        line_weight="medium",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="hand-ornamental-mandala-fingers",
        title="Sacred Geometry Hand Mandala & Finger Bands",
        image_url=_card_img("hand_ornamental_mandala_fingers.jpg"),
        word=DescriptiveWord.geometric,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="japanese-koi-maple",
        title="Koi & Maple Leaves",
        image_url=_card_img("japanese_koi_maple.jpg"),
        word=DescriptiveWord.japanese,
        line_weight="bold",
        color_approach="color",
        composition="organic",
    ),

    StyleCardItem(
        id="text-roman-inscription",
        title="Classical Latin Trajan Epigraphy",
        image_url=_card_img("text_roman_inscription.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="surrealist-eye-portal",
        title="Eye Within a Stone Portal",
        image_url=_card_img("surrealist_eye_portal.jpg"),
        word=DescriptiveWord.surrealist,
        line_weight="medium",
        color_approach="black_grey",
        composition="framed",
    ),

    StyleCardItem(
        id="hand-neotraditional-tiger-rose",
        title="Neo-Traditional Tiger & Rose Hand Piece",
        image_url=_card_img("hand_neotraditional_tiger_rose.jpg"),
        word=DescriptiveWord.neo_traditional,
        line_weight="bold",
        color_approach="color",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="realism-tiger-portrait",
        title="Realistic Tiger Portrait",
        image_url=_card_img("realism_tiger_portrait.jpg"),
        word=DescriptiveWord.realism,
        line_weight="medium",
        color_approach="black_grey",
        composition="framed",
    ),

    StyleCardItem(
        id="hand-chicano-lettering-script",
        title="Bold Chicano Calligraphy Hand Piece",
        image_url=_card_img("hand_chicano_lettering_script.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="bold",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="hand-dark-illustrative-moth",
        title="Illustrative Hawk Moth Hand Piece",
        image_url=_card_img("hand_dark_illustrative_moth.jpg"),
        word=DescriptiveWord.illustrative,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="detailed-anatomical-eye",
        title="Microrealism Anatomical Eye & Tear",
        image_url=_card_img("detailed_anatomical_eye.jpg"),
        word=DescriptiveWord.detailed,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="full-back-cybersigilism-exoskeleton",
        title="Cyber-Sigilism Biomechanical Spine Backpiece",
        image_url=_card_img("full_back_cybersigilism_exoskeleton.jpg"),
        word=DescriptiveWord.bold,
        line_weight="bold",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="text-chinese-hanzi-seal",
        title="Classical Chinese Hanzi & Vermilion Seal",
        image_url=_card_img("text_chinese_hanzi_seal.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="fine",
        color_approach="color",
        composition="organic",
    ),

    StyleCardItem(
        id="japanese-hannya-peony",
        title="Hannya Mask & Peonies",
        image_url=_card_img("japanese_hannya_peony.jpg"),
        word=DescriptiveWord.japanese,
        line_weight="bold",
        color_approach="color",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="minimal-botanical-arm",
        title="Fine-Line Botanical Arm Tattoo",
        image_url=_card_img("minimal_botanical_arm.jpg"),
        word=DescriptiveWord.minimal,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="ornamental-celtic-interlace",
        title="Celtic Interlace Band",
        image_url=_card_img("ornamental_celtic_interlace.jpg"),
        word=DescriptiveWord.ornamental,
        line_weight="bold",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="text-arabic-calligraphy",
        title="Arabic Thuluth & Diwani Calligraphy",
        image_url=_card_img("text_arabic_calligraphy.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="neo-traditional-ganesha-lotus",
        title="Ganesha & Lotus",
        image_url=_card_img("neo_traditional_ganesha_lotus.jpg"),
        word=DescriptiveWord.neo_traditional,
        line_weight="bold",
        color_approach="color",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="realism-classical-bust",
        title="Greco-Roman Marble Bust",
        image_url=_card_img("realism_classical_bust.jpg"),
        word=DescriptiveWord.realism,
        line_weight="medium",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="detailed-engraving-portrait",
        title="Fine-Line Renaissance Portrait",
        image_url=_card_img("detailed_engraving_portrait.jpg"),
        word=DescriptiveWord.detailed,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="text-vintage-serif-retro",
        title="1970s Vintage Serif Editorial",
        image_url=_card_img("text_vintage_serif_retro.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="bold",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="full-sleeve-japanese-irezumi",
        title="Traditional Japanese Irezumi Full Sleeve",
        image_url=_card_img("full_sleeve_japanese_irezumi.jpg"),
        word=DescriptiveWord.japanese,
        line_weight="bold",
        color_approach="color",
        composition="flowing",
    ),

    StyleCardItem(
        id="traditional-clipper-ship",
        title="Traditional Maritime Clipper Ship",
        image_url=_card_img("traditional_clipper_ship.jpg"),
        word=DescriptiveWord.traditional,
        line_weight="bold",
        color_approach="color",
        composition="organic",
    ),

    StyleCardItem(
        id="geometric-flash-mandala",
        title="Dotwork Sacred Mandala Flash",
        image_url=_card_img("geometric_flash_mandala.jpg"),
        word=DescriptiveWord.geometric,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="text-vintage-typewriter",
        title="Vintage Typewriter Monospace Text",
        image_url=_card_img("text_vintage_typewriter.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="neo-traditional-medusa",
        title="Medusa Portrait & Serpents",
        image_url=_card_img("neo_traditional_medusa.jpg"),
        word=DescriptiveWord.neo_traditional,
        line_weight="bold",
        color_approach="color",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="leg-thigh-renaissance-sculpture",
        title="Renaissance Statue & Peonies Thigh Piece",
        image_url=_card_img("leg_thigh_renaissance_sculpture.jpg"),
        word=DescriptiveWord.detailed,
        line_weight="medium",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="minimal-abstract-continuous",
        title="Continuous Single-Line Silhouette",
        image_url=_card_img("minimal_abstract_continuous.jpg"),
        word=DescriptiveWord.minimal,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="text-chicano-flourished-script",
        title="Chicano Calligraphy & Filigree Script",
        image_url=_card_img("text_chicano_flourished_script.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="bold",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="full-sleeve-optical-geometry",
        title="Optical Sacred Geometry & Blackout Full Sleeve",
        image_url=_card_img("full_sleeve_optical_geometry.jpg"),
        word=DescriptiveWord.geometric,
        line_weight="bold",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="full-sleeve-art-nouveau-mucha",
        title="Art Nouveau Alphonse Mucha Full Sleeve",
        image_url=_card_img("full_sleeve_art_nouveau_mucha.jpg"),
        word=DescriptiveWord.illustrative,
        line_weight="bold",
        color_approach="color",
        composition="organic",
    ),

    StyleCardItem(
        id="bold-cybersigilism-spine",
        title="Sharp Cyber-Sigilism Spine Piece",
        image_url=_card_img("bold_cybersigilism_spine.jpg"),
        word=DescriptiveWord.bold,
        line_weight="bold",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="full-sleeve-renaissance-atelier",
        title="Classical Renaissance Atelier Full Sleeve",
        image_url=_card_img("full_sleeve_renaissance_atelier.jpg"),
        word=DescriptiveWord.detailed,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="text-roman-numerals",
        title="Architectural Roman Numerals",
        image_url=_card_img("text_roman_numerals.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="neo-traditional-fox-peonies",
        title="Ornate Fox & Peonies",
        image_url=_card_img("neo_traditional_fox_peonies.jpg"),
        word=DescriptiveWord.neo_traditional,
        line_weight="bold",
        color_approach="color",
        composition="organic",
    ),

    StyleCardItem(
        id="full-back-sacred-geometry-tree",
        title="Sacred Geometry & Spinal Tree Backpiece",
        image_url=_card_img("full_back_sacred_geometry_tree.jpg"),
        word=DescriptiveWord.geometric,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="realism-anatomical-heart",
        title="Anatomical Heart & Vessels",
        image_url=_card_img("realism_anatomical_heart.jpg"),
        word=DescriptiveWord.realism,
        line_weight="medium",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="text-nordic-runic-inscription",
        title="Elder Futhark Nordic Rune Inscription",
        image_url=_card_img("text_nordic_runic_inscription.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="bold",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="full-sleeve-nordic-viking",
        title="Nordic Viking Mythology & Yggdrasil Full Sleeve",
        image_url=_card_img("full_sleeve_nordic_viking.jpg"),
        word=DescriptiveWord.illustrative,
        line_weight="bold",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="full-sleeve-astronomical-codex",
        title="Medieval Astronomical Codex Full Sleeve",
        image_url=_card_img("full_sleeve_astronomical_codex.jpg"),
        word=DescriptiveWord.detailed,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="surrealist-melting-hourglass",
        title="Melting Hourglass & Wildflowers",
        image_url=_card_img("surrealist_melting_hourglass.jpg"),
        word=DescriptiveWord.surrealist,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="text-sanskrit-mantra",
        title="Sanskrit Devanagari Vedic Mantra",
        image_url=_card_img("text_sanskrit_mantra.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="full-sleeve-neotraditional-maritime",
        title="Neo-Traditional Maritime Full Sleeve",
        image_url=_card_img("full_sleeve_neotraditional_maritime.jpg"),
        word=DescriptiveWord.neo_traditional,
        line_weight="bold",
        color_approach="color",
        composition="organic",
    ),

    StyleCardItem(
        id="full-sleeve-polynesian-tatau",
        title="Polynesian Samoan Tatau Full Sleeve",
        image_url=_card_img("full_sleeve_polynesian_tatau.jpg"),
        word=DescriptiveWord.bold,
        line_weight="bold",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="minimal-flash-wildflower",
        title="Delicate Wildflower Sprig",
        image_url=_card_img("minimal_flash_wildflower.jpg"),
        word=DescriptiveWord.minimal,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="text-modernist-sans-serif",
        title="Swiss Modernist Coordinates Typography",
        image_url=_card_img("text_modernist_sans_serif.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="detailed-baroque-sculpture",
        title="High-Detail Baroque Marble Torso",
        image_url=_card_img("detailed_baroque_sculpture.jpg"),
        word=DescriptiveWord.detailed,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="full-back-fallen-angel",
        title="The Fallen Angel Realism Full Backpiece",
        image_url=_card_img("full_back_fallen_angel.jpg"),
        word=DescriptiveWord.realism,
        line_weight="medium",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="illustrative-flash-serpent",
        title="Celestial Crescent Serpent Flash",
        image_url=_card_img("illustrative_flash_serpent.jpg"),
        word=DescriptiveWord.illustrative,
        line_weight="fine",
        color_approach="black_grey",
        composition="organic",
    ),

    StyleCardItem(
        id="text-hebrew-calligraphy",
        title="Sacred Hebrew Script Inscription",
        image_url=_card_img("text_hebrew_calligraphy.jpg"),
        word=DescriptiveWord.lettering,
        line_weight="fine",
        color_approach="black_grey",
        composition="symmetrical",
    ),

    StyleCardItem(
        id="full-back-baroque-sculpture",
        title="Baroque Bernini Marble Sculpture Backpiece",
        image_url=_card_img("full_back_baroque_sculpture.jpg"),
        word=DescriptiveWord.detailed,
        line_weight="medium",
        color_approach="black_grey",
        composition="organic",
    ),

]


def get_default_style_deck(limit: int = 150) -> list[StyleCardItem]:
    """
    Return style cards for the taste profile discovery quiz.
    The deck is pre-randomized and balanced such that no consecutive cards
    share the same style/type (e.g., typographical tattoos are well-spaced)
    or composition flow.
    """
    if not isinstance(limit, int):
        limit = 150
    return _DEFAULT_STYLE_DECK[:limit]


_ARCHETYPE_PAIRS = {
    frozenset({DescriptiveWord.minimal, DescriptiveWord.lettering}): (
        "The Poetic Epigraphist",
        "Fine-line typographical devotion balanced with quiet, deliberate negative space.",
    ),
    frozenset({DescriptiveWord.minimal, DescriptiveWord.geometric}): (
        "The Minimalist Architect",
        "Stripped-back structural geometry rendered with single-needle precision.",
    ),
    frozenset({DescriptiveWord.minimal, DescriptiveWord.illustrative}): (
        "The Delicate Botanist",
        "Fine-line natural history etchings and organic flora with breathable contours.",
    ),
    frozenset({DescriptiveWord.geometric, DescriptiveWord.ornamental}): (
        "The Sacred Mandalaist",
        "Intricate rotational mandalas, cosmological geometry, and harmonized dotwork.",
    ),
    frozenset({DescriptiveWord.detailed, DescriptiveWord.illustrative}): (
        "The Renaissance Engraver",
        "Dense woodcut engraving, cross-hatched linework, and mythological iconography.",
    ),
    frozenset({DescriptiveWord.traditional, DescriptiveWord.bold}): (
        "The Americana Traditionalist",
        "Heavy graphic blackwork, bold outlines, and iconic maritime/Americana flash.",
    ),
    frozenset({DescriptiveWord.neo_traditional, DescriptiveWord.illustrative}): (
        "The Art Nouveau Visionary",
        "Lavish botanical filigree, dimensional line hierarchy, and expressive figurative forms.",
    ),
    frozenset({DescriptiveWord.realism, DescriptiveWord.detailed}): (
        "The Chiaroscuro Sculptor",
        "Classical marble statuary, realistic photographic depth, and velvety tonal gradients.",
    ),
    frozenset({DescriptiveWord.bold, DescriptiveWord.lettering}): (
        "The Blackletter Calligrapher",
        "Authoritative gothic fraktur, bold chicano calligraphy, and sharp graphic impact.",
    ),
    frozenset({DescriptiveWord.japanese, DescriptiveWord.bold}): (
        "The Irezumi Master",
        "Dynamic wind bars, wave currents, and powerful mythological Japanese iconography.",
    ),
    frozenset({DescriptiveWord.surrealist, DescriptiveWord.illustrative}): (
        "The Metaphysical Alchemist",
        "Paradoxical juxtapositions, antique symbology, and dreamscape compositions.",
    ),
    frozenset({DescriptiveWord.watercolor, DescriptiveWord.illustrative}): (
        "The Chromatic Expressionist",
        "Fluid ink-wash blooms, dissolving borders, and spontaneous painterly motion.",
    ),
}

_SINGLE_ARCHETYPES = {
    DescriptiveWord.minimal: ("The Pure Minimalist", "Understated elegance celebrating negative space and single-needle purity."),
    DescriptiveWord.bold: ("The Graphic Blackworker", "Heavy saturation, sharp contrast, and commanding graphic silhouettes."),
    DescriptiveWord.detailed: ("The Master Engraver", "Meticulous micro-textures, multi-layered shading, and museum-grade detail."),
    DescriptiveWord.geometric: ("The Sacred Geometer", "Mathematical harmony, crystalline symmetry, and dimensional sacred geometry."),
    DescriptiveWord.illustrative: ("The Storybook Illustrator", "Narrative folklore, woodcut textures, and hand-drawn character."),
    DescriptiveWord.traditional: ("The Classic Voyager", "Timeless bold lines, heritage flash, and enduring nautical symbolism."),
    DescriptiveWord.japanese: ("The Irezumi Chronicler", "Deep mythological storytelling, flowing natural currents, and bodily harmony."),
    DescriptiveWord.neo_traditional: ("The Ornate Romantic", "Opulent floral borders, rich line hierarchy, and expressive depth."),
    DescriptiveWord.realism: ("The Photographic Realist", "Lifelike dimensionality, subtle chiaroscuro light, and skin-tone harmony."),
    DescriptiveWord.ornamental: ("The Filigree Artisan", "Architectural friezes, jewelry-inspired lace, and sacred ornamental symmetry."),
    DescriptiveWord.watercolor: ("The Watercolor Poet", "Pigment bleeds, brushwork transitions, and boundary-defying color washes."),
    DescriptiveWord.surrealist: ("The Surrealist Dreamer", "Esoteric symbolism, psychological depth, and visual paradoxes."),
    DescriptiveWord.lettering: ("The Epigraphic Scribe", "Timeless typographic weight, literary devotion, and lapidary precision."),
}

_STYLE_MOOD_MAP = {
    DescriptiveWord.minimal: ["Airy", "Subtle", "Delicate", "Restrained", "Clean"],
    DescriptiveWord.bold: ["Impactful", "Authoritative", "Commanding", "Graphic"],
    DescriptiveWord.detailed: ["Meticulous", "Museum-Grade", "Intricate", "Architectural"],
    DescriptiveWord.geometric: ["Sacred", "Crystalline", "Harmonious", "Mathematical"],
    DescriptiveWord.illustrative: ["Folkloric", "Storybook", "Organic", "Hand-Crafted"],
    DescriptiveWord.traditional: ["Heritage", "Timeless", "Iconic", "Americana"],
    DescriptiveWord.japanese: ["Mythological", "Dynamic", "Fluid", "Elemental"],
    DescriptiveWord.neo_traditional: ["Romantic", "Opulent", "Dimensional", "Art Nouveau"],
    DescriptiveWord.realism: ["Chiaroscuro", "Sculptural", "Photographic", "Atmospheric"],
    DescriptiveWord.ornamental: ["Filigree", "Lace-like", "Architectural", "Cosmological"],
    DescriptiveWord.watercolor: ["Painterly", "Chromatic", "Spontaneous", "Luminous"],
    DescriptiveWord.surrealist: ["Metaphysical", "Esoteric", "Dreamscape", "Paradoxical"],
    DescriptiveWord.lettering: ["Epigraphic", "Literary", "Calligraphic", "Lapidary"],
}

_STYLE_TECHNIQUES = {
    DescriptiveWord.minimal: "single-needle passes (1RL/3RL) and deliberate skin breaks",
    DescriptiveWord.bold: "solid black saturation, heavy outer border passes, and clean line junctions",
    DescriptiveWord.detailed: "micro-needle stippling, multi-tier wash gradients, and delicate cross-hatching",
    DescriptiveWord.geometric: "precise rotational symmetry, crisp line intersections, and consistent dotwork density",
    DescriptiveWord.illustrative: "woodcut etching linework, dynamic line weight hierarchy, and whip-shaded textures",
    DescriptiveWord.traditional: "rich black outlines, classic spit-shade gradients, and bold color packing",
    DescriptiveWord.japanese: "flowing background wind-bars, anatomical motion contouring, and deep pigment saturation",
    DescriptiveWord.neo_traditional: "sculpted variable-weight outlines, soft dimensional blending, and ornate filigree framing",
    DescriptiveWord.realism: "smooth continuous-tone grey washes, soft-edge transitions, and pinpoint highlight preservation",
    DescriptiveWord.ornamental: "mandala center-point alignment, ornamental dotwork gradients, and jewelry-grade balance",
    DescriptiveWord.watercolor: "pigment splash dispersal, soft wet-on-wet color transitions, and boundary-free edges",
    DescriptiveWord.surrealist: "perspective distortion, optical precision, and nuanced symbolic negative space",
    DescriptiveWord.lettering: "consistent letterform kerning, baseline curvature, and crisp terminal flourish execution",
}


def _resolve_archetype(words: list[DescriptiveWord], line_weight: str, composition: str) -> tuple[str, str]:
    if len(words) >= 2:
        for i in range(len(words)):
            for j in range(i + 1, len(words)):
                pair = frozenset({words[i], words[j]})
                if pair in _ARCHETYPE_PAIRS:
                    return _ARCHETYPE_PAIRS[pair]

    if words and words[0] in _SINGLE_ARCHETYPES:
        return _SINGLE_ARCHETYPES[words[0]]

    primary = words[0].value.replace("_", " ").title() if words else "Eclectic"
    secondary = words[1].value.replace("_", " ").title() if len(words) > 1 else "Curator"
    return (
        f"The {primary} {secondary}",
        f"A bespoke synthesis balancing {line_weight} linework with {composition} flow.",
    )


def _build_aesthetic_traits(req: TasteProfileRequest) -> TasteAestheticTraits:
    words = req.descriptive_words or [DescriptiveWord.minimal]
    primary = words[0].value.replace("_", " ").title()
    secondaries = [w.value.replace("_", " ").title() for w in words[1:]]

    if req.line_weight == "fine" and any(w in (DescriptiveWord.minimal, DescriptiveWord.lettering) for w in words):
        density = "Airy & Negative-Space Forward"
    elif req.line_weight == "bold" or any(w in (DescriptiveWord.bold, DescriptiveWord.traditional) for w in words):
        density = "High-Impact & Richly Saturated"
    else:
        density = "Balanced Structural Density"

    if req.color_approach == "color":
        contrast = "Vibrant Multi-Hue Chromatic Contrast"
    elif req.line_weight == "bold":
        contrast = "High-Contrast Graphic Blackwork"
    else:
        contrast = "Soft Monochromatic Tonal Gradients"

    moods: list[str] = []
    for w in words:
        for m in _STYLE_MOOD_MAP.get(w, []):
            if m not in moods:
                moods.append(m)
    if req.composition == "symmetrical":
        moods.append("Balanced")
    elif req.composition == "organic":
        moods.append("Fluid")

    return TasteAestheticTraits(
        primary_style=primary,
        secondary_styles=secondaries,
        density=density,
        contrast=contrast,
        mood_keywords=moods[:6],
    )


def _build_consultation_advice(req: TasteProfileRequest) -> TasteConsultationAdvice:
    words = req.descriptive_words or [DescriptiveWord.minimal]
    primary = words[0]

    ask_for = [
        f"Request needle groupings tuned for {req.line_weight} work (e.g. 1RL or 3RL single-needle for micro-details, or 7-9RL for bold linework).",
        "Ask for intentional skin breaks and negative space between adjacent design elements to ensure contrast endures over time.",
        "Request that the artist inspect the stencil while standing naturally, ensuring composition conforms to muscle contours.",
    ]

    avoid = [
        "Avoid compressing multiple intricate elements into a surface area smaller than 3 inches, which risks blurring as pigment settles.",
        "Avoid muddy or heavy black fills where the design requires breathable skin breaks and light.",
        "Avoid letting an artist freehand complex geometric or typographic elements without a locked stencil.",
    ]

    key_terms = ["Negative space", "Skin break", "Whip-shading"]
    if primary in (DescriptiveWord.minimal, DescriptiveWord.lettering):
        key_terms.extend(["Single-needle linework", "Kerning & baseline", "Fine-line script"])
    elif primary in (DescriptiveWord.geometric, DescriptiveWord.ornamental):
        key_terms.extend(["Rotational symmetry", "Dotwork stippling", "Sacred geometry"])
    elif primary in (DescriptiveWord.illustrative, DescriptiveWord.detailed):
        key_terms.extend(["Woodcut etching", "Cross-hatching", "Chiaroscuro"])
    elif primary in (DescriptiveWord.traditional, DescriptiveWord.bold):
        key_terms.extend(["Bold flash linework", "Solid saturation", "Color packing"])
    else:
        key_terms.extend(["Tonal graduation", "Anatomical flow"])

    return TasteConsultationAdvice(
        what_to_ask_for=ask_for,
        what_to_avoid=avoid,
        key_terms=list(dict.fromkeys(key_terms))[:5],
    )


def _build_placement_insights(req: TasteProfileRequest) -> TastePlacementInsights:
    comp = req.composition
    if comp in ("symmetrical", "radial"):
        placements = ["Sternum / Center Chest", "Upper Spine / Vertebrae", "Kneecap / Shoulder Cap", "Solar Plexus"]
    elif comp in ("flowing", "organic"):
        placements = ["Inner Forearm", "Ribcage / Flank", "Clavicle & Collarbone", "Outer Thigh"]
    else:
        placements = ["Outer Bicep / Deltoid", "Outer Calf", "Shoulder Blade / Scapula", "Forearm Flat"]

    if req.line_weight == "fine":
        aging = (
            "Fine-line ink naturally softens and spreads by ~0.5mm in the dermis over a 5 to 10 year timeline. "
            "Sizing this piece 15-20% larger than minimum ensures delicate loops, stippling, and negative space remain "
            "crisp for decades. Always apply SPF 50+ on healed skin."
        )
    elif req.line_weight == "bold":
        aging = (
            "Bold linework and solid black saturation hold their structural power exceptionally well over decades. "
            "Ensure adequate breathing room between bold lines so they do not bleed into one another with age. "
            "Daily moisturization keeps blacks rich and deep."
        )
    else:
        aging = (
            "Balanced medium-weight ink strikes an ideal equilibrium between detail retention and long-term durability. "
            "Protecting the area from excessive sun exposure ensures subtle tonal washes do not fade unevenly."
        )

    return TastePlacementInsights(
        recommended_placements=placements,
        aging_considerations=aging,
    )


def build_taste_profile_result(profile_id: str, req: TasteProfileRequest) -> TasteProfileResult:
    """Synchronous builder producing the complete editorial taste dossier."""
    deck_by_id = {c.id: c for c in _DEFAULT_STYLE_DECK}
    liked_cards = [deck_by_id[cid] for cid in req.liked_card_ids if cid in deck_by_id]

    archetype, subtitle = _resolve_archetype(req.descriptive_words, req.line_weight, req.composition)
    summary = build_summary(req)

    words_str = ", ".join(w.value.replace("_", " ") for w in req.descriptive_words)
    line_phrase = _LINE_WEIGHT_PHRASES.get(req.line_weight, f"{req.line_weight} linework")
    color_phrase = _COLOR_PHRASES.get(req.color_approach, req.color_approach)
    comp_phrase = _COMPOSITION_PHRASES.get(req.composition, f"{req.composition} composition")
    primary = req.descriptive_words[0] if req.descriptive_words else DescriptiveWord.minimal
    technique = _STYLE_TECHNIQUES.get(primary, "deliberate line hierarchy and clean skin breaks")

    p1_subjects = ""
    if liked_cards:
        titles = [f'"{c.title}"' for c in liked_cards[:3]]
        p1_subjects = (
            f" Reflecting on your selections—including pieces like {', '.join(titles)}—your visual affinity "
            f"demonstrates a keen appreciation for intentional storytelling over transient flash trends."
        )

    p1 = (
        f"Your aesthetic profile centers on {words_str} work, crystallizing into the identity of {archetype}. "
        f"Rather than following generic commercial trends, your selections reveal a visual dialogue defined by "
        f"intentional structure, artistic restraint, and aesthetic maturity.{p1_subjects}"
    )

    p2 = (
        f"Technically, your preference for {line_phrase} executed in {color_phrase} establishes a refined visual rhythm. "
        f"Anchored by a {comp_phrase}, this design approach prioritizes skin breathability and negative space. "
        f"The interplay between pigment and untouched skin turns your natural body contours into an active design element, "
        f"ensuring the tattoo moves gracefully with your anatomy rather than fighting against it."
    )

    p3 = (
        f"Translating this vision onto human skin requires an artist with proven mastery in {technique}. "
        f"Because ink naturally settles and expands microscopically within the dermis over the years, executing this aesthetic "
        f"at an appropriate physical scale with disciplined needle depth is paramount. When crafted with respect for line hierarchy "
        f"and skin longevity, your tattoo will evolve into a timeless, museum-grade signature piece."
    )

    narrative = f"{p1}\n\n{p2}\n\n{p3}"

    return TasteProfileResult(
        profile_id=profile_id,
        descriptive_words=req.descriptive_words,
        line_weight=req.line_weight,
        color_approach=req.color_approach,
        composition=req.composition,
        archetype=archetype,
        archetype_subtitle=subtitle,
        summary=summary,
        narrative=narrative,
        aesthetic_traits=_build_aesthetic_traits(req),
        consultation_advice=_build_consultation_advice(req),
        placement_insights=_build_placement_insights(req),
    )


async def build_taste_profile_result_async(profile_id: str, req: TasteProfileRequest) -> TasteProfileResult:
    """
    Async builder that provides LLM narrative synthesis when configured,
    with an immediate fallback to the editorial rule engine.
    """
    result = build_taste_profile_result(profile_id, req)
    api_key = getattr(settings, "api_key", None)
    if not api_key:
        return result

    try:
        from app.core.llm_client import get_client
        client = get_client()

        deck_by_id = {c.id: c for c in _DEFAULT_STYLE_DECK}
        liked_titles = [deck_by_id[cid].title for cid in req.liked_card_ids if cid in deck_by_id][:4]
        liked_ctx = f"\nLiked reference pieces: {', '.join(liked_titles)}" if liked_titles else ""

        prompt = (
            f"You are the master tattoo art director and aesthetic curator at Corpus.\n"
            f"A client completed their visual taste profile with the following diagnostic:\n"
            f"- Archetype: {result.archetype} ({result.archetype_subtitle})\n"
            f"- Style keywords: {', '.join(w.value for w in req.descriptive_words)}\n"
            f"- Line weight preference: {req.line_weight}\n"
            f"- Color approach: {req.color_approach}\n"
            f"- Composition: {req.composition}{liked_ctx}\n\n"
            f"Write an eloquent, 3-paragraph editorial critique deconstructing their personal tattoo taste profile. "
            f"Paragraph 1: Discuss the visual psychology, mood, and distinct identity of their aesthetic leanings. "
            f"Paragraph 2: Explain the technical chemistry between their chosen linework, palette, and anatomical composition. "
            f"Paragraph 3: Provide high-level curatorial advice on how to translate this vision into an enduring, museum-quality tattoo on human skin. "
            f"Write in an authoritative, inspiring, and sophisticated tone. Output only the 3 paragraphs separated by double newlines."
        )

        response = await client.aio.models.generate_content(
            model=settings.concierge_model,
            contents=prompt,
        )
        llm_text = (response.text or "").strip()
        if len(llm_text) > 100:
            result.narrative = llm_text
    except Exception as e:
        logger.debug(f"Taste profile LLM narrative enrichment fallback used: {e}")

    return result


def build_summary(req: TasteProfileRequest) -> str:
    words = ", ".join(w.value for w in req.descriptive_words)
    line = _LINE_WEIGHT_PHRASES.get(req.line_weight, f"{req.line_weight} lines")
    color = _COLOR_PHRASES.get(req.color_approach, req.color_approach)
    composition = _COMPOSITION_PHRASES.get(req.composition, f"{req.composition} composition")
    return (
        f"Drawn to {words} work, leaning toward {line} in {color}, "
        f"with a {composition}."
    )
