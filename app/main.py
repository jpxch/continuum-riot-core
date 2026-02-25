from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.router import router as v1_router
from app.api.response import error_response
from app.core.config import settings
from app.core.logging import configure_logging, new_request_id, set_request_id

configure_logging(settings.SERVICE_NAME, settings.ENV)

app = FastAPI(
    title=settings.SERVICE_NAME,
    version="0.1.0",
)

app.include_router(v1_router)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("x-request-id") or new_request_id()
    set_request_id(rid)
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            request,
            code="INTERNAL_ERROR",
            message="An unexpected error occured.",
        ),
    )