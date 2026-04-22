from __future__ import annotations
import json
from sqlalchemy.dialects.postgresql import insert
from app.db.session import AsyncSessionLocal
from app.models.asset import AssetRegistry, AssetType
from app.models.lore import ChampionMetadata
from app.core.paths import ddragon_asset_path
from app.core.config import settings
from sqlalchemy import select

REGION_MAP = {
    "Kennen": "Ionia",
    "Akali": "Ionia",
    "Shen": "Ionia",
}