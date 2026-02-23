"""add patch registry

Revision ID: a6673c90b13c
Revises: 24b217004927
Create Date: 2026-02-22 17:52:36.035481

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6673c90b13c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patch_registry",
        sa.Column("patch", sa.String(length=32), primary_key=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "discover_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("patch_registry")