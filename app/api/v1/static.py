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

def error_response(code: str, message: str, status_code: int):
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
        },
    )

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
async def read_champions(session: AsyncSession = Depends(get_db)):
    try:
        return await load_asset_json(session, AssetType.CHAMPION)
    except RuntimeError as e:
        handle_runtime_error(e)

@router.get("/items")
async def read_items(session: AsyncSession = Depends(get_db)):
    try:
        return await load_asset_json(session, AssetType.ITEM)
    except RuntimeError as e:
        handle_runtime_error(e)

@router.get("/runes")
async def read_runes(session: AsyncSession = Depends(get_db)):
    try:
        return await load_asset_json(session, AssetType.RUNE)
    except RuntimeError as e:
        handle_runtime_error(e)

@router.get("/summoners")
async def read_summoners(session: AsyncSession = Depends(get_db)):
    try:
        return await load_asset_json(session, AssetType.SUMMONER)
    except RuntimeError as e:
        handle_runtime_error(e)

def handle_runtime_error(e: RuntimeError):
    code = str(e)
    if code == "NO_CURRENT_PATCH":
        error_response(
            code,
            "No current patch available.",
            status.HTTP_404_NOT_FOUND,
        )

    if code == "ASSET_NOT_READY":
        error_response(
            code,
            "Requested asset not yet ingested.",
            status.HTTP_409_CONFLICT,
        )

    if code == "FILE_MISSING":
        error_response(
            code,
            "Asset registry entry exists but file is missing.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if code == "INVALID_JSON":
        error_response(
            code,
            "Asset file is corrupted or invalid JSON.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if code == "UNKNOWN_ASSET_TYPE":
        error_response(
            code,
            "Requested asset type is not supported.",
            status.HTTP_400_BAD_REQUEST,
        )

    error_response(
        "UNKNOWN_ERROR",
        "Unexpected error occurred.",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
