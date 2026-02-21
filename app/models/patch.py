from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PatchRegistry(Base):
    __tablename__ = "patch_registry"

    patch: Mapped[str] = mapped_column(String(32), primary_key=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())