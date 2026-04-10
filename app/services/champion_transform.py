from typing import Dict, Any, List

ROLE_MAP = {
    "Fighter": "fighter",
    "Tank": "tank",
    "Mage": "mage",
    "Assassin": "assassin",
    "Marksman": "marksman",
    "Support": "support"
}

RESOURCE_MAP = {
    "Mana": "mana",
    "Energy": "energy",
    "None": "none",
    "Rage": "rage",
    "Heat": "heat",
}


def normalize_id(champion_id: str) -> str:
    return champion_id.lower()


def map_roles(tags: List[str]) -> List[str]:
    return [ROLE_MAP.get(tag, tag.lower()) for tag in tags]


def map_resource(partype: str) -> str:
    return RESOURCE_MAP.get(partype, partype.lower())


def transform_champion(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": normalize_id(raw["id"]),
        "key": int(raw["key"]),
        "name": raw["name"],
        "title": raw.get("title"),
        "roles": map_roles(raw.get("tags", [])),
        "resource": map_resource(raw.get("partype", "None")),
        "base": {
            "tags": raw.get("tags", []),
            "partype": raw.get("partype"),
        },
        "stats": {
            "hp": raw.get("stats", {}).get("hp"),
            "mp": raw.get("stats", {}).get("mp"),
            "armor": raw.get("stats", {}).get("armor"),
            "attack_damage": raw.get("stats", {}).get("attackdamage"),
            "move_speed": raw.get("stats", {}).get("movespeed"),
        },
    }