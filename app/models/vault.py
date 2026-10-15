from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class VaultItemType(str, Enum):
    movement = "movement"
    motif = "motif"


class SavedVaultItemCreate(BaseModel):
    item_id: str = Field(..., description="Unique identifier of the movement or motif")
    item_type: VaultItemType = Field(..., description="Type of vault item: 'movement' or 'motif'")


class SavedVaultItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_id: str
    item_type: VaultItemType
    created_at: datetime


class SavedVaultListResponse(BaseModel):
    saved_items: list[SavedVaultItemResponse]
    movement_ids: list[str]
    motif_ids: list[str]


class VaultBulkSyncRequest(BaseModel):
    movement_ids: list[str] = Field(default_factory=list)
    motif_ids: list[str] = Field(default_factory=list)
