"""add player identity tables

Revision ID: a20ae2841408
Revise: a80417ec8616
Create Date: 2026-04-11 09:37:22.801749

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision indentifiers, used by Alembic.
revision = 'a20ae2841408'
down_revision = 'a80417ec8616'
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy.dialects import postgresql

    op.create_table(
        "riot_account",
        sa.Column("puuid", sa.String(length=100), primary_key=True),
        sa.Column("game_name", sa.String(length=100), nullable=True),
        sa.Column("tag_line", sa.String(length=20), nullable=True),
        sa.Column("riot_region", sa.String(length=20), nullable=True),

        sa.Column("raw_account_payload", postgresql.JSONB, nullable=True),
        sa.Column("account_payload_fetched_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "summoner_profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),

        sa.Column(
            "puuid",
            sa.String(length=100),
            sa.ForeignKey("riot_account.puuid"),
            nullable=False
        ),
        sa.Column("platform_region", sa.String(length=20), nullable=False),

        sa.Column("summoner_id", sa.String(length=100), nullable=True),
        sa.Column("account_id", sa.String(length=100), nullable=True),

        sa.Column("profile_icon_id", sa.Integer(), nullable=True),
        sa.Column("summoner_level", sa.BigInteger(), nullable=True),
        sa.Column("revision_date", sa.BigInteger(), nullable=True),

        sa.Column("raw_summoner_payload", postgresql.JSONB, nullable=True),
        sa.Column("payload_fetched_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)

op.create_index(
    "ix_summoner_profile_puuid_platform",
    "summoner_profile",
    ["puuid", "platform_region"],
    unique=True,
)


def downgrade() -> None:
    op.drop_index(
        "ix_summoner_profile_puuid_platform",
        table_name="summoner_profile"
    )
    op.drop_table("summoner_profile")
    op.drop_table("riot_account")