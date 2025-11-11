"""Unlock evaluation engine"""
from typing import List, Dict, Any, Set
from sqlalchemy.orm import Session
from app.models import Player, PlayerStats, PlayerClass
from app.rules import get_rules
from app.generator import generate_class
import json


def get_player_stats(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Get aggregated player statistics.
    
    Returns:
        Dictionary with event counts: {"event_name": {"count": int, "distinct_count": int, "distinct_values": set}}
    """
    # Get or create player stats - refresh to get latest data
    stats = db.query(PlayerStats).filter(PlayerStats.user_id == user_id).first()
    
    if not stats:
        return {}
    
    # Refresh the object to ensure we have latest data
    db.refresh(stats)
    
    # Convert JSON back to proper format (sets need special handling)
    event_counts = stats.event_counts or {}
    
    # Convert distinct_values lists back to sets for processing
    processed_counts = {}
    for event_name, data in event_counts.items():
        processed_counts[event_name] = {
            "count": data.get("count", 0),
            "distinct_count": data.get("distinct_count", 0),
            "distinct_values": set(data.get("distinct_values", []))
        }
    
    return processed_counts


def evaluate_rule(rule: Dict[str, Any], player_stats: Dict[str, Any]) -> bool:
    """
    Evaluate if a player meets the conditions for an unlock rule.
    
    Args:
        rule: Unlock rule dictionary
        player_stats: Player's aggregated statistics
        
    Returns:
        True if rule conditions are met
    """
    match_conditions = rule.get("match", {})
    event_name = match_conditions.get("event_name")
    
    if not event_name:
        return False
    
    # Get stats for this event
    event_stats = player_stats.get(event_name, {"count": 0, "distinct_count": 0, "distinct_values": set()})
    
    # Check aggregation type
    agg_type = rule.get("agg", "count")
    threshold = rule.get("threshold", 0)
    
    if agg_type == "count":
        return event_stats["count"] >= threshold
    elif agg_type == "distinct_count":
        return event_stats["distinct_count"] >= threshold
    else:
        return False


def check_unlocks(db: Session, user_id: str) -> List[str]:
    """
    Check all unlock rules for a player and generate classes for newly unlocked ones.
    
    Args:
        db: Database session
        user_id: Player ID
        
    Returns:
        List of newly generated class IDs
    """
    # Ensure player exists
    player = db.query(Player).filter(Player.id == user_id).first()
    if not player:
        player = Player(id=user_id)
        db.add(player)
        db.commit()
        db.refresh(player)
    
    # Get player stats
    player_stats = get_player_stats(db, user_id)
    
    # Get all rules
    rules = get_rules()
    
    # Get already unlocked class condition IDs
    existing_unlocks = {
        pc.unlock_condition_id 
        for pc in db.query(PlayerClass).filter(PlayerClass.user_id == user_id).all()
        if pc.unlock_condition_id
    }
    
    # Check each rule
    newly_unlocked = []
    for rule in rules:
        rule_id = rule["id"]
        
        # Skip if already unlocked
        if rule_id in existing_unlocks:
            continue
        
        # Evaluate rule
        if evaluate_rule(rule, player_stats):
            # Generate class
            template_key = rule.get("result_template")
            preferred_rarity = rule.get("preferred_rarity")
            
            if template_key:
                class_data = generate_class(template_key, rule_id, preferred_rarity)
                
                # Save to database
                player_class = PlayerClass(
                    user_id=user_id,
                    class_data=class_data,
                    unlock_condition_id=rule_id
                )
                db.add(player_class)
                db.commit()
                db.refresh(player_class)
                
                newly_unlocked.append(class_data["id"])
    
    return newly_unlocked

