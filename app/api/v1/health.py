from __future__ import annotations

from fastapi import APIRouter, Request
from app.api.response import success_response

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    return success_response(
        request,
        data={"service": "healthy"},
        data_version=None,
    )