from __future__ import annotations
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class ChampionMetadata(Base):
    __tablename__ = "champion_metadata"

    champion_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    region: Mapped[str] = mapped_column(String(64), index=True)
    short_bio: Mapped[str] = mapped_column(Text)