from __future__ import annotations
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.contract import contract_response
from app.services.static_read import load_champion_lore_json, get_current_patch

router = APIRouter()

@router.get("/lore/{champion_id}")
@contract_response
async def get_champion_story(
    champion_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    data = await load_champion_lore_json(session, champion_id)
    return {
        "__data__": data,
        "__data_version__": await get_current_patch(session),
    }