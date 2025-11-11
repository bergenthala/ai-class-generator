"""Class and skill generation logic"""
from typing import Dict, Any, List
import uuid
from app.utils import (
    weighted_rarity_choice,
    random_adjective,
    generate_class_id,
    rarity_to_stat_multiplier
)


# Class templates define base stats, growth patterns, and skill themes
CLASS_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "bookworm": {
        "name_prefix": "The Wise",
        "description_template": "A sage shrouded in ink and parchment. Bonuses to knowledge and spell power.",
        "base_stats": {"HP": 80, "MP": 200, "STR": 6, "INT": 18, "DEX": 8},
        "growth_per_rank": {"HP": 10, "MP": 30, "STR": 1, "INT": 4, "DEX": 1},
        "skill_themes": ["knowledge", "magic", "wisdom"],
        "preferred_rarity": "Epic"
    },
    "slayer": {
        "name_prefix": "The Slayer",
        "description_template": "A warrior forged in battle. Excels in combat and destruction.",
        "base_stats": {"HP": 150, "MP": 50, "STR": 20, "INT": 5, "DEX": 12},
        "growth_per_rank": {"HP": 25, "MP": 5, "STR": 5, "INT": 1, "DEX": 2},
        "skill_themes": ["combat", "damage", "berserker"],
        "preferred_rarity": "Rare"
    },
    "tinkerer": {
        "name_prefix": "The Tinkerer",
        "description_template": "A master craftsman who bends materials to their will. Expert in creation and modification.",
        "base_stats": {"HP": 100, "MP": 120, "STR": 8, "INT": 15, "DEX": 16},
        "growth_per_rank": {"HP": 15, "MP": 20, "STR": 2, "INT": 3, "DEX": 3},
        "skill_themes": ["crafting", "engineering", "innovation"],
        "preferred_rarity": "Uncommon"
    }
}


# Skill templates by theme
SKILL_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "knowledge": [
        {"name": "Omniscience", "type": "active", "effect": "Reveals entire map and buffs INT by 50% for 60s"},
        {"name": "Memorize", "type": "passive", "effect": "+10% XP from reading activities"},
        {"name": "Eidetic Memory", "type": "passive", "effect": "Never forgets learned recipes or patterns"}
    ],
    "magic": [
        {"name": "Arcane Mastery", "type": "passive", "effect": "+25% spell damage and +15% MP regeneration"},
        {"name": "Mana Surge", "type": "active", "effect": "Instantly restores 50% MP, 2min cooldown"},
        {"name": "Spell Weaving", "type": "active", "effect": "Combines two spells into a more powerful effect"}
    ],
    "wisdom": [
        {"name": "Ancient Knowledge", "type": "passive", "effect": "+20% experience gain from all sources"},
        {"name": "Meditation", "type": "active", "effect": "Restores HP and MP over 30s, can move while active"}
    ],
    "combat": [
        {"name": "Bloodlust", "type": "passive", "effect": "Each kill increases damage by 2% (stacks up to 10x)"},
        {"name": "Execute", "type": "active", "effect": "Deals 300% damage to enemies below 30% HP"},
        {"name": "Battle Frenzy", "type": "active", "effect": "Doubles attack speed for 15s, 1min cooldown"}
    ],
    "damage": [
        {"name": "Critical Strike", "type": "passive", "effect": "+15% critical hit chance and +50% critical damage"},
        {"name": "Sundering Blow", "type": "active", "effect": "Ignores 50% of enemy armor, 30s cooldown"}
    ],
    "berserker": [
        {"name": "Rage", "type": "active", "effect": "Takes 20% more damage but deals 50% more damage for 20s"},
        {"name": "Last Stand", "type": "passive", "effect": "When HP drops below 25%, gain 100% damage boost"}
    ],
    "crafting": [
        {"name": "Master Craftsman", "type": "passive", "effect": "All crafted items have +20% quality and durability"},
        {"name": "Rapid Assembly", "type": "active", "effect": "Crafting speed increased by 300% for 5 minutes"},
        {"name": "Innovation", "type": "passive", "effect": "10% chance to create an improved version of any recipe"}
    ],
    "engineering": [
        {"name": "Precision Tools", "type": "passive", "effect": "Reduces material cost by 15% and failure rate by 25%"},
        {"name": "Blueprint Mastery", "type": "passive", "effect": "Can craft items 5 levels above current skill"}
    ],
    "innovation": [
        {"name": "Reverse Engineering", "type": "active", "effect": "Analyze any item to learn its recipe, 1hr cooldown"},
        {"name": "Experimental Design", "type": "passive", "effect": "Can combine materials in new ways to create unique items"}
    ]
}


