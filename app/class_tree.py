"""Class tree generation and management system"""
import random
import uuid
from typing import Dict, List, Any, Optional
from app.generator import generate_class, CLASS_TEMPLATES
from app.utils import RARITY_WEIGHTS, weighted_rarity_choice
from app.rules import UNLOCK_RULES


# Base classes that players can start with
BASE_CLASSES = {
    "warrior": {
        "name": "Warrior",
        "description": "Master of combat and strength",
        "base_stats": {"HP": 120, "MP": 50, "STR": 18, "INT": 5, "DEX": 10},
        "rarity": "Common"
    },
    "priest": {
        "name": "Priest",
        "description": "Healer and protector of the light",
        "base_stats": {"HP": 80, "MP": 150, "STR": 6, "INT": 16, "DEX": 8},
        "rarity": "Common"
    },
    "mage": {
        "name": "Mage",
        "description": "Wielder of arcane magic",
        "base_stats": {"HP": 70, "MP": 180, "STR": 4, "INT": 20, "DEX": 6},
        "rarity": "Common"
    },
    "thief": {
        "name": "Thief",
        "description": "Shadow and stealth expert",
        "base_stats": {"HP": 90, "MP": 80, "STR": 10, "INT": 8, "DEX": 18},
        "rarity": "Common"
    },
    "wanderer": {
        "name": "Wanderer",
        "description": "Free from class restrictions",
        "base_stats": {"HP": 100, "MP": 100, "STR": 10, "INT": 10, "DEX": 10},
        "rarity": "Common"
    }
}


