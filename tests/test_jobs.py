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
    assert body["detail"]["code"] == "INVALID_STATUS"
    assert "Invalid status" in body["detail"]["message"]


async def test_recent_jobs_invalid_offset(client):
    response = await client.get("/v1/jobs/recent?offset=-1")

    assert response.status_code == 400

    body = response.json()
    assert body["detail"]["code"] == "INVALID_OFFSET"
    assert body["detail"]["message"] == "offset must be >= 0"


async def test_recent_jobs_invalid_job_type(client):
    response = await client.get("/v1/jobs/recent?job_type=bad_type")

    assert response.status_code == 400

    body = response.json()
    assert body["detail"]["code"] == "INVALID_JOB_TYPE"
    assert "Invalid job_type" in body["detail"]["message"]


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
    assert body["detail"]["code"] == "JOB_NOT_FOUND"
    assert body["detail"]["message"] == "No job found for job_type 'ddragon_sync'."


async def test_latest_job_invalid_job_type(client):
    response = await client.get("/v1/jobs/latest?job_type=bad_type")

    assert response.status_code == 400

    body = response.json()
    assert body["detail"]["code"] == "INVALID_JOB_TYPE"
    assert "Invalid job_type" in body["detail"]["message"]

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
    assert body["detail"]["code"] == "JOB_NOT_FOUND"
    assert body["detail"]["message"] == f"Job '{fake_id}' does not exist."