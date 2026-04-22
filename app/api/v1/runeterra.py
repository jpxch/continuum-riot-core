from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.contract import contract_response
from app.api.v1.static import handle_runtime_error
from app.db.session import get_db
from app.services.lore_read import get_champion_lore, list_champion_lore
from app.services.static_read import get_current_patch

router = APIRouter()

@router.get("/lore")
@contract_response
async def list_champion_stories(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    try:
        patch = await get_current_patch(session)
        data = await list_champion_lore(session)
        return {
            "__data__": data,
            "__data_version__": patch,
        }
    except RuntimeError as e:
        raise handle_runeterra_error(e)

@router.get("/lore/{champion_id}")
@contract_response
async def get_champion_story(
    champion_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    try:
        patch = await get_current_patch(session)
        data = await get_champion_lore(session, champion_id)
        return {
            "__data__": data,
            "__data_version__": patch,
        }
    except RuntimeError as e:
        raise handle_runeterra_error(e)


def handle_runeterra_error(e: RuntimeError) -> HTTPException:
    code = str(e)
    if code == "CHAMPION_NOT_FOUND":
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": code,
                "message": "Champion lore entry was not found for the current patch.",
            },
        )

    return handle_runtime_error(e)
