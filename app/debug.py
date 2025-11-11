"""Debug endpoints for viewing unlock rules and class relationships"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from app.database import get_db
from app.rules import get_rules
from app.models import PlayerClass
from app.generator import CLASS_TEMPLATES
from app.class_tree import get_class_tree_for_player, BASE_CLASSES

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/unlock-tree")
async def get_unlock_tree(db: Session = Depends(get_db)):
    """
    Get a tree structure showing all unlock rules and their relationships.
    Returns data for visualizing the unlock system.
    """
    rules = get_rules()
    
    # Get all unlocked classes from database to see what's been generated
    all_unlocked_classes = db.query(PlayerClass).all()
    
    # Build the tree structure
    tree_data = {
        "rules": [],
        "templates": {},
        "unlocked_classes_count": len(all_unlocked_classes)
    }
    
    # Add all rules
    for rule in rules:
        rule_info = {
            "id": rule["id"],
            "event_name": rule["match"].get("event_name"),
            "aggregation": rule["agg"],
            "threshold": rule["threshold"],
            "template_key": rule.get("result_template"),
            "preferred_rarity": rule.get("preferred_rarity"),
            "description": f"{rule['agg']} of {rule['match'].get('event_name')} >= {rule['threshold']}"
        }
        tree_data["rules"].append(rule_info)
    
    # Add template information
    for template_key, template_data in CLASS_TEMPLATES.items():
        tree_data["templates"][template_key] = {
            "name_prefix": template_data["name_prefix"],
            "description": template_data["description_template"],
            "base_stats": template_data["base_stats"],
            "skill_themes": template_data["skill_themes"],
            "preferred_rarity": template_data.get("preferred_rarity")
        }
    
    # Count how many times each template has been unlocked
    template_counts = {}
    for pc in all_unlocked_classes:
        if pc.unlock_condition_id:
            # Find the rule that matches
            for rule in rules:
                if rule["id"] == pc.unlock_condition_id:
                    template_key = rule.get("result_template")
                    if template_key:
                        template_counts[template_key] = template_counts.get(template_key, 0) + 1
                    break
    
    tree_data["template_unlock_counts"] = template_counts
    
    return tree_data


@router.get("/class-tree")
async def get_class_tree(player_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get the complete class tree with AI-generated classes.
    If player_id is provided, shows which classes they've unlocked.
    """
    # Generate class tree
    tree = get_class_tree_for_player(player_id or "default")
    
    # Get unlocked classes if player_id provided
    unlocked_class_ids = set()
    if player_id:
        unlocked = db.query(PlayerClass).filter(PlayerClass.user_id == player_id).all()
        unlocked_class_ids = {pc.class_data.get("id") for pc in unlocked if pc.class_data}
    
    # Mark which classes are unlocked
    for gen_class in tree["generated_classes"]:
        class_id = gen_class["class_data"]["id"]
        gen_class["unlocked"] = class_id in unlocked_class_ids
    
    return tree

