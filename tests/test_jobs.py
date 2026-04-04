import uuid
from datetime import datetime, timezone

from app.models.job_run import JobRunRegistry



async def test_recent_jobs_empty(client):
    response = await client.get("/v1/jobs/recent")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert body["data"] == []
    assert body["meta"]["total"] == 0
    assert body["meta"]["limit"] == 10
    assert body["meta"]["offset"] == 0


async def test_recent_jobs_with_data(client, db_session):
    job = JobRunRegistry(
        job_type="ddragon_sync",
        status="success",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    db_session.add(job)
    await db_session.commit()

    response = await client.get("/v1/jobs/recent")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert len(body["data"]) == 1
    assert body["data"][0]["job_type"] == "ddragon_sync"
    assert body["meta"]["total"] == 1


async def test_recent_jobs_invalid_status(client):
    response = await client.get("/v1/jobs/recent?status=invalid")

    assert response.status_code == 400

    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "INVALID_STATUS"
    assert "Invalid status" in body["error"]["message"]


async def test_recent_jobs_invalid_offset(client):
    response = await client.get("/v1/jobs/recent?offset=-1")

    assert response.status_code == 400

    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "INVALID_OFFSET"
    assert body["error"]["message"] == "offset must be >= 0"


async def test_recent_jobs_invalid_job_type(client):
    response = await client.get("/v1/jobs/recent?job_type=bad_type")

    assert response.status_code == 400

    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "INVALID_JOB_TYPE"
    assert "Invalid job_type" in body["error"]["message"]


async def test_latest_job_success(client, db_session):
    job = JobRunRegistry(
        job_type="ddragon_sync",
        status="success",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    db_session.add(job)
    await db_session.commit()

    response = await client.get("/v1/jobs/latest?job_type=ddragon_sync")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert body["data"]["job_type"] == "ddragon_sync"


async def test_latest_job_not_found(client):
    response = await client.get("/v1/jobs/latest?job_type=ddragon_sync")

    assert response.status_code == 404

    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "JOB_NOT_FOUND"
    assert body["error"]["message"] == "No job found for job_type 'ddragon_sync'."


async def test_latest_job_invalid_job_type(client):
    response = await client.get("/v1/jobs/latest?job_type=bad_type")

    assert response.status_code == 400

    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "INVALID_JOB_TYPE"
    assert "Invalid job_type" in body["error"]["message"]

async def test_get_job_by_id(client, db_session):
    job = JobRunRegistry(
        job_type="ddragon_sync",
        status="success",
        started_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )

    db_session.add(job)
    await db_session.commit()

    response = await client.get(f"/v1/jobs/{job.id}")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert body["data"]["id"] == str(job.id)


async def test_get_job_by_id_not_found(client):
    fake_id = uuid.uuid4()

    response = await client.get(f"/v1/jobs/{fake_id}")

    assert response.status_code == 404

    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "JOB_NOT_FOUND"
    assert body["error"]["message"] == f"Job '{fake_id}' does not exist."


async def test_job_summary(client, db_session):
    from datetime import datetime, timezone
    from app.models.job_run import JobRunRegistry

    jobs = [
        JobRunRegistry(
            job_type="ddragon_sync",
            status="success",
            job_metadata={"duration_ms": 1000},
            started_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        ),
        JobRunRegistry(
            job_type="ddragon_sync",
            status="failed",
            job_metadata={"duration_ms": 2000},
            started_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        ),
    ]
    
    db_session.add_all(jobs)
    await db_session.commit()

    response = await client.get("/v1/jobs/summary")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "success"
    assert body["data"]["total"] == 2
    assert body["data"]["success"] == 1
    assert body["data"]["failed"] == 1