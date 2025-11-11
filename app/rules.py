"""Hardcoded unlock rules"""
from typing import Dict, Any, List


# Unlock rule structure:
# {
#   "id": str,
#   "match": {"event_name": str},  # Event to match
#   "agg": str,  # "count" or "distinct_count"
#   "threshold": int,  # Threshold value
#   "result_template": str,  # Template key for class generation
#   "preferred_rarity": str (optional)  # Preferred rarity for generated class
# }

UNLOCK_RULES: List[Dict[str, Any]] = [
    {
        "id": "unlock_read_10000",
        "match": {"event_name": "read_book"},
        "agg": "count",
        "threshold": 10000,
        "result_template": "bookworm",
        "preferred_rarity": "Epic"
    },
    {
        "id": "unlock_kill_5000",
        "match": {"event_name": "kill_monster"},
        "agg": "count",
        "threshold": 5000,
        "result_template": "slayer",
        "preferred_rarity": "Rare"
    },
    {
        "id": "unlock_craft_100_unique",
        "match": {"event_name": "craft_item"},
        "agg": "distinct_count",
        "threshold": 100,
        "result_template": "tinkerer",
        "preferred_rarity": "Uncommon"
    }
]


def get_rules() -> List[Dict[str, Any]]:
    """Get all unlock rules"""
    return UNLOCK_RULES


def get_rule_by_id(rule_id: str) -> Dict[str, Any]:
    """Get a specific rule by ID"""
    for rule in UNLOCK_RULES:
        if rule["id"] == rule_id:
            return rule
    raise ValueError(f"Rule not found: {rule_id}")

