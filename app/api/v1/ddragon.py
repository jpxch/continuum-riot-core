from fastapi import APIRouter, Depends, BackgroundTasks, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.response import success_response
from app.core.config import settings
from app.db.session import get_db, AsyncSessionLocal
from app.services.ddragon import fetch_latest_patch, set_current_patch
from app.services.static_ingestion import ingest_patch_static_data
from app.services.mode_authority import sync_modes_for_patch
from app.services.job_registry import (
    start_job,
    complete_job_success,
    complete_job_failure,
)

router = APIRouter()

async def run_ddragon_sync_job(patch: str, locale: str):
    async with AsyncSessionLocal() as session:

        job = await start_job(
            session,
            job_type="ddragon_sync",
            job_key=patch,
            metadata={"locale": locale},
        )
        await session.commit()

        try:
            await ingest_patch_static_data(patch=patch, locale=locale)
            await sync_modes_for_patch(patch=patch)

            await complete_job_success(session, job.id)
            await session.commit()

        except Exception as e:
            await complete_job_failure(session, job.id, str(e))
            await session.commit()
            raise


@router.post("/ddragon/sync")
async def ddragon_sync(
    request: Request,
    background_tasks: BackgroundTasks,
    locale: str = Query(default=settings.DEFAULT_LOCALE),
    db: AsyncSession = Depends(get_db),
):
    info = await fetch_latest_patch()
    await set_current_patch(db, info.latest)

    background_tasks.add_task(
        run_ddragon_sync_job,
        patch=info.latest,
        locale=locale,
    )

    return success_response(
        request,
        data={
            "currentPatch": info.latest,
            "locale": locale,
            "ingestionSchedules": True,
            "modeAuthoritySchedules": True,
        },
        data_version=info.latest,
    )
