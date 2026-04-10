import httpx
from typing import List
from app.core.config import settings


RIOT_BASE_URL = "https://americas.api.riotgames.com"


async def fetch_match_ids(puuid: str, total: int = 50) -> List[str]:
    url = f"{RIOT_BASE_URL}/lol/match/v5/matches/by-puuid/{puuid}/ids"

    headers = {
        "X-Riot-Token": settings.RIOT_API_KEY
    }

    all_matches = []
    start = 0
    batch_size = 10

    async with httpx.AsyncClient() as client:
        while len(all_matches) < total:
            params = {
                "start": start,
                "count": batch_size
            }
            response = await client.get(url, headers=headers, params=params)

            if response.status_code != 200:
                raise Exception(f"Riot API error: {response.text}")

            batch = response.json()

            if not batch:
                break

            all_matches.extend(batch)
            start += batch_size

    return all_matches[:total]