import httpx
from typing import List
from app.core.config import settings


RIOT_BASE_URL = "https://americas.api.riotgames.com"


async def fetch_match_ids(puuid: str, count: int = 10) -> List[str]:
    url = f"{RIOT_BASE_URL}/lol/match/v5/matches/by-puuid/{puuid}/ids"

    headers = {
        "X-Riot-Token": settings.RIOT_API_KEY
    }

    params = {
        "start": 0,
        "count": count
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Riot API error: {response.text}")
        return response.json()