from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from app.core.config import settings
from app.core.logging import get_request_id

def success_response(
    request: Request,
    data: Any,
    data_version: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict:
    response_meta = {
        "requestId": get_request_id(),
        "apiVersion": "v1",
        "dataVersion": data_version,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
    if meta:
        response_meta.update(meta)

    return {
        "status": "success",
        "data": data,
        "meta": response_meta,
    }

def error_response(
    request: Request,
    code: str,
    message: str,
) -> dict:
    return {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "requestId": get_request_id(),
        },
    }
