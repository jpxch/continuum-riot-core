from typing import Dict, Any, List


def normalize_player(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "puuid": p["puuid"],
        "summoner_name": p.get("summonerName"),
        "champion": p["championName"].lower(),
        "team_id": p["teamId"],
        "win": p["win"],
        "kills": p["kills"],
        "deaths": p["deaths"],
        "assists": p["assists"],
        "kda": (
            (p["kills"] + p["assists"]) / max(1, p["deaths"])
        ),
        "damage_dealt": p["totalDamageDealtToChampions"],
        "damage_taken": p["totalDamageTaken"],
        "gold": p["goldEarned"],
        "cs": p["totalMinionsKilled"],

        "items": [
            p.get("item0"),
            p.get("item1"),
            p.get("item2"),
            p.get("item3"),
            p.get("item4"),
            p.get("item5"),
            p.get("item6"),
        ],

        "runes": {
            "primary": p.get("perks", {}).get("styles", [{}])[0].get("style"),
            "secondary": p.get("perks", {}).get("styles", [{}])[1].get("style"),
        },
    }

def transform_match(match: Dict[str, Any]) -> Dict[str, Any]:
    info = match["info"]
    metadata = match["metadata"]

    return {
        "match_id": metadata["matchId"],
        "mode": info["gameMode"],
        "duration": info["gameDuration"],

        "players": [
            normalize_player(p)
            for p in info["participants"]
        ],
    }