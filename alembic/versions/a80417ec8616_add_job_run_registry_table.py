"""add job_run_registry table

Revision ID: a80417ec8616
Revise: 76cb22759f36
Create Date: 2026-03-01 03:18:04.240981

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision indentifiers, used by Alembic.
revision = 'a80417ec8616'
down_revision = '76cb22759f36'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_run_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("job_key", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index("ix_job_run_registry_job_type", "job_run_registry", ["job_type"])
    op.create_index("ix_job_run_registry_job_key", "job_run_registry", ["job_key"])
    op.create_index("ix_job_run_registry_status", "job_run_registry", ["status"])
    op.create_index(
        "ix_job_run_type_started_desc",
        "job_run_registry",
        ["job_type", "started_at"],
    )


def downgrade() -> None:
    op.drop_table("job_run_registry")