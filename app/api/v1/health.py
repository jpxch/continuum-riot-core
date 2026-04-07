from __future__ import annotations

from fastapi import APIRouter, Request
from app.api.contracts import contract_response

router = APIRouter()


@router.get("/health")
@contract_response
async def health(request: Request):
    return {
        "__data__": {"status": "ok"},
        "__data_version__": "1.0",
    }