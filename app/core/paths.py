from __future__ import annotations

from pathlib import Path

from app.core.config import settings


def ddragon_locale_dir(*, patch: str, locale: str) -> Path:
    """
    Layout:
        <STATIC_ROOT>/<patch>/<locale>/
    """
    root = Path(settings.STATIC_ROOT)
    return root / patch / locale

def ddragon_asset_path(*, patch: str, locale: str, filename: str) -> Path:
    return ddragon_locale_dir(patch=patch, locale=locale) / filename