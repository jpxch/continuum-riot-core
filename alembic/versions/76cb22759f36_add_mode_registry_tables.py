"""add mode registry tables

Revision ID: 76cb22759f36
Revise: 6d7f9db2b6b1
Create Date: 2026-02-24 14:04:32.038399

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision indentifiers, used by Alembic.
revision = '76cb22759f36'
down_revision = '6d7f9db2b6b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    mode_family_enum = postgresql.ENUM(
        "sr",
        "aram",
        "tft",
        "rotating",
        name="mode_family_enum",
        create_type=False,
    )
    mode_status_enum = postgresql.ENUM(
        "ready",
        "partial",
        "failed",
        name="mode_status_enum",
        create_type=False,
    )

    mode_family_enum.create(op.get_bind(), checkfirst=True)
    mode_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "mode_registry",
        sa.Column("mode_key", sa.String(length=32), primary_key=True),
        sa.Column("mode_family", mode_family_enum, nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("first_seen_patch", sa.String(length=32), nullable=True),
        sa.Column("last_seen_patch", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["first_seen_patch"],
            ["patch_registry.patch"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["last_seen_patch"],
            ["patch_registry.patch"],
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "mode_key = lower(mode_key)",
            name="ck_mode_registry_lowercase_key",
        ),
    )

    op.create_index(
        "ix_mode_registry_family",
        "mode_registry",
        ["mode_family"],
    )

    op.create_table(
        "mode_patch_registry",
        sa.Column("mode_key", sa.String(length=32), nullable=False),
        sa.Column("patch", sa.String(length=32), nullable=False),
        sa.Column("status", mode_status_enum, nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["mode_key"],
            ["mode_registry.mode_key"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["patch"],
            ["patch_registry.patch"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("mode_key", "patch"),
    )
    op.create_index(
        "ix_mode_patch_registry_status",
        "mode_patch_registry",
        ["status"],
    )

    op.create_table(
        "mode_queue_binding",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("mode_key", sa.String(length=32), nullable=False),
        sa.Column("queue_id", sa.Integer(), nullable=False),
        sa.Column("queue_description", sa.String(length=256), nullable=True),
        sa.ForeignKeyConstraint(
            ["mode_key"],
            ["mode_registry.mode_key"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "queue_id",
            name="uq_mode_queue_binding_queue_id",
        ),

    )
    op.create_index(
        "ix_mode_queue_binding_mode_key",
        "mode_queue_binding",
        ["mode_key"],
    )


def downgrade() -> None:
    op.drop_index("ix_mode_queue_binding_mode_key", table_name="mode_queue_binding")
    op.drop_table("mode_queue_binding")
    op.drop_index("ix_mode_patch_registry_status", table_name="mode_patch_registry")
    op.drop_table("mode_patch_registry")
    op.drop_index("ix_mode_registry_family", table_name="mode_registry")
    op.drop_table("mode_registry")
    sa.Enum(name="mode_family_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="mode_status_enum").drop(op.get_bind(), checkfirst=True)
