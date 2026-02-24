"""fix patch_registry discovered_at column

Revision ID: 6d7f9db2b6b1
Revises: 24b217004927
Create Date: 2026-02-23 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6d7f9db2b6b1"
down_revision = "24b217004927"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def upgrade() -> None:
    if _has_column("patch_registry", "discover_at") and not _has_column("patch_registry", "discovered_at"):
        op.alter_column("patch_registry", "discover_at", new_column_name="discovered_at")


def downgrade() -> None:
    if _has_column("patch_registry", "discovered_at") and not _has_column("patch_registry", "discover_at"):
        op.alter_column("patch_registry", "discovered_at", new_column_name="discover_at")
