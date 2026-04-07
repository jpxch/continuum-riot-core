from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from fastapi import Request

from app.api.response import success_response


def contract_response(func: Callable) -> Callable:
    """
    Automatically wraps endpoint responses into the contract.

    If the endpoint:
    - returns raw data → wraps into success_response
    - returns already formatted response → passes through
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")

        result = await func(*args, **kwargs)

        # If already structured, pass through
        if isinstance(result, dict) and "status" in result:
            return result

        # Otherwise wrap it
        return success_response(
            request=request,
            data=result,
        )

    return wrapper