from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Integer,
    Enum as SAEnum,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ModeFamily(str, Enum):
    SR = "sr"
    ARAM = "aram"
    TFT = "tft"
    ROTATING = "rotating"


class ModeStatus(str, Enum):
    READY = "ready"
    PARTIAL = "partial"
    FAILED = "failed"


class ModeRegistry(Base):
    __tablename__ = "mode_registry"

    __table_args__ = (
        Index("ix_mode_registry_family", "mode_family"),
    )

    mode_key: Mapped[str] = mapped_column(String(32), pimary_key=True)

    mode_family: Mapped[ModeFamily] = mapped_column(
        SAEnum(
            ModeFamily,
            name="mode_family_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )

    display_name: Mapped[str] = mapped_column(String(128), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    first_seen_patch: Mapped[str | None] = mapped_column(
        String(32),
        ForeignKey("patch_registry.patch", ondelete="SET NULL"),
        nullable=True,
    )

    last_seen_patch: Mapped[str | None] = mapped_column(
        String(32),
        ForeignKey("patch_registry.patch", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

class ModePatchRegistry(Base):
    __tablename__ = "mode_patch_registry"

    __table_args__ = (
        Index("ix_mode_patch_registry_status", "status"),
    )

    mode_key: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("mode_registry.mode_key", ondelete="CASCADE"),
        primary_key=True,
    )

    patch: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("patch_registry.patch", ondelete="CASADE"),
        primary_key=True,
    )

    status: Mapped[ModeStatus] = mapped_column(
        SAEnum(
            ModeStatus,
            name="mode_status_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )

    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

class ModeQueueBinding(Base):
    __tablename__ = "mode_queue_binding"

    __table_args__ = (
        UniqueConstraint("queue_id", name="uq_mode_queue_binding_queue_id"),
        Index("ix_mode_queue_binding_mode_key", "mode_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoinrement=True)

    mode_key: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("mode_registry.mode_key", ondelete="CASCADE"),
        nullable=False,
    )

    queue_id: Mapped[int] = mapped_column(Integer, nullable=False)

    queue_description: Mapped[str | None] = mapped_column(String(256), nullable=True)