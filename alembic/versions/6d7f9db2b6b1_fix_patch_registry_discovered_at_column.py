"""fix patch_registry discovered_at column

Revision ID: 6d7f9db2b6b1
Revises: 24b217004927
Create Date: 2026-02-23 00:00:00.000000

"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "6d7f9db2b6b1"
down_revision = "24b217004927"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'patch_registry'
          AND column_name = 'discover_at'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'patch_registry'
          AND column_name = 'discovered_at'
    )
    THEN
        ALTER TABLE public.patch_registry
            RENAME COLUMN discover_at TO discovered_at;
    END IF;
END $$;
"""
    )


def downgrade() -> None:
    op.execute(
        """
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'patch_registry'
          AND column_name = 'discovered_at'
    )
    AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'patch_registry'
          AND column_name = 'discover_at'
    )
    THEN
        ALTER TABLE public.patch_registry
            RENAME COLUMN discovered_at TO discover_at;
    END IF;
END $$;
"""
    )
