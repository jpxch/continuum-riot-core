from fastapi import APIRouter, Depends, Request, HTTPException
from uuid import UUID
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
            "id": str(job.id),
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

@router.get("/jobs/latest")
async def get_latest_job(
    request: Request,
    job_type: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JobRunRegistry)
        .where(JobRunRegistry.job_type == job_type)
        .order_by(desc(JobRunRegistry.created_at))
        .limit(1)
    )

    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    metadata = job.job_metadata or {}

    return success_response(
        request,
        data={
            "id": str(job.id),
            "job_type": job.job_type,
            "job_key": job.job_key,
            "status": job.status,
            "error": job.error_message,
            "started_at": job.started_at,
            "finished_at": job.finished_at,

            "patch": metadata.get("patch"),
            "locale": metadata.get("locale"),
            "duration_ms": metadata.get("duration_ms"),
            "assets": metadata.get("assets"),

            "metadata": metadata,
        }
    )


@router.get("/jobs/{job_id}")
async def get_job_by_id(
    job_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(JobRunRegistry).where(JobRunRegistry.id == job_id)
    )

    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    metadata = job.job_metadata or {}

    return success_response(
        request,
        data={
            "id": str(job.id),
            "job_type": job.job_type,
            "job_key": job.job_key,
            "status": job.status,
            "error": job.error_message,
            "started_at": job.started_at,
            "finished_at": job.finished_at,

            "patch": metadata.get("patch"),
            "locale": metadata.get("locale"),
            "duration_ms": metadata.get("duration_ms"),
            "assets": metadata.get("assets"),

            "metadata": metadata,
        }
    )

