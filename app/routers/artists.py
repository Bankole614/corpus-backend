from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.deps import get_admin_user
from app.db.models import Artist, TasteProfile, User
from app.models.admin import AdminArtistUpdate
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
async def create_artist(
    request: ArtistCreate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_session),
) -> ArtistOut:
    """
    Add an artist to the directory. Requires admin privileges or valid X-Admin-Key header.
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


@router.put("/{artist_id}", response_model=ArtistOut)
async def update_artist(
    artist_id: str,
    update: AdminArtistUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_session),
) -> ArtistOut:
    """Update artist details. Requires admin privileges or X-Admin-Key header."""
    result = await db.execute(select(Artist).where(Artist.id == artist_id))
    artist = result.scalar_one_or_none()
    if artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")

    if update.name is not None:
        artist.name = update.name
    if update.contact_url is not None:
        artist.contact_url = update.contact_url
    if update.bio is not None:
        artist.bio = update.bio
    if update.style_tags is not None:
        artist.style_tags = ",".join(w.value for w in update.style_tags)
    if update.line_weight is not None:
        artist.line_weight = update.line_weight
    if update.color_approach is not None:
        artist.color_approach = update.color_approach
    if update.composition is not None:
        artist.composition = update.composition

    await db.commit()
    await db.refresh(artist)
    return _to_out(artist)


@router.delete("/{artist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artist(
    artist_id: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_session),
) -> None:
    """Remove an artist from the directory. Requires admin privileges or X-Admin-Key header."""
    result = await db.execute(select(Artist).where(Artist.id == artist_id))
    artist = result.scalar_one_or_none()
    if artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")

    await db.delete(artist)
    await db.commit()
