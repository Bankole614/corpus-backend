# Corpus — Backend Saved Taste Styles Sync API Guide

This document specifies the backend endpoints and database schema required to support **Cloud-Synced Saved Taste Cards** across devices for **Corpus**.

---

## 🏛️ Feature Overview

When a user bookmarks a Taste Profile style card in the app, the Flutter app updates the UI optimistically and syncs the bookmark state with the backend. 

* **Offline / Guest Mode**: Bookmarks are saved locally in `SharedPreferences`.
* **Authenticated Mode**: Bookmarks sync automatically across all devices when logged in.

---

## 1. 🗄️ Recommended Database Schema

Create a lightweight junction table or collection in your database:

### Table Name: `user_saved_taste_styles`

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer / UUID | Primary Key, Auto-increment | Unique record ID |
| `user_id` | Foreign Key (User) | NOT NULL, Indexed | Owner user ID |
| `style_id` | String / Text | NOT NULL | Style card ID (e.g., `"deck_01"`) |
| `created_at` | Timestamp | Default NOW() | Timestamp when saved |

* **Unique Constraint**: `UNIQUE(user_id, style_id)` to prevent duplicate bookmarks for the same style card.

---

## 2. 🔌 API Endpoint Specifications

All endpoints require a valid JWT Bearer token in the `Authorization` header:
`Authorization: Bearer <jwt_access_token>`

---

### A. Get All Bookmarked Cards
Retrieves the list of bookmarked style card IDs for the authenticated user.

* **HTTP Method**: `GET`
* **Route**: `/taste-profile/saved`
* **Headers**: `Authorization: Bearer <token>`
* **Response `200 OK`**:
  ```json
  {
    "saved_style_ids": ["deck_01", "deck_04", "deck_09"]
  }
  ```

---

### B. Bookmark a Style Card
Adds a style card ID to the user's saved list.

* **HTTP Method**: `POST`
* **Route**: `/taste-profile/saved`
* **Headers**: `Authorization: Bearer <token>`
* **Request Body**:
  ```json
  {
    "style_id": "deck_01"
  }
  ```
* **Response `200 OK`**:
  ```json
  {
    "saved_style_ids": ["deck_01", "deck_04", "deck_09"]
  }
  ```

---

### C. Remove a Bookmarked Style Card
Removes a style card ID from the user's saved list.

* **HTTP Method**: `DELETE`
* **Route**: `/taste-profile/saved/{style_id}`
* **Headers**: `Authorization: Bearer <token>`
* **Response `200 OK` or `204 No Content`**:
  ```json
  {
    "status": "success"
  }
  ```

---

### D. Bulk Sync Bookmarks (On Login / App Launch)
Merges any style cards saved locally on the device prior to logging in with the cloud database.

* **HTTP Method**: `POST`
* **Route**: `/taste-profile/saved/sync`
* **Headers**: `Authorization: Bearer <token>`
* **Request Body**:
  ```json
  {
    "saved_style_ids": ["deck_01", "deck_05"]
  }
  ```
* **Logic**:
  1. Insert any missing `style_ids` into `user_saved_taste_styles` for `user_id`.
  2. Query the updated complete set of `saved_style_ids` for `user_id`.
  3. Return the union array.
* **Response `200 OK`**:
  ```json
  {
    "saved_style_ids": ["deck_01", "deck_04", "deck_05", "deck_09"]
  }
  ```

---

## 3. 🐍 FastAPI Python Reference Implementation

You can copy and paste this router implementation directly into your FastAPI backend:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List

# Import your auth dependency and DB session here
# from app.auth import get_current_user
# from app.db import get_db

router = APIRouter(prefix="/taste-profile/saved", tags=["Taste Profile Saved"])


class SaveStyleRequest(BaseModel):
    style_id: str


class SyncStyleRequest(BaseModel):
    saved_style_ids: List[str]


@router.get("", response_model=dict)
async def get_saved_taste_styles(current_user = Depends(get_current_user), db = Depends(get_db)):
    """Fetch all saved taste style IDs for the logged-in user."""
    saved_ids = db.query(UserSavedTasteStyle.style_id).filter(
        UserSavedTasteStyle.user_id == current_user.id
    ).all()
    
    return {"saved_style_ids": [s[0] for s in saved_ids]}


@router.post("", response_model=dict)
async def save_taste_style_item(payload: SaveStyleRequest, current_user = Depends(get_current_user), db = Depends(get_db)):
    """Bookmark a new style card."""
    existing = db.query(UserSavedTasteStyle).filter(
        UserSavedTasteStyle.user_id == current_user.id,
        UserSavedTasteStyle.style_id == payload.style_id
    ).first()

    if not existing:
        new_entry = UserSavedTasteStyle(user_id=current_user.id, style_id=payload.style_id)
        db.add(new_entry)
        db.commit()

    saved_ids = db.query(UserSavedTasteStyle.style_id).filter(
        UserSavedTasteStyle.user_id == current_user.id
    ).all()
    
    return {"saved_style_ids": [s[0] for s in saved_ids]}


@router.delete("/{style_id}", response_model=dict)
async def unsave_taste_style_item(style_id: str, current_user = Depends(get_current_user), db = Depends(get_db)):
    """Remove a bookmarked style card."""
    db.query(UserSavedTasteStyle).filter(
        UserSavedTasteStyle.user_id == current_user.id,
        UserSavedTasteStyle.style_id == style_id
    ).delete()
    db.commit()
    
    return {"status": "success"}


@router.post("/sync", response_model=dict)
async def sync_saved_taste_styles(payload: SyncStyleRequest, current_user = Depends(get_current_user), db = Depends(get_db)):
    """Merge local offline bookmarks with user cloud database."""
    for style_id in payload.saved_style_ids:
        existing = db.query(UserSavedTasteStyle).filter(
            UserSavedTasteStyle.user_id == current_user.id,
            UserSavedTasteStyle.style_id == style_id
        ).first()
        if not existing:
            db.add(UserSavedTasteStyle(user_id=current_user.id, style_id=style_id))
    
    db.commit()

    saved_ids = db.query(UserSavedTasteStyle.style_id).filter(
        UserSavedTasteStyle.user_id == current_user.id
    ).all()

    return {"saved_style_ids": [s[0] for s in saved_ids]}
```

---

## 🛠️ Frontend Status

The Flutter frontend implementation in `lib/core/api_client.dart`, `lib/core/saved_style_service.dart`, and `lib/core/auth_service.dart` is **100% complete**. Once you deploy these routes, the app will automatically start syncing bookmarks in the cloud seamlessly!
