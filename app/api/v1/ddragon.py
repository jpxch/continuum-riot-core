from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.services.ddragon import fetch_latest_patch, set_current_patch
from app.services.static_ingestion import ingest_patch_static_data
from app.services.mode_authority import sync_modes_for_patch

router = APIRouter()


@router.post("/ddragon/sync")
async def ddragon_sync(
    background_tasks: BackgroundTasks,
    locale: str = Query(default=settings.DEFAULT_LOCALE),
    db: AsyncSession = Depends(get_db),
):
    info = await fetch_latest_patch()
    await set_current_patch(db, info.latest)

    background_tasks.add_task(
        ingest_patch_static_data,
        patch=info.latest,
        locale=locale,
    )

    background_tasks.add_task(
        sync_modes_for_patch,
        patch=info.latest,
    )

    return {
        "status": "ok",
        "currentPatch": info.latest,
        "locale": locale,
        "ingestionScheduled": True,
        "modeAuthorityScheduled": True,
    }
