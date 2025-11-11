"""Utility functions for rarity, random generation, etc."""
import random
from typing import List, Dict, Optional


# Rarity system with weights
RARITY_WEIGHTS = {
    "Common": 54.899,
    "Uncommon": 25.0,
    "Magic": 8.0,
    "Rare": 4.0,
    "Epic": 3.0,
    "Unique": 2.5,
    "Legendary": 2.0,
    "Mythic": 0.5,
    "God": 0.1,
    "Forbidden": 0.001,
}

# Adjectives for dynamic class naming
ADJECTIVES = [
    "Wise", "Vigilant", "Silent", "Ancient", "Eternal", "Mystic", "Shadow",
    "Golden", "Crimson", "Azure", "Frost", "Flame", "Storm", "Thunder",
    "Divine", "Infernal", "Celestial", "Abyssal", "Primal", "Arcane"
]


def weighted_rarity_choice(preferred_rarity: Optional[str] = None, parent_rarity: Optional[str] = None) -> str:
    """
    Select a rarity based on weights, with optional bias toward preferred rarity.
    If parent_rarity is provided, removes all rarities lower than parent and redistributes weights.
    
    Args:
        preferred_rarity: If provided, increases weight by 50% for that rarity
        parent_rarity: If provided, removes all rarities lower than this and redistributes weights
        
    Returns:
        Selected rarity string
    """
    weights = RARITY_WEIGHTS.copy()
    
    # If parent_rarity is provided, remove all rarities lower than parent
    # and redistribute the percentages proportionally
    if parent_rarity and parent_rarity in RARITY_WEIGHTS:
        # Get the order of rarities
        rarity_order = list(RARITY_WEIGHTS.keys())
        parent_index = rarity_order.index(parent_rarity)
        
        # Remove all rarities below parent's rarity (set weight to 0)
        # CRITICAL: Only keep rarities at parent_index or higher
        for i in range(parent_index):
            lower_rarity = rarity_order[i]
            if lower_rarity in weights:
                weights[lower_rarity] = 0
        
        # Calculate total of remaining (non-zero) weights (parent and above only)
        remaining_weights = {k: v for k, v in weights.items() if v > 0}
        remaining_total = sum(remaining_weights.values())
        
        # Calculate what was removed
        removed_total = sum(RARITY_WEIGHTS[r] for r in rarity_order[:parent_index])
        
        # Redistribute the removed weights proportionally to remaining rarities
        if remaining_total > 0 and removed_total > 0:
            # Scale up remaining weights to maintain relative proportions
            # The removed weight gets distributed proportionally
            scale_factor = (remaining_total + removed_total) / remaining_total
            for rarity in remaining_weights.keys():
                weights[rarity] = weights[rarity] * scale_factor
        
        # Final safety: ensure no lower rarities can be selected
        # Double-check that all rarities below parent are zero
        for i in range(parent_index):
            lower_rarity = rarity_order[i]
            weights[lower_rarity] = 0
    
    if preferred_rarity and preferred_rarity in weights and weights[preferred_rarity] > 0:
        # Boost preferred rarity by 50%
        weights[preferred_rarity] *= 1.5
        # Normalize weights
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total * 100 for k, v in weights.items()}
    
    # Filter out zero weights and convert to cumulative weights
    # IMPORTANT: Only include rarities that are >= parent_rarity
    rarities = [r for r in weights.keys() if weights[r] > 0]
    
    # Final safety check: if parent_rarity is provided, ensure we only have rarities >= parent
    if parent_rarity and parent_rarity in RARITY_WEIGHTS:
        rarity_order = list(RARITY_WEIGHTS.keys())
        parent_index = rarity_order.index(parent_rarity)
        # Filter to only include rarities at parent_index or higher
        rarities = [r for r in rarities if r in rarity_order and rarity_order.index(r) >= parent_index]
    
    if not rarities:
        # Fallback: if all weights are zero, use parent rarity or highest available
        if parent_rarity:
            return parent_rarity
        return list(RARITY_WEIGHTS.keys())[-1]
    
    # Build cumulative weights only from valid rarities
    cumulative_weights = []
    cumulative = 0
    for rarity in rarities:
        if weights[rarity] > 0:  # Double-check weight is positive
            cumulative += weights[rarity]
            cumulative_weights.append(cumulative)
    
    if not cumulative_weights or cumulative_weights[-1] == 0:
        # No valid weights - return parent rarity or highest
        if parent_rarity:
            return parent_rarity
        return list(RARITY_WEIGHTS.keys())[-1]
    
    # Select based on random value
    rand = random.uniform(0, cumulative_weights[-1])
    for i, weight in enumerate(cumulative_weights):
        if rand <= weight:
            selected_rarity = rarities[i]
            # Final safety: verify selected rarity is >= parent_rarity
            if parent_rarity and parent_rarity in RARITY_WEIGHTS:
                rarity_order = list(RARITY_WEIGHTS.keys())
                if selected_rarity in rarity_order:
                    selected_index = rarity_order.index(selected_rarity)
                    parent_index = rarity_order.index(parent_rarity)
                    if selected_index < parent_index:
                        # Selected rarity is lower than parent - return parent instead
                        return parent_rarity
                    # SPECIAL RULE: After Unique, must be strictly higher (not same)
                    unique_index = rarity_order.index("Unique") if "Unique" in rarity_order else 5
                    if parent_index >= unique_index and selected_index <= parent_index:
                        # Parent is Unique or higher, but child is same or lower - force higher
                        if parent_index < len(rarity_order) - 1:
                            return rarity_order[parent_index + 1]
                        else:
                            return parent_rarity  # Can't go higher
            return selected_rarity
    
    # Fallback to last valid rarity
    selected_rarity = rarities[-1]
    # Final safety check
    if parent_rarity and parent_rarity in RARITY_WEIGHTS:
        rarity_order = list(RARITY_WEIGHTS.keys())
        if selected_rarity in rarity_order:
            selected_index = rarity_order.index(selected_rarity)
            parent_index = rarity_order.index(parent_rarity)
            if selected_index < parent_index:
                return parent_rarity
            # SPECIAL RULE: After Unique, must be strictly higher (not same)
            unique_index = rarity_order.index("Unique") if "Unique" in rarity_order else 5
            if parent_index >= unique_index and selected_index <= parent_index:
                # Parent is Unique or higher, but child is same or lower - force higher
                if parent_index < len(rarity_order) - 1:
                    return rarity_order[parent_index + 1]
                else:
                    return parent_rarity  # Can't go higher
    return selected_rarity


def random_adjective() -> str:
    """Get a random adjective for class naming"""
    return random.choice(ADJECTIVES)


def generate_class_id(template_key: str) -> str:
    """Generate a unique class ID based on template"""
    adj = random_adjective().lower()
    return f"class_{template_key}_{adj}"


def rarity_to_stat_multiplier(rarity: str) -> float:
    """
    Convert rarity to stat multiplier for balancing.
    Higher rarity = better stats.
    """
    multipliers = {
        "Common": 1.0,
        "Uncommon": 1.1,
        "Magic": 1.2,
        "Rare": 1.35,
        "Epic": 1.5,
        "Unique": 1.7,
        "Legendary": 2.0,
        "Mythic": 2.5,
        "God": 3.0,
        "Forbidden": 4.0,
    }
    return multipliers.get(rarity, 1.0)

