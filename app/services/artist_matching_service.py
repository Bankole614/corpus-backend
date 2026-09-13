"""
Artist matching.

Deliberately simple for v1: score = number of overlapping style tags, plus a
bonus point each for matching line_weight / color_approach / composition.
No embeddings, no ML — a fixed small vocabulary doesn't need it yet. Revisit
if/when the style vocabulary grows beyond the current six DescriptiveWord
values or artists want free-text style descriptions.
"""

from app.db.models import Artist
from app.models.taste_profile import DescriptiveWord


def score_match(
    artist_tags: set[DescriptiveWord],
    artist_line_weight: str,
    artist_color_approach: str,
    artist_composition: str,
    profile_words: set[DescriptiveWord],
    profile_line_weight: str,
    profile_color_approach: str,
    profile_composition: str,
) -> int:
    score = len(artist_tags & profile_words)
    if artist_line_weight == profile_line_weight:
        score += 1
    if artist_color_approach == profile_color_approach:
        score += 1
    if artist_composition == profile_composition:
        score += 1
    return score


def artist_tags(artist: Artist) -> set[DescriptiveWord]:
    return {DescriptiveWord(w) for w in artist.style_tags.split(",") if w}
