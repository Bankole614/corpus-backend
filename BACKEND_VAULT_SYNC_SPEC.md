# 🏛️ CORPUS — Backend Vault Sync & User Favorites Specification

This specification details the backend database schema, API endpoints, and implementation code required to synchronize a user's saved Vault items (**Art Movements** & **Historic Motifs**) with the `corpus-backend` API.

---

## 💡 How The Vault Works & Architectural Overview

### 1. The Client-Side Vault Catalog (`lib/data/codex_data.dart`)
* **What it is:** A curated, art-historically researched library containing **37 Art Movements** (`CodexMovement`) and **94 Historic Motifs** (`CodexMotif`).
* **Why it is defined on the client:** The Vault catalog itself acts as an immutable reference encyclopedia. Storing the dataset on the client allows **instant zero-latency browsing**, search, filtering, and offline access without making heavy HTTP catalog requests.
* **Image Hosting:** Images are loaded via `CachedNetworkImage` from your static media CDN endpoint (`$baseUrl/static/vault/...`). Once fetched, images are cached on the device's disk.

### 2. The User's Saved Relationship (Backend Sync)
While the art catalog is static, **user interactions with the Vault belong in the user's database profile**:
* When a user taps **Save / Favorite** on a movement or motif, the app records `item_id` (e.g. `'chiaroscuro_baroque'`) and `item_type` (`'movement'` or `'motif'`).
* The client syncs these saved preferences to the backend so that when a user logs in on a new device, their saved Vault collection is restored seamlessly.

---

## 🗄️ 1. Database Schema (`user_saved_vault`)

Add a new table `user_saved_vault` (or `user_favorites`) to your database models.

### SQLAlchemy Model (Python)

```python
import enum
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

class VaultItemType(str, enum.Enum):
    MOVEMENT = "movement"
    MOTIF = "motif"

class UserSavedVault(Base):
    __tablename__ = "user_saved_vault"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(String(100), nullable=False, index=True)  # e.g. 'neoclassicism', 'hannya_mask'
    item_type = Column(Enum(VaultItemType), nullable=False)     # 'movement' or 'motif'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "item_id", name="uq_user_vault_item"),
    )
```

---

## 📝 2. Pydantic Schemas

```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class ItemTypeEnum(str, Enum):
    movement = "movement"
    motif = "motif"

class SavedVaultItemCreate(BaseModel):
    item_id: str = Field(..., example="chiaroscuro_baroque")
    item_type: ItemTypeEnum = Field(..., example="movement")

class SavedVaultItemResponse(BaseModel):
    id: str
    item_id: str
    item_type: ItemTypeEnum
    created_at: datetime

    class Config:
        from_attributes = True

class SavedVaultListResponse(BaseModel):
    saved_items: list[SavedVaultItemResponse]
    movement_ids: list[str]
    motif_ids: list[str]

class VaultBulkSyncRequest(BaseModel):
    movement_ids: list[str] = []
    motif_ids: list[str] = []
```

---

## 🚀 3. FastAPI API Routes (`/vault/saved`)

Create a new router file `routers/vault.py` (or include in `routers/users.py`):

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import UserSavedVault, VaultItemType, User
from schemas import (
    SavedVaultItemCreate,
    SavedVaultItemResponse,
    SavedVaultListResponse,
    VaultBulkSyncRequest
)
from auth_utils import get_current_user

router = APIRouter(prefix="/vault", tags=["Vault"])

@router.get("/saved", response_model=SavedVaultListResponse)
def get_saved_vault_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all movements and motifs saved by the current authenticated user."""
    items = db.query(UserSavedVault).filter(UserSavedVault.user_id == current_user.id).all()
    
    movement_ids = [item.item_id for item in items if item.item_type == VaultItemType.MOVEMENT]
    motif_ids = [item.item_id for item in items if item.item_type == VaultItemType.MOTIF]

    saved_responses = [
        SavedVaultItemResponse(
            id=str(item.id),
            item_id=item.item_id,
            item_type=item.item_type.value,
            created_at=item.created_at
        )
        for item in items
    ]

    return SavedVaultListResponse(
        saved_items=saved_responses,
        movement_ids=movement_ids,
        motif_ids=motif_ids
    )


@router.post("/saved", response_model=SavedVaultItemResponse, status_code=status.HTTP_201_CREATED)
def save_vault_item(
    payload: SavedVaultItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save/bookmark a movement or motif for the current user."""
    existing = db.query(UserSavedVault).filter(
        UserSavedVault.user_id == current_user.id,
        UserSavedVault.item_id == payload.item_id
    ).first()

    if existing:
        return SavedVaultItemResponse(
            id=str(existing.id),
            item_id=existing.item_id,
            item_type=existing.item_type.value,
            created_at=existing.created_at
        )

    new_item = UserSavedVault(
        user_id=current_user.id,
        item_id=payload.item_id,
        item_type=VaultItemType(payload.item_type.value)
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return SavedVaultItemResponse(
        id=str(new_item.id),
        item_id=new_item.item_id,
        item_type=new_item.item_type.value,
        created_at=new_item.created_at
    )


@router.delete("/saved/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def unsave_vault_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a movement or motif from the user's saved items."""
    db.query(UserSavedVault).filter(
        UserSavedVault.user_id == current_user.id,
        UserSavedVault.item_id == item_id
    ).delete(synchronize_session=False)
    
    db.commit()
    return None


@router.post("/saved/sync", response_model=SavedVaultListResponse)
def bulk_sync_saved_vault(
    payload: VaultBulkSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk sync items saved locally on mobile before/after user login."""
    # Insert movements
    for m_id in payload.movement_ids:
        exists = db.query(UserSavedVault).filter(
            UserSavedVault.user_id == current_user.id,
            UserSavedVault.item_id == m_id
        ).first()
        if not exists:
            db.add(UserSavedVault(user_id=current_user.id, item_id=m_id, item_type=VaultItemType.MOVEMENT))

    # Insert motifs
    for motif_id in payload.motif_ids:
        exists = db.query(UserSavedVault).filter(
            UserSavedVault.user_id == current_user.id,
            UserSavedVault.item_id == motif_id
        ).first()
        if not exists:
            db.add(UserSavedVault(user_id=current_user.id, item_id=motif_id, item_type=VaultItemType.MOTIF))

    db.commit()

    # Return updated full list
    return get_saved_vault_items(current_user=current_user, db=db)
```

---

## 📲 4. Mobile Client Integration Summary

The mobile client will handle saved items with a dual-layer strategy:
1. **Instant UI Updates:** Updates local `SharedPreferences` immediately so bookmarking feels instantaneous (0ms lag).
2. **Background Backend Sync:** When logged in, fires API calls (`POST /vault/saved`, `DELETE /vault/saved/{item_id}`) to synchronize state with the server.
3. **On Login:** Invokes `POST /vault/saved/sync` with any offline bookmarks saved before logging in, merging local and cloud collections.
