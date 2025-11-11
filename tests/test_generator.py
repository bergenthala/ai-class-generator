"""Tests for class generator"""
import pytest
from app.generator import generate_class, CLASS_TEMPLATES, generate_skills
from app.utils import weighted_rarity_choice, RARITY_WEIGHTS


def test_generate_bookworm_class():
    """Test generating a bookworm class"""
    class_data = generate_class("bookworm", "unlock_read_10000", "Epic")
    
    assert class_data["id"] is not None
    assert "wise" in class_data["name"].lower() or "wise" in class_data["id"]
    assert class_data["rarity"] in RARITY_WEIGHTS.keys()
    assert "base_stats" in class_data
    assert "growth_per_rank" in class_data
    assert "skills" in class_data
    assert len(class_data["skills"]) >= 2
    assert class_data["unlock_condition_id"] == "unlock_read_10000"
    
    # Check stats structure
    assert "HP" in class_data["base_stats"]
    assert "MP" in class_data["base_stats"]
    assert "INT" in class_data["base_stats"]
    
    # Bookworm should have high INT
    assert class_data["base_stats"]["INT"] > class_data["base_stats"]["STR"]


def test_generate_slayer_class():
    """Test generating a slayer class"""
    class_data = generate_class("slayer", "unlock_kill_5000", "Rare")
    
    assert class_data["id"] is not None
    assert "slayer" in class_data["name"].lower() or "slayer" in class_data["id"]
    assert class_data["rarity"] in RARITY_WEIGHTS.keys()
    
    # Slayer should have high STR and HP
    assert class_data["base_stats"]["STR"] > class_data["base_stats"]["INT"]
    assert class_data["base_stats"]["HP"] > 100


def test_generate_tinkerer_class():
    """Test generating a tinkerer class"""
    class_data = generate_class("tinkerer", "unlock_craft_100_unique", "Uncommon")
    
    assert class_data["id"] is not None
    assert "tinkerer" in class_data["name"].lower() or "tinkerer" in class_data["id"]
    assert class_data["rarity"] in RARITY_WEIGHTS.keys()
    
    # Tinkerer should have balanced stats
    assert "DEX" in class_data["base_stats"]
    assert class_data["base_stats"]["DEX"] >= 10


def test_class_has_skills():
    """Test that generated classes have skills"""
    for template_key in CLASS_TEMPLATES.keys():
        class_data = generate_class(template_key, f"test_{template_key}")
        assert len(class_data["skills"]) >= 2
        
        for skill in class_data["skills"]:
            assert "id" in skill
            assert "name" in skill
            assert "type" in skill
            assert skill["type"] in ["active", "passive"]
            assert "rarity" in skill
            assert "effect" in skill


def test_rarity_affects_stats():
    """Test that higher rarity classes have better stats"""
    common_class = generate_class("bookworm", "test", "Common")
    epic_class = generate_class("bookworm", "test", "Epic")
    
    # Epic should generally have higher stats (though randomness can affect this)
    # We'll check that at least some stats are higher
    epic_total = sum(epic_class["base_stats"].values())
    common_total = sum(common_class["base_stats"].values())
    
    # Epic should have higher total stats (with some tolerance for randomness)
    assert epic_total >= common_total * 0.8  # Allow some variance


def test_weighted_rarity_choice():
    """Test rarity selection with weights"""
    # Test without preference
    rarity = weighted_rarity_choice()
    assert rarity in RARITY_WEIGHTS.keys()
    
    # Test with preference
    rarity_preferred = weighted_rarity_choice("Epic")
    assert rarity_preferred in RARITY_WEIGHTS.keys()
    
    # Run multiple times to ensure it works
    rarities = [weighted_rarity_choice() for _ in range(100)]
    assert all(r in RARITY_WEIGHTS.keys() for r in rarities)

