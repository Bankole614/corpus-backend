from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.db.models import Artist, TasteProfile
from app.models.artist import ArtistCreate, ArtistMatch, ArtistOut
from app.models.taste_profile import DescriptiveWord
from app.services.artist_matching_service import artist_tags, score_match

router = APIRouter(prefix="/artists", tags=["artists"])


def _to_out(artist: Artist) -> ArtistOut:
    return ArtistOut(
        id=artist.id,
        name=artist.name,
        contact_url=artist.contact_url,
        bio=artist.bio,
        style_tags=list(artist_tags(artist)),
        line_weight=artist.line_weight,
        color_approach=artist.color_approach,
        composition=artist.composition,
    )


@router.post("", response_model=ArtistOut)
async def create_artist(request: ArtistCreate, db: AsyncSession = Depends(get_session)) -> ArtistOut:
    """
    Add an artist to the directory. No auth/admin gate yet — see README.
    Do not expose this endpoint publicly without one.
    """
    artist = Artist(
        name=request.name,
        contact_url=request.contact_url,
        bio=request.bio,
        style_tags=",".join(w.value for w in request.style_tags),
        line_weight=request.line_weight,
        color_approach=request.color_approach,
        composition=request.composition,
    )
    db.add(artist)
    await db.commit()
    await db.refresh(artist)
    return _to_out(artist)


@router.get("", response_model=list[ArtistOut])
async def list_artists(db: AsyncSession = Depends(get_session)) -> list[ArtistOut]:
    result = await db.execute(select(Artist).order_by(Artist.created_at))
    return [_to_out(a) for a in result.scalars().all()]


@router.get("/{artist_id}", response_model=ArtistOut)
async def get_artist(artist_id: str, db: AsyncSession = Depends(get_session)) -> ArtistOut:
    result = await db.execute(select(Artist).where(Artist.id == artist_id))
    artist = result.scalar_one_or_none()
    if artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    return _to_out(artist)


@router.get("/match/{profile_id}", response_model=list[ArtistMatch])
async def match_artists(
    profile_id: str, limit: int = 10, db: AsyncSession = Depends(get_session)
) -> list[ArtistMatch]:
    """Rank artists in the directory against a previously submitted taste profile."""
    profile_result = await db.execute(select(TasteProfile).where(TasteProfile.id == profile_id))
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Taste profile not found")

    profile_words = {DescriptiveWord(w) for w in profile.descriptive_words.split(",") if w}

    artists_result = await db.execute(select(Artist))
    artists = artists_result.scalars().all()

    matches = [
        ArtistMatch(
            artist=_to_out(artist),
            match_score=score_match(
                artist_tags(artist),
                artist.line_weight,
                artist.color_approach,
                artist.composition,
                profile_words,
                profile.line_weight,
                profile.color_approach,
                profile.composition,
            ),
        )
        for artist in artists
    ]
    matches.sort(key=lambda m: m.match_score, reverse=True)
    return matches[:limit]
