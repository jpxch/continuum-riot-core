from fastapi import APIRouter, Request
from app.api.contract import contract_response
from app.services.player_ingestion import fetch_match_ids

router = APIRouter()


@router.post("/players/{puuid}/sync")
@contract_response
async def sync_player(puuid: str, request: Request):
    match_ids = await fetch_match_ids(puuid)

    return {
        "__data__": {
            "puuid": puuid,
            "matches_found": len(match_ids),
            "match_ids": match_ids
        }
    }