from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, case

from app.api.contract import contract_response
from app.api.pagination import paginate_result
from app.db.session import get_db
from app.models.job_run import JobRunRegistry

router = APIRouter()

MAX_LIMIT = 100

VALID_STATUSES = {"success", "failed", "running"}
VALID_JOB_TYPES = {"ddragon_sync"}


def validate_job_type(job_type: Optional[str]):
    if job_type and job_type not in VALID_JOB_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_job_type",
                "message": f"Invalid job_type. Must be one of {sorted(VALID_JOB_TYPES)}",
            },
        )

def validate_status(job_status: Optional[str]):
    if job_status and job_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_status",
                "message": f"Invalid status. Must be one of {sorted(VALID_STATUSES)}",
            },
        )

@router.get("/jobs/recent")
@contract_response
async def get_recent_jobs(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    job_type: Optional[str] = None,
    job_status: Optional[str] = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    if limit > MAX_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_limit",
                "message": f"limit must be <= {MAX_LIMIT}",
            }
        )

    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_offset",
                "message": "offset must be >= 0",
            },
        )

    validate_status(job_status)

    validate_job_type(job_type)


    query = select(JobRunRegistry)

    if job_type:
        query = query.where(JobRunRegistry.job_type == job_type)

    if job_status is not None:
        query = query.where(JobRunRegistry.status == job_status)

    count_query = select(func.count()).select_from(JobRunRegistry)

    if job_type:
        count_query = count_query.where(JobRunRegistry.job_type == job_type)

    if job_status is not None:
        count_query = count_query.where(JobRunRegistry.status == job_status)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = (
        query
        .order_by(desc(JobRunRegistry.created_at))
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)
    jobs = result.scalars().all()

    data = []

    for job in jobs:
        metadata = job.job_metadata or {}

        data.append(
            {
                "id": str(job.id),
                "job_type": job.job_type,
                "status": job.status,
                "patch": metadata.get("patch"),
                "duration_ms": metadata.get("duration_ms"),
                "assets": metadata.get("assets"),
                "started_at": job.started_at,
                "finished_at": job.finished_at,
            }
        )

    data, pagination = paginate_result(
        items=data,
        total=total,
        limit=limit,
        offset=offset,

    )

    return {
        "__data__": data,
        "__meta__": {
            "pagination": pagination
        }
    }


@router.get("/jobs/latest")
@contract_response
async def get_latest_job(
    request: Request,
    job_type: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if job_type not in VALID_JOB_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_job_type",
                "message": f"Invalid job_type. Must be one of {sorted(VALID_JOB_TYPES)}",
            },
        )

    result = await db.execute(
        select(JobRunRegistry)
        .where(JobRunRegistry.job_type == job_type)
        .order_by(desc(JobRunRegistry.created_at))
        .limit(1)
    )

    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "job_not_found",
                "message": f"No job found for job_type '{job_type}'.",
            },
        )

    metadata = job.job_metadata or {}

    return {
        "__data__": {
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
        },
    }


@router.get("/jobs/summary")
@contract_response
async def get_jobs_summary(
    request: Request,
    job_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    validate_job_type(job_type)

    summary_query = select(
        func.count().label("total"),
        func.sum(case((JobRunRegistry.status == "success", 1), else_=0)).label("success"),
        func.sum(case((JobRunRegistry.status == "failed", 1), else_=0)).label("failed"),
        func.sum(case((JobRunRegistry.status == "running", 1), else_=0)).label("running"),
        func.avg(
            case(
                (JobRunRegistry.status.in_(("success", "failed")), JobRunRegistry.job_metadata["duration_ms"].as_integer()),
                else_=None,
            )
        ).label("avg_duration_ms"),
    )

    if job_type:
        summary_query = summary_query.where(JobRunRegistry.job_type == job_type)

    result = await db.execute(summary_query)
    row = result.one()
    data = row._mapping

    return {
        "__data__": {
            "total": int(data["total"] or 0),
            "success": int(data["success"] or 0),
            "failed": int(data["failed"] or 0),
            "running": int(data["running"] or 0),
            "avg_duration_ms": float(data["avg_duration_ms"] or 0),

        },
    }

@router.get("/jobs/failures")
@contract_response
async def get_job_failures(
    request: Request,
    job_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func

    validate_job_type(job_type)

    query = select(
        JobRunRegistry.error_message,
        func.count().label("count"),
    ).where(
        JobRunRegistry.status == "failed"
    )

    if job_type:
        query = query.where(JobRunRegistry.job_type == job_type)

    query = query.group_by(JobRunRegistry.error_message).order_by(func.count().desc())

    result = await db.execute(query)
    rows = result.all()

    failures = [
        {
            "error": row[0] or "unknown",
            "count": row[1],
        }
        for row in rows
    ]

    total_failures = sum(item["count"] for item in failures)

    return {
        "__data__": {
            "total_failures": total_failures,
            "by_error": failures,
        },
    }



@router.get("/jobs/{job_id}")
@contract_response
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "job_not_found",
                "message": f"Job '{job_id}' does not exist.",
            },
        )

    metadata = job.job_metadata or {}

    return {
        "__data__": {
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
        },
        "__data_version__": job.finished_at.isoformat() if job.finished_at else None,
    }

