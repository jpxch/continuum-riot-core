from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.version import router as version_router
from app.api.v1.ddragon import router as ddragon_router
from app.api.v1.modes import router as modes_router
from app.api.v1 import jobs
from app.api.v1 import static

router = APIRouter(prefix="/v1")
router.include_router(health_router, tags=["health"])
router.include_router(version_router, tags=["version"])
router.include_router(ddragon_router, tags=["ddragon"])
router.include_router(static.router, tags=["static"])
router.include_router(modes_router, tags=["modes"])
router.include_router(jobs.router, tags=["jobs"])