def generate_skills(skill_themes: List[str], rarity: str, num_skills: int = None) -> List[Dict[str, Any]]:
    """
    Generate skills based on themes and rarity.
    
    Args:
        skill_themes: List of skill theme names
        rarity: Class rarity (affects skill rarity)
        num_skills: Number of skills to generate (default: 2-4 based on rarity)
        
    Returns:
        List of skill dictionaries
    """
    if num_skills is None:
        # Higher rarity = more skills
        rarity_skill_count = {
            "Common": 2,
            "Uncommon": 2,
            "Magic": 3,
            "Rare": 3,
            "Epic": 3,
            "Unique": 4,
            "Legendary": 4,
            "Mythic": 4,
            "God": 5,
            "Forbidden": 5,
        }
        num_skills = rarity_skill_count.get(rarity, 2)
    
    # Collect all available skills from themes
    available_skills = []
    for theme in skill_themes:
        if theme in SKILL_TEMPLATES:
            available_skills.extend(SKILL_TEMPLATES[theme])
    
    # Select random skills (without replacement if possible)
    import random
    selected_skills = random.sample(available_skills, min(num_skills, len(available_skills)))
    
    # Assign skill rarity (usually matches class rarity, but can vary)
    skill_rarities = [rarity] * len(selected_skills)
    # Sometimes upgrade one skill to next tier
    if len(selected_skills) > 1 and random.random() < 0.3:
        rarity_order = ["Common", "Uncommon", "Magic", "Rare", "Epic", "Unique", "Legendary", "Mythic", "God", "Forbidden"]
        if rarity in rarity_order:
            idx = rarity_order.index(rarity)
            if idx < len(rarity_order) - 1:
                skill_rarities[0] = rarity_order[idx + 1]
    
    # Format skills
    formatted_skills = []
    for skill, skill_rarity in zip(selected_skills, skill_rarities):
        formatted_skills.append({
            "id": f"skill_{uuid.uuid4().hex[:8]}",
            "name": skill["name"],
            "type": skill["type"],
            "rarity": skill_rarity,
            "effect": skill["effect"]
        })
    
    return formatted_skills


def generate_class(template_key: str, unlock_condition_id: str, preferred_rarity: str = None) -> Dict[str, Any]:
    """
    Generate a class based on a template key.
    
    Args:
        template_key: Key from CLASS_TEMPLATES
        unlock_condition_id: ID of the unlock condition that triggered this
        preferred_rarity: Preferred rarity (from rule or template)
        
    Returns:
        Complete class dictionary
    """
    if template_key not in CLASS_TEMPLATES:
        raise ValueError(f"Unknown template key: {template_key}")
    
    template = CLASS_TEMPLATES[template_key]
    
    # Determine rarity
    # Check if we need to force exact rarity (for minimum requirements)
    import app.generator as gen_module
    force_exact_rarity = getattr(gen_module, '_force_exact_rarity', False)
    parent_rarity_for_weights = getattr(gen_module, '_parent_rarity_for_weights', None)
    
    if force_exact_rarity and preferred_rarity:
        # For minimum requirements, use exact rarity
        rarity = preferred_rarity
    elif preferred_rarity:
        # Use parent rarity to adjust weights if available
        rarity = weighted_rarity_choice(preferred_rarity, parent_rarity_for_weights)
    elif "preferred_rarity" in template:
        rarity = weighted_rarity_choice(template["preferred_rarity"], parent_rarity_for_weights)
    else:
        # Use parent rarity to adjust weights if available
        rarity = weighted_rarity_choice(None, parent_rarity_for_weights)
    
    # Apply rarity multiplier to stats
    multiplier = rarity_to_stat_multiplier(rarity)
    base_stats = {k: int(v * multiplier) for k, v in template["base_stats"].items()}
    growth_per_rank = {k: int(v * multiplier) for k, v in template["growth_per_rank"].items()}
    
    # Generate class name
    adjective = random_adjective()
    name = f"{adjective} {template['name_prefix']}"
    
    # Generate class ID
    class_id = generate_class_id(template_key)
    
    # Generate skills
    skills = generate_skills(template["skill_themes"], rarity)
    
    # Build description
    description = template["description_template"]
    if rarity in ["Legendary", "Mythic", "God", "Forbidden"]:
        description = f"[{rarity}] {description}"
    
    return {
        "id": class_id,
        "name": name,
        "rarity": rarity,
        "description": description,
        "base_stats": base_stats,
        "growth_per_rank": growth_per_rank,
        "skills": skills,
        "unlock_condition_id": unlock_condition_id
    }

