from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.deps import get_current_user
from app.db.models import User, UserSavedVault
from app.models.vault import (
    SavedVaultItemCreate,
    SavedVaultItemResponse,
    SavedVaultListResponse,
    VaultBulkSyncRequest,
    VaultItemType,
)

router = APIRouter(prefix="/vault", tags=["Vault"])


async def _fetch_saved_vault_list(user_id: str, db: AsyncSession) -> SavedVaultListResponse:
    result = await db.execute(
        select(UserSavedVault)
        .where(UserSavedVault.user_id == user_id)
        .order_by(UserSavedVault.created_at.desc())
    )
    items = list(result.scalars().all())

    movement_ids = [item.item_id for item in items if item.item_type == VaultItemType.movement.value]
    motif_ids = [item.item_id for item in items if item.item_type == VaultItemType.motif.value]

    saved_responses = [
        SavedVaultItemResponse(
            id=item.id,
            item_id=item.item_id,
            item_type=VaultItemType(item.item_type),
            created_at=item.created_at,
        )
        for item in items
    ]

    return SavedVaultListResponse(
        saved_items=saved_responses,
        movement_ids=movement_ids,
        motif_ids=motif_ids,
    )


@router.get("/saved", response_model=SavedVaultListResponse)
async def get_saved_vault_items(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> SavedVaultListResponse:
    """Retrieve all movements and motifs saved by the current authenticated user."""
    return await _fetch_saved_vault_list(current_user.id, db)


@router.post("/saved", response_model=SavedVaultItemResponse, status_code=status.HTTP_201_CREATED)
async def save_vault_item(
    payload: SavedVaultItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> SavedVaultItemResponse:
    """Save/bookmark a movement or motif for the current user."""
    result = await db.execute(
        select(UserSavedVault).where(
            UserSavedVault.user_id == current_user.id,
            UserSavedVault.item_id == payload.item_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        return SavedVaultItemResponse(
            id=existing.id,
            item_id=existing.item_id,
            item_type=VaultItemType(existing.item_type),
            created_at=existing.created_at,
        )

    new_item = UserSavedVault(
        user_id=current_user.id,
        item_id=payload.item_id,
        item_type=payload.item_type.value,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)

    return SavedVaultItemResponse(
        id=new_item.id,
        item_id=new_item.item_id,
        item_type=VaultItemType(new_item.item_type),
        created_at=new_item.created_at,
    )


@router.delete("/saved/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_vault_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Response:
    """Remove a movement or motif from the user's saved items."""
    await db.execute(
        delete(UserSavedVault).where(
            UserSavedVault.user_id == current_user.id,
            UserSavedVault.item_id == item_id,
        )
    )
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/saved/sync", response_model=SavedVaultListResponse)
async def bulk_sync_saved_vault(
    payload: VaultBulkSyncRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> SavedVaultListResponse:
    """Bulk sync items saved locally on mobile before/after user login."""
    result = await db.execute(
        select(UserSavedVault.item_id).where(UserSavedVault.user_id == current_user.id)
    )
    existing_ids = set(result.scalars().all())

    # Insert movements
    for m_id in payload.movement_ids:
        clean_m_id = m_id.strip()
        if clean_m_id and clean_m_id not in existing_ids:
            db.add(
                UserSavedVault(
                    user_id=current_user.id,
                    item_id=clean_m_id,
                    item_type=VaultItemType.movement.value,
                )
            )
            existing_ids.add(clean_m_id)

    # Insert motifs
    for motif_id in payload.motif_ids:
        clean_motif_id = motif_id.strip()
        if clean_motif_id and clean_motif_id not in existing_ids:
            db.add(
                UserSavedVault(
                    user_id=current_user.id,
                    item_id=clean_motif_id,
                    item_type=VaultItemType.motif.value,
                )
            )
            existing_ids.add(clean_motif_id)

    await db.commit()

    return await _fetch_saved_vault_list(current_user.id, db)
