from fastapi import APIRouter, Request
from app.api.contract import contract_response
from app.services.player_ingestion import fetch_match_ids

router = APIRouter()


@router.post("/players/{puuid}/sync")
@contract_response
async def sync_player(puuid: str, request: Request):
    match_ids = await fetch_match_ids(puuid)

    matches = []

    for match_id in match_ids[:5]:
        match = await fetch_match(match_id)
        matches.append(match)

    return {
        "__data__": {
            "puuid": puuid,
            "matches_fetched": len(matches),
            "sample_match": matches[0] if matches else None
        }
    }