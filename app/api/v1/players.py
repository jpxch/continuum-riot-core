from fastapi import APIRouter, Request
from app.api.contract import contract_response
from app.services.match_transform import transform_match
from app.services.player_ingestion import fetch_match_ids, fetch_match

router = APIRouter()


@router.post("/players/{puuid}/sync")
@contract_response
async def sync_player(puuid: str, request: Request):
    match_ids = await fetch_match_ids(puuid)

    clean_matches = []

    for match_id in match_ids[:5]:
        match = await fetch_match(match_id)
        clean = transform_match(match)
        clean_matches.append(clean)

    return {
        "__data__": {
            "matches": clean_matches
        }
    }