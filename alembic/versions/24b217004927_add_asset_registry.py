"""add asset_registry

Revision ID: 24b217004927
Revises: a6673c90b13c
Create Date: 2026-02-22 12:16:01.125795

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '24b217004927'
down_revision = 'a6673c90b13c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    asset_type_enum = postgresql.ENUM(
        "champion",
        "item",
        "rune",
        "summoner",
        name="asset_type_enum",
        create_type=False,
    )
    asset_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "asset_registry",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "patch",
            sa.String(length=32),
            sa.ForeignKey("patch_registry.patch", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "asset_type",
            asset_type_enum,
            nullable=False,
        ),
        sa.Column("locale", sa.String(length=16), nullable=True),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("sha256", sa.Text(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column(
            "checksum_algo",
            sa.String(length=16),
            nullable=False,
            server_default="sha256",
        ),
        sa.Column(
            "downloaded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "patch",
            "asset_type",
            "locale",
            "filename",
            name="uq_asset_identity",
        ),
    )

    op.create_index("ix_asset_patch", "asset_registry", ["patch"])
    op.create_index("ix_asset_type", "asset_registry", ["asset_type"])
    op.create_index("ix_asset_sha256", "asset_registry", ["sha256"])


def downgrade() -> None:
    op.drop_index("ix_asset_sha256", table_name="asset_registry")
    op.drop_index("ix_asset_type", table_name="asset_registry")
    op.drop_index("ix_asset_patch", table_name="asset_registry")
    op.drop_table("asset_registry")
    asset_type_enum = postgresql.ENUM(
        "champion",
        "item",
        "rune",
        "summoner",
        name="asset_type_enum",
    )
    asset_type_enum.drop(op.get_bind(), checkfirst=True)