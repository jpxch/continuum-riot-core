from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import Request
from app.core.logging import get_request_id


REQUIRED_META_FIELDS = {
    "resquestId",
    "apiVersion",
    "dataVersion",
    "generatedAt",
}

def success_response(
    request: Request,
    data: Any,
    data_version: str | None = None,
    meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Canonical sucess reponse builder.

    Guarantees:
    - stable envelopment
    - required meta fields always present
    - controlled meta merging
    """

    base_meta = {
        "requestId": get_request_id(),
        "apiVersion": "v1",
        "dataVersion": data_version,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }

    if meta:
        for key in meta:
            if key in REQUIRED_META_FIELDS:
                raise ValueError(
                    f"Meta field '{key}' is reserved and cannot be overridden."
                )
        base_meta.update(meta)

    response = {
        "status": "success",
        "data": data,
        "meta": base_meta,
    }


    return response


def error_response(
    request: Request,
    code: str,
    message: str,
) -> Dict[str, Any]:
    """
    Canonical error response builder.

    Guarantees:
    - stable error shape
    - request correlation via requestId
    """

    return {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "requestId": get_request_id(),
        },
    }