from __future__ import annotations

from contextlib import asynccontextmanager
import asyncio
import contextlib

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException

from app.api.router import router as v1_router
from app.api.response import error_response
from app.core.config import settings
from app.core.logging import configure_logging, new_request_id, set_request_id
from app.services.patch_poller import start_patch_poller

configure_logging(settings.SERVICE_NAME, settings.ENV)

@asynccontextmanager
async def lifespan(app: FastAPI):
    poller_task = None

    if settings.ENABLE_PATCH_POLLER:
        poller_task = await start_patch_poller()

    try:
        yield
    finally:
        if poller_task:
            poller_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await poller_task

app = FastAPI(
    title=settings.SERVICE_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(v1_router)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("x-request-id") or new_request_id()
    set_request_id(rid)
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response


@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    if isinstance(exc.detail, dict):
        code = exc.detail.get("code", "UNKNOWN_ERROR")
        message = exc.detail.get("message", "An error occurred")
    else:
        code = "HTTP_ERROR"
        message = str(exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            request,
            code=code,
            message=message,
        ),
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            request,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
        ),
    )