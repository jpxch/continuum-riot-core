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

    now = datetime.now(timezone.utc)

    job = JobRunRegistry(
        job_type=job_type,
        job_key=job_key,
        status="running",
        started_at=now,
        job_metadata=metadata,
        created_at=now,
    )

    session.add(job)
    await session.flush()
    return job

async def complete_job_success(
    session: AsyncSession,
    job_id,
    metadata: Optional[dict] = None,
):
    now = datetime.now(timezone.utc)

    result = await session.execute(
        select(JobRunRegistry).where(JobRunRegistry.id == job_id)
    )
    job = result.scalar_one()

    duration_ms = int((now - job.started_at).total_seconds() * 1000)

    final_metadata = job.job_metadata or {}
    if metadata:
        final_metadata.update(metadata)

    final_metadata["duration_ms"] = duration_ms

    await session.execute(
        update(JobRunRegistry)
        .where(JobRunRegistry.id == job_id)
        .values(
            status="success",
            finished_at=now,
            job_metadata=final_metadata,
        )
    )

async def complete_job_failure(
    session: AsyncSession,
    job_id,
    error_message: str,
):
    now = datetime.now(timezone.utc)

    result = await session.execute(
        select(JobRunRegistry).where(JobRunRegistry.id == job_id)
    )
    job = result.scalar_one()

    duration_ms = int((now - job.started_at).total_seconds() * 1000)

    final_metadata = job.job_metadata or {}
    final_metadata["duration_ms"] = duration_ms

    await session.execute(
        update(JobRunRegistry)
        .where(JobRunRegistry.id == job_id)
        .values(
            status="failed",
            error_message=error_message,
            finished_at=now,
            job_metadata=final_metadata,
        )
    )