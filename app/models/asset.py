from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Text,
    String,
    Enum as SAEnum,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class AssetType(str, Enum):
    CHAMPION = "champion"
    ITEM = "item"
    RUNE = "rune"
    SUMMONER = "summoner"

class AssetRegistry(Base):
    __tablename__ = "asset_registry"

    __table_args__ = (
        UniqueConstraint(
            "patch",
            "asset_type",
            "locale",
            "filename",
            name="uq_asset_identity",
        ),
        Index("ix_asset_patch", "patch"),
        Index("ix_asset_type", "asset_type"),
        Index("ix_asset_sha256", "sha256"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    patch: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("patch_registry.patch", ondelete="CASCADE"),
        nullable=False,
    )

    asset_type: Mapped[AssetType] = mapped_column(
        SAEnum(AssetType, name="asset_type_enum"),
        nullable=False,
    )

    locale: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
    )

    filename: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sha256: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    checksum_algo: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default="sha256",
    )

    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )