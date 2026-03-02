from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_run import JobRunRegistry


class JobAlreadyRunningError(Exception):
    pass

async def start_job(
    session: AsyncSession,
    job_type: str,
    job_key: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> JobRunRegistry:

    existing = await session.execute(
        select(JobRunRegistry)
        .where(JobRunRegistry.job_type == job_type)
        .where(JobRunRegistry.status == "running")
    )

    if existing.scalar_one_or_none():
        raise JobAlreadyRunningError(f"Job '{job_type}' already running.")

    job = JobRunRegistry(
        job_type=job_type,
        job_key=job_key,
        status="running",
        started_at=datetime.now(timezone.utc),
        job_metadata=metadata,
        created_at=datetime.now(timezone.utc),
    )

    session.add(job)
    await session.flush()
    return job

async def complete_job_success(
    session: AsyncSession,
    job_id,
):
    await session.execute(
        update(JobRunRegistry)
        .where(JobRunRegistry.id == job_id)
        .values(
            status="success",
            finished_at=datetime.now(timezone.utc),
        )
    )

async def complete_job_failure(
    session: AsyncSession,
    job_id,
    error_message: str,
):
    await session.execute(
        update(JobRunRegistry)
        .where(JobRunRegistry.id == job_id)
        .values(
            status="failed",
            error_message=error_message,
            finished_at=datetime.now(timezone.utc),
        )
    )