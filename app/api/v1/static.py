from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.response import success_response
from app.models.asset import AssetType
from app.services.static_read import (
    get_current_patch,
    load_asset_json,
    asset_exists,
    REQUIRED_ASSETS,
)
from app.core.config import settings

router = APIRouter()

@router.get("/patch")
async def read_patch(
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

    readiness = {}
    for asset_type in REQUIRED_ASSETS.keys():
        readiness[asset_type.value] = await asset_exists(
            session,
            patch,
            asset_type,
        )

    return success_response(
        request,
        data={
            "currentPatch": patch,
            "locale": settings.DEFAULT_LOCALE,
            "assets": readiness,
        },
        data_version=patch,
    )

@router.get("/champions")
async def read_champions(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    try:
        patch = await get_current_patch(session)
        data = await load_asset_json(session, AssetType.CHAMPION)

        return success_response(
            request,
            data=data,
            data_version=patch,
        )
    except RuntimeError as e:
        raise handle_runtime_error(e)

@router.get("/items")
async def read_items(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    try:
        patch = await get_current_patch(session)
        data = await load_asset_json(session, AssetType.ITEM)
        return success_response(
            request,
            data=data,
            data_version=patch,
        )
    except RuntimeError as e:
        raise handle_runtime_error(e)

@router.get("/runes")
async def read_runes(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    try:
        patch = await get_current_patch(session)
        data = await load_asset_json(session, AssetType.RUNE)
        return success_response(
            request,
            data=data,
            data_version=patch,
        )
    except RuntimeError as e:
        raise handle_runtime_error(e)

@router.get("/summoners")
async def read_summoners(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    try:
        patch = await get_current_patch(session)
        data = await load_asset_json(session, AssetType.SUMMONER)
        return success_response(
            request,
            data=data,
            data_version=patch,
        )
    except RuntimeError as e:
        raise handle_runtime_error(e)

def handle_runtime_error(e: RuntimeError) -> HTTPException:
    code = str(e)
    if code == "NO_CURRENT_PATCH":
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": code,
                "message": "No current patch available.",
            },
        )

    if code == "ASSET_NOT_READY":
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": code,
                "message": "Requested asset not yet ingested.",
            },
        )

    if code == "FILE_MISSING":
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": code,
                "message": "Asset registry entry exists but file is missing.",
            },
        )

    if code == "INVALID_JSON":
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": code,
                "message": "Asset file is corrupted or invalid JSON.",
            },
        )

    if code == "UNKNOWN_ASSET_TYPE":
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": code,
                "message": "Requested asset type is not supported.",
            },
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "code": "UNKNOWN_ERROR",
            "message": "Unexpected error occurred.",
        },
    )
