from __future__ import annotations

from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.response import success_response
from app.services.mode_read import get_current_patch, list_modes_for_patch, get_mode_manifest

router = APIRouter()


@router.get("/modes")
async def read_modes(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    patch = await get_current_patch(session)
    if not patch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NO_CURRENT_PATCH",
                "message": "No current patch is registered.",
            },
        )

    data = await list_modes_for_patch(session, patch)
    return success_response(request, data=data, data_version=patch)


@router.get("/modes/{mode_key}/manifest")
async def read_mode_manifest(
    mode_key: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    patch = await get_current_patch(session)
    if not patch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NO_CURRENT_PATCH",
                "message": "No current patch is registered.",
            },
        )

    manifest = await get_mode_manifest(session, patch, mode_key)
    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "MODE_NOT_FOUND",
                "message": f"Mode '{mode_key}' does not exist.",
            },
        )

    return success_response(
        request,
        data=manifest,
        data_version=patch,
    )