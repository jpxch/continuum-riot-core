from __future__ import annotations

from typing import Any, Dict, List, Tuple


def build_pagination_meta(
    *,
    limit: int,
    offset: int,
    total: int,
) -> Dict[str, int]:
    """
    Standard pagination metadata builder.

    Guarantees:
    - consistent pagination contract
    - no missing fields
    """

    return {
        "limit": limit,
        "offset": offset,
        "total": total

    }

def paginate_result(
    *,
    items: List[Any],
    total: int,
    limit: int,
    offset: int,
) -> Tuple[List[Any], Dict[str, int]]:
    """
    Returns:
    - data
    - pagination meta
    """

    meta = build_pagination_meta(
        limit=limit,
        offset=offset,
        total=total

    )

    return items, meta # meta = pagination