def generate_class_tree(num_classes: int = 50) -> Dict[str, Any]:
    """
    Generate a complete class tree with unlock rules.
    Supports multi-level trees with depth up to 10 (representing rarity levels).
    
    Args:
        num_classes: Number of classes to generate (excluding base classes)
        
    Returns:
        Dictionary containing:
        - base_classes: The 5 starting classes
        - generated_classes: List of generated classes with unlock rules
        - tree_structure: Connections between classes
    """
    generated_classes = []
    unlock_rules = []
    tree_structure = {
        "base_classes": list(BASE_CLASSES.keys()),
        "connections": []  # List of (from_class, to_class, condition_id) tuples
    }
    
    # Event types for unlock conditions
    event_types = ["read_book", "kill_monster", "craft_item", "explore", "meditate", 
                   "complete_quest", "defeat_boss", "discover_secret", "master_skill"]
    
    # Track which classes have been generated to avoid duplicates
    generated_class_names = set()
    generated_class_ids = set()  # Track class IDs to prevent duplicates
    
    # Track classes by base class and level for multi-level tree
    class_tree_by_base = {key: [] for key in BASE_CLASSES.keys()}
    
    # Track which classes already have a parent (to prevent multiple parents)
    classes_with_parents = set()  # Set of class IDs that already have a parent connection
    
    # Rarity progression (10 levels)
    rarity_levels = ["Common", "Uncommon", "Magic", "Rare", "Epic", 
                     "Unique", "Legendary", "Mythic", "God", "Forbidden"]
    
    # Track minimum requirements per base class
    # Base class must have: 1 Common, 1 Uncommon, 2 higher tiers (Magic or above) DIRECTLY connected
    min_requirements = {
        "Common": 1,
        "Uncommon": 1,
        "Higher": 2  # Magic, Rare, Epic, Unique, Legendary, Mythic, God, Forbidden
    }
    
    # Track direct children of base classes (level 1 only)
    direct_children_by_base = {key: {"Common": 0, "Uncommon": 0, "Higher": 0} 
                                for key in BASE_CLASSES.keys()}
    
    # Track Common-only paths for each base class
    # Each base class should have a path: base -> Common -> Common -> ... (up to depth 10)
    common_path_by_base = {key: [] for key in BASE_CLASSES.keys()}  # List of class IDs in the Common-only path
    
    # Generate classes - create multi-level trees with depth up to 10
    classes_generated = 0
    target_classes_per_base = num_classes // len(BASE_CLASSES)  # Should be 50
    max_iterations = num_classes * 10  # Increased safety limit to handle skips
    iteration = 0
    requirement_round_robin = 0  # Track which base class to work on for requirements
    
    # Continue until we have target_classes_per_base for each base class
    def all_bases_have_enough():
        for key in BASE_CLASSES.keys():
            count = len([gc for gc in generated_classes 
                        if gc["class_data"].get("base_class") == key])
            if count < target_classes_per_base:
                return False
        return True
    
    while not all_bases_have_enough() and iteration < max_iterations:
        iteration += 1
        
        # Choose base class - prioritize ones that need minimum requirements first
        # Find base classes that still need minimum requirements
        bases_needing_requirements = [
            key for key in BASE_CLASSES.keys()
            if (direct_children_by_base[key]["Common"] < min_requirements["Common"] or
                direct_children_by_base[key]["Uncommon"] < min_requirements["Uncommon"] or
                direct_children_by_base[key]["Higher"] < min_requirements["Higher"])
        ]
        
        # Track classes generated per base class to ensure 50 per base
        # Count actual generated classes (not just in tree structure)
        classes_per_base = {}
        for key in BASE_CLASSES.keys():
            # Count classes that have been successfully generated and added
            classes_per_base[key] = len([gc for gc in generated_classes 
                                        if gc["class_data"].get("base_class") == key])
        target_classes_per_base = num_classes // len(BASE_CLASSES)  # Should be 50
        
        # Choose base class - prioritize ones that need minimum requirements first
        if bases_needing_requirements:
            # Cycle through base classes that need requirements to ensure all get them
            base_class_key = bases_needing_requirements[requirement_round_robin % len(bases_needing_requirements)]
            requirement_round_robin += 1
        else:
            # All base classes have minimum requirements
            # Distribute evenly, but prioritize base classes that have fewer classes
            # Find base classes that haven't reached target yet
            bases_below_target = [
                key for key in BASE_CLASSES.keys()
                if classes_per_base[key] < target_classes_per_base
            ]
            
            if bases_below_target:
                # Prioritize base classes that need more classes
                # Weight by how many classes they still need
                weights = [(target_classes_per_base - classes_per_base[key]) for key in bases_below_target]
                total_weight = sum(weights)
                if total_weight > 0:
                    rand = random.uniform(0, total_weight)
                    cumulative = 0
                    for i, weight in enumerate(weights):
                        cumulative += weight
                        if rand <= cumulative:
                            base_class_key = bases_below_target[i]
                            break
                    else:
                        base_class_key = bases_below_target[0]
                else:
                    base_class_key = bases_below_target[0]
            else:
                # All base classes have reached target, distribute evenly
                base_class_key = list(BASE_CLASSES.keys())[classes_generated % len(BASE_CLASSES)]
        
        # Check if we need to build Common-only path for this base class
        # Each base class should have a path of Common classes going to depth 10
        common_path = common_path_by_base[base_class_key]
        needs_common_path = len(common_path) < 10  # Need 10 Common classes in the path (depth 10)
        
        # Initialize Common path variables (will be set if needed)
        common_path_parent = None
        common_path_level = None
        
        # Check if we need to fulfill minimum requirements for DIRECT children of this base class
        needs_common = direct_children_by_base[base_class_key]["Common"] < min_requirements["Common"]
        needs_uncommon = direct_children_by_base[base_class_key]["Uncommon"] < min_requirements["Uncommon"]
        needs_higher = direct_children_by_base[base_class_key]["Higher"] < min_requirements["Higher"]
        
        # Decide generation type: minimum requirements > normal generation (which includes Common path building)
        # Force specific rarity if minimum requirements not met for DIRECT children
        if needs_common:
            target_rarity = "Common"
            must_be_direct_child = True
            build_common_path_this_iteration = False
        elif needs_uncommon:
            target_rarity = "Uncommon"
            must_be_direct_child = True
            build_common_path_this_iteration = False
        elif needs_higher:
            # Choose a higher tier rarity (Magic or above) - must be direct child
            # We need 2 higher tier classes, so check how many we already have
            higher_count = direct_children_by_base[base_class_key]["Higher"]
            if higher_count == 0:
                # First higher tier - choose a lower one (Magic, Rare, or Epic)
                higher_rarities = ["Magic", "Rare", "Epic"]
            else:
                # Second higher tier - can be any higher tier
                higher_rarities = ["Magic", "Rare", "Epic", "Unique", "Legendary", "Mythic", "God", "Forbidden"]
            target_rarity = random.choice(higher_rarities)
            must_be_direct_child = True
            build_common_path_this_iteration = False
        else:
            # Normal generation - choose level/rarity naturally
            # Can connect to any existing class (including Common path nodes), but must be same tier or higher
            # If Common path is incomplete, prioritize extending it to ensure it reaches level 10
            target_rarity = None
            must_be_direct_child = False
            build_common_path_this_iteration = False
            
            # Check if we should extend the Common path during normal generation
            # Priority: Ensure Common path reaches level 10 for all base classes
            # Use probability-based approach, but with high probabilities to ensure completion
            if needs_common_path:
                # Calculate what level the Common path should be at
                # The path should have classes at levels 1, 2, 3, ..., 10
                # So if we have N classes, the next should be at level N+1
                expected_path_level = len(common_path) + 1
                
                if len(common_path) == 0:
                    # Common path doesn't exist yet - high probability to start it
                    if random.random() < 0.7:  # 70% chance to start Common path
                        build_common_path_this_iteration = True
                        common_path_parent = base_class_key
                        common_path_level = 1
                else:
                    # Common path exists but incomplete - prioritize extending it
                    # Higher probability when path is less complete
                    completion_ratio = len(common_path) / 10.0
                    if completion_ratio < 0.5:
                        # Less than 50% complete - high priority (75% chance)
                        extend_probability = 0.75
                    elif completion_ratio < 0.8:
                        # 50-80% complete - medium-high priority (65% chance)
                        extend_probability = 0.65
                    else:
                        # 80%+ complete - still prioritize to finish (60% chance)
                        extend_probability = 0.6
                    
                    if random.random() < extend_probability:
                        build_common_path_this_iteration = True
                        common_path_parent = common_path[-1]
                        # Find parent's level
                        parent_candidate = next((c for c in class_tree_by_base[base_class_key] 
                                               if c["class_id"] == common_path_parent), None)
                        if parent_candidate:
                            parent_level = parent_candidate.get("level", 1)
                            # Always increment by exactly 1 to ensure we get every level (1-10)
                            # The path should have one class at each level
                            common_path_level = parent_level + 1
                            # Ensure we don't exceed level 10
                            common_path_level = min(common_path_level, 10)
                            # CRITICAL: Ensure we're building to the next expected level in sequence
                            # The expected level should be len(common_path) + 1
                            if common_path_level < expected_path_level:
                                # If calculated level is lower than expected, use expected
                                common_path_level = expected_path_level
                            elif common_path_level > expected_path_level:
                                # If calculated level is higher, something's wrong - use expected
                                common_path_level = expected_path_level
                        else:
                            # Fallback - use expected level (should be len(common_path) + 1)
                            common_path_level = min(expected_path_level, 10)
        
        # Determine parent and level
        if must_be_direct_child:
            # Forced rarity to meet minimum requirements - MUST be direct child of base (level 1)
            level = 1  # Direct children are always level 1
            rarity = target_rarity
            parent_class = base_class_key  # Always connect directly to base class
        elif build_common_path_this_iteration:
            # Building Common-only path as part of normal generation
            # Use pre-calculated parent and level
            parent_class = common_path_parent
            level = common_path_level
            rarity = "Common"  # Force Common rarity for path extension
        else:
            # Normal generation - can connect to any existing class
            # Build deeper trees by connecting to existing classes
            if len(class_tree_by_base[base_class_key]) == 0:
                # No classes yet - this shouldn't happen if minimum requirements were met
                # But if it does, connect to base class
                parent_class = base_class_key
                level = 1
            else:
                # Choose a parent from existing classes in this base's tree
                # Prefer classes at lower levels to build depth, but allow any level < 10
                # EXCLUDE Forbidden classes (they are end nodes - no children)
                available_parents = [c for c in class_tree_by_base[base_class_key] 
                                   if c.get("level", 1) < 10 and 
                                   c.get("rarity") != "Forbidden"]  # Max depth 10, exclude Forbidden
                if available_parents:
                    # If Common path is incomplete, give strong preference to Common path nodes
                    # This helps ensure the path gets built to level 10
                    weights = []
                    for c in available_parents:
                        base_weight = 1.0 / (c.get("level", 1) + 1)
                        # Boost weight if this is part of the Common path and path is incomplete
                        if needs_common_path and c["class_id"] in common_path:
                            # Strong boost for Common path nodes, especially the last one
                            if len(common_path) > 0 and c["class_id"] == common_path[-1]:
                                base_weight *= 3.0  # 3x boost for the last Common path node
                            else:
                                base_weight *= 2.0  # 2x boost for other Common path nodes
                        weights.append(base_weight)
                    
                    total_weight = sum(weights)
                    rand = random.uniform(0, total_weight)
                    cumulative = 0
                    parent_candidate = available_parents[0]  # Default
                    for i, weight in enumerate(weights):
                        cumulative += weight
                        if rand <= cumulative:
                            parent_candidate = available_parents[i]
                            break
                    
                    parent_class = parent_candidate["class_id"]
                    parent_level = parent_candidate.get("level", 1)
                    
                    # Get parent's rarity FIRST to ensure child is same or higher
                    parent_rarity = None
                    parent_rarity_index = 0
                    if "rarity" in parent_candidate:
                        parent_rarity = parent_candidate["rarity"]
                        parent_rarity_index = rarity_levels.index(parent_rarity) if parent_rarity in rarity_levels else 0
                    else:
                        # Try to find from generated classes
                        parent_gen_class = next((gc for gc in generated_classes 
                                                if gc["class_data"]["id"] == parent_class), None)
                        if parent_gen_class:
                            parent_rarity = parent_gen_class["class_data"]["rarity"]
                            parent_rarity_index = rarity_levels.index(parent_rarity) if parent_rarity in rarity_levels else 0
                    
                    # Child must be same tier or higher than parent
                    # Level must be higher than parent to build depth (up to depth 10)
                    # Always increment level to build depth - no staying at same level
                    if parent_level < 10:
                        # Prefer incrementing by 1, but sometimes skip a level for variety
                        if parent_level < 9 and random.random() < 0.2:
                            level = parent_level + 2  # Skip a level occasionally
                        else:
                            level = parent_level + 1  # Normal increment
                    else:
                        # Parent is already at max depth, can't go deeper
                        level = 10
                    
                    level = min(level, 10)  # Cap at max depth
                    
                    # CRITICAL: Ensure level corresponds to at least parent's rarity
                    # Level 1 = Common (index 0), Level 2 = Uncommon (index 1), etc.
                    # So level = rarity_index + 1
                    min_level_for_parent_rarity = parent_rarity_index + 1  # Minimum level to match parent's rarity
                    
                    # Calculate desired level (parent_level + 1 or +2)
                    desired_level = level
                    
                    # Ensure desired level is at least high enough for parent's rarity
                    if desired_level < min_level_for_parent_rarity:
                        # Level is too low - must be at least parent's rarity level
                        desired_level = min_level_for_parent_rarity
                    
                    # Cap at max depth
                    level = min(desired_level, 10)
                    
                    # Choose rarity using weighted_rarity_choice with parent rarity adjustment
                    # This ensures percentages are adjusted (Common removed if parent is Uncommon+, etc.)
                    # IMPORTANT: weighted_rarity_choice should only return rarities >= parent_rarity
                    rarity = weighted_rarity_choice(None, parent_rarity)
                    rarity_index = rarity_levels.index(rarity) if rarity in rarity_levels else parent_rarity_index
                    
                    # CRITICAL ENFORCEMENT: rarity_index MUST be >= parent_rarity_index
                    # If weighted_rarity_choice somehow returned a lower rarity, force it up
                    if rarity_index < parent_rarity_index:
                        rarity_index = parent_rarity_index
                        rarity = rarity_levels[rarity_index]
                    
                    # SPECIAL RULE: After Unique rarity, child MUST be higher (not same)
                    # Unique is index 5, so if parent is Unique (5) or higher, child must be > parent
                    unique_index = rarity_levels.index("Unique") if "Unique" in rarity_levels else 5
                    if parent_rarity_index >= unique_index:
                        # Parent is Unique or higher - child MUST be strictly higher
                        if rarity_index <= parent_rarity_index:
                            # Child is same or lower - force it to be higher
                            if parent_rarity_index < len(rarity_levels) - 1:
                                rarity_index = parent_rarity_index + 1
                                rarity = rarity_levels[rarity_index]
                            else:
                                # Parent is already at max rarity - can't go higher
                                # This shouldn't happen if Forbidden is excluded, but handle it
                                rarity_index = parent_rarity_index
                                rarity = rarity_levels[rarity_index]
                    
                    # Adjust level to match rarity (level = rarity_index + 1)
                    # But ensure level is ALWAYS higher than parent_level (never same)
                    calculated_level = rarity_index + 1
                    if calculated_level <= parent_level:
                        # Level would be same or lower than parent - force it higher
                        calculated_level = parent_level + 1
                        # Recalculate rarity to match the higher level
                        if calculated_level <= len(rarity_levels):
                            rarity_index = calculated_level - 1
                            rarity = rarity_levels[rarity_index]
                        else:
                            rarity_index = len(rarity_levels) - 1
                            rarity = rarity_levels[rarity_index]
                    
                    level = min(calculated_level, 10)  # Cap at max depth
                    
                    # Store parent rarity for weight adjustment (will be used in generate_class)
                    parent_rarity_for_weights = parent_rarity
                else:
                    # Fallback to base class
                    parent_class = base_class_key
                    level = 1
                    parent_rarity = None
                    parent_rarity_index = 0
                    parent_rarity_for_weights = None  # Base class - use normal weights
                    
                    # Choose rarity based on level
                    if level <= len(rarity_levels):
                        rarity = rarity_levels[level - 1]
                    else:
                        rarity = weighted_rarity_choice()  # Fallback
        
        # Choose event type for unlock
        event_type = random.choice(event_types)
        
        # Determine threshold based on rarity and level (higher rarity = higher threshold)
        base_thresholds = {
            "Common": (10, 50),
            "Uncommon": (50, 200),
            "Magic": (200, 500),
            "Rare": (500, 1000),
            "Epic": (1000, 3000),
            "Unique": (3000, 5000),
            "Legendary": (5000, 8000),
            "Mythic": (8000, 12000),
            "God": (12000, 20000),
            "Forbidden": (20000, 50000)
        }
        
        threshold_range = base_thresholds.get(rarity, (10, 50))
        threshold = random.randint(threshold_range[0], threshold_range[1])
        
        # Use count or distinct_count
        agg_type = random.choice(["count", "distinct_count"])
        
        # Generate class using a random template or create a new one
        template_key = random.choice(list(CLASS_TEMPLATES.keys()))
        
        # Create unique unlock rule ID
        rule_id = f"unlock_gen_{uuid.uuid4().hex[:8]}"
        
        # Generate the class
        try:
            # If we're forcing a rarity for minimum requirements, use exact rarity
            if must_be_direct_child:
                # Set a flag to force exact rarity in generator
                import app.generator as gen_module
                gen_module._force_exact_rarity = True
                preferred_rarity_for_gen = rarity
                # For minimum requirements, don't adjust weights (use base class)
                gen_module._parent_rarity_for_weights = None
            else:
                gen_module._force_exact_rarity = False
                preferred_rarity_for_gen = None
                # Pass parent rarity to adjust weight percentages
                # If parent exists and is not base class, adjust weights
                if parent_class != base_class_key and 'parent_rarity_for_weights' in locals() and parent_rarity_for_weights:
                    gen_module._parent_rarity_for_weights = parent_rarity_for_weights
                else:
                    gen_module._parent_rarity_for_weights = None
            
            class_data = generate_class(template_key, rule_id, preferred_rarity_for_gen)
            
            # Check if this class ID already exists (prevent duplicate classes)
            if class_data["id"] in generated_class_ids:
                # This class was already generated - skip
                # Don't increment classes_generated, but continue to try generating another
                continue
            
            # Check if this class already has a parent (prevent multiple parents)
            if class_data["id"] in classes_with_parents:
                # This class already has a parent - skip adding another connection
                # Don't increment classes_generated, but continue to try generating another
                continue
            
            # CRITICAL: Override class_data rarity with our calculated rarity
            # This ensures the rarity we calculated (with parent enforcement) is used
            class_data["rarity"] = rarity
            class_data["level"] = level  # Also ensure level is set correctly
            
            # If we're forcing a rarity for minimum requirements, ensure it matches exactly
            if must_be_direct_child:
                # Override the rarity to match what we need (safety check)
                if class_data["rarity"] != rarity:
                    class_data["rarity"] = rarity
                # Clear the flag
                gen_module._force_exact_rarity = False
            
            # Ensure unique class name
            base_name = class_data["name"]
            if base_name in generated_class_names:
                # Add suffix to make unique
                suffix = random.randint(1, 999)
                base_name = f"{base_name} {suffix}"
            
            generated_class_names.add(base_name)
            generated_class_ids.add(class_data["id"])  # Track class ID
            
            # Modify class to have unique name based on evolution path and level
            # All classes are connected to a base class
            if parent_class in BASE_CLASSES:
                class_data["name"] = f"{base_name} ({BASE_CLASSES[parent_class]['name']} Lv.{level})"
            else:
                # Find the base class for this tree
                base_for_tree = base_class_key
                class_data["name"] = f"{base_name} ({BASE_CLASSES[base_for_tree]['name']} Lv.{level})"
            class_data["evolves_from"] = parent_class
            class_data["level"] = level
            class_data["base_class"] = base_class_key
            
            # Create unlock rule
            unlock_rule = {
                "id": rule_id,
                "match": {"event_name": event_type},
                "agg": agg_type,
                "threshold": threshold,
                "result_template": template_key,
                "preferred_rarity": rarity,
                "generated_class_id": class_data["id"],
                "parent_class": parent_class,
                "level": level
            }
            
            generated_classes.append({
                "class_data": class_data,
                "unlock_rule": unlock_rule
            })
            
            unlock_rules.append(unlock_rule)
            
            # Mark this class as having a parent (prevent multiple parents)
            classes_with_parents.add(class_data["id"])
            
            # Add to tree structure - all connected to base class
            tree_structure["connections"].append({
                "from": parent_class,
                "to": class_data["id"],
                "condition_id": rule_id,
                "type": "evolution",
                "level": level
            })
            
            # Track this class in the tree
            class_tree_by_base[base_class_key].append({
                "class_id": class_data["id"],
                "level": level,
                "parent": parent_class,
                "rarity": rarity
            })
            
            # Update rarity counts for DIRECT children only (parent is base class)
            # IMPORTANT: Only count if parent is base class (direct child, should be level 1)
            if parent_class == base_class_key:
                # Double-check this is actually a direct child (level 1)
                if level == 1:
                    if rarity == "Common":
                        direct_children_by_base[base_class_key]["Common"] += 1
                    elif rarity == "Uncommon":
                        direct_children_by_base[base_class_key]["Uncommon"] += 1
                    elif rarity in ["Magic", "Rare", "Epic", "Unique", "Legendary", "Mythic", "God", "Forbidden"]:
                        direct_children_by_base[base_class_key]["Higher"] += 1
            
            # If this is part of the Common-only path, add it to the path
            # Also check if we're extending the path naturally (parent is last in path and we're Common)
            current_path = common_path_by_base[base_class_key]
            expected_path_level = len(current_path) + 1
            
            if build_common_path_this_iteration and rarity == "Common":
                # Verify this is at the expected level for the path
                # The path should have classes at levels 1, 2, 3, ..., 10
                if level == expected_path_level:
                    common_path_by_base[base_class_key].append(class_data["id"])
                else:
                    # Level doesn't match - this shouldn't happen if logic is correct
                    # But add it anyway if it's close (within 1 level) to help complete the path
                    if abs(level - expected_path_level) <= 1 and level <= 10:
                        common_path_by_base[base_class_key].append(class_data["id"])
            elif (not build_common_path_this_iteration and 
                  rarity == "Common" and 
                  parent_class in current_path and 
                  len(current_path) < 10):
                # Natural extension: parent is in Common path, we're Common, path is incomplete
                # Check if parent is the last in the path (extending the path)
                # And verify we're at the expected level
                if len(current_path) > 0 and current_path[-1] == parent_class:
                    if level == expected_path_level:
                        common_path_by_base[base_class_key].append(class_data["id"])
                    elif abs(level - expected_path_level) <= 1 and level <= 10:
                        # Close enough - add it to help complete the path
                        common_path_by_base[base_class_key].append(class_data["id"])
            
            classes_generated += 1
                
        except Exception as e:
            print(f"Error generating class: {e}")
            continue
    
    return {
        "base_classes": BASE_CLASSES,
        "generated_classes": generated_classes,
        "unlock_rules": unlock_rules,
        "tree_structure": tree_structure
    }


def get_class_tree_for_player(player_id: str) -> Dict[str, Any]:
    """
    Get or generate the class tree for a specific player.
    In a real system, this would be stored per player/session.
    For now, we'll generate it fresh each time.
    """
    # Generate 50 classes per base class
    # 5 base classes × 50 classes = 250 total classes
    # This ensures enough classes for depth 10 trees with branching
    result = generate_class_tree(num_classes=250)
    
    return result

