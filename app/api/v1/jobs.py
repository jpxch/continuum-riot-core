from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.api.response import success_response
from app.db.session import get_db
from app.models.job_run import JobRunRegistry

router = APIRouter()


@router.get("/jobs/recent")
async def get_recent_jobs(
    request: Request,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JobRunRegistry)
        .order_by(desc(JobRunRegistry.created_at))
        .limit(limit)
    )

    jobs = result.scalars().all()

    data = []

    for job in jobs:
        metadata = job.job_metadata or {}

        data.append({
            "job_type": job.job_type,
            "status": job.status,
            "patch": metadata.get("patch"),
            "duration_ms": metadata.get("duration_ms"),
            "assets": metadata.get("assets"),
            "started_at": job.started_at,
            "finished_at": job.finished_at,
        })

    return success_response(
        request,
        data=data,
    )