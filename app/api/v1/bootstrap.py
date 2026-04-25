from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.contract import contract_response
from app.api.v1.static import handle_runtime_error
from app.db.session import get_db
from app.services.bootstrap_read import build_bootstrap
from app.services.static_read import get_current_patch

router = APIRouter()


@router.get("/bootstrap")
@contract_response
async def read_bootstrap(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    try:
        patch = await get_current_patch(session)
        data = await build_bootstrap(session)
        return {
            "__data__": data,
            "__data_version__": patch,
        }
    except RuntimeError as e:
        raise handle_runtime_error(e)
