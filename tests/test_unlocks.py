"""Tests for unlock engine"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.models import Player, Event, PlayerStats, PlayerClass
from app.unlock_engine import check_unlocks, evaluate_rule, get_player_stats
from app.event_service import ingest_event


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_read_10000_books_unlock(db_session):
    """Test that reading 10,000 books unlocks 'The Wise One' class"""
    user_id = "test_player_1"
    
    # Ingest 10,000 book reading events
    for i in range(10000):
        ingest_event(
            db=db_session,
            user_id=user_id,
            event_name="read_book",
            metadata={"book_id": f"book_{i}"}
        )
    
    # Check that class was unlocked
    classes = db_session.query(PlayerClass).filter(PlayerClass.user_id == user_id).all()
    assert len(classes) > 0
    
    # Check that it's a bookworm class
    bookworm_class = None
    for pc in classes:
        if pc.unlock_condition_id == "unlock_read_10000":
            bookworm_class = pc
            break
    
    assert bookworm_class is not None
    assert "bookworm" in bookworm_class.class_data["id"] or "wise" in bookworm_class.class_data["name"].lower()
    assert bookworm_class.class_data["rarity"] in ["Epic", "Unique", "Legendary", "Mythic", "God", "Forbidden"]


def test_kill_5000_monsters_unlock(db_session):
    """Test that killing 5,000 monsters unlocks 'The Slayer' class"""
    user_id = "test_player_2"
    
    # Ingest 5,000 monster kill events
    for i in range(5000):
        ingest_event(
            db=db_session,
            user_id=user_id,
            event_name="kill_monster",
            metadata={"monster_id": f"monster_{i}"}
        )
    
    # Check that class was unlocked
    classes = db_session.query(PlayerClass).filter(PlayerClass.user_id == user_id).all()
    assert len(classes) > 0
    
    # Check that it's a slayer class
    slayer_class = None
    for pc in classes:
        if pc.unlock_condition_id == "unlock_kill_5000":
            slayer_class = pc
            break
    
    assert slayer_class is not None
    assert "slayer" in slayer_class.class_data["id"] or "slayer" in slayer_class.class_data["name"].lower()


def test_craft_100_unique_items_unlock(db_session):
    """Test that crafting 100 unique items unlocks 'The Tinkerer' class"""
    user_id = "test_player_3"
    
    # Ingest 100 unique craft events
    for i in range(100):
        ingest_event(
            db=db_session,
            user_id=user_id,
            event_name="craft_item",
            metadata={"crafted_item_id": f"item_{i}"}
        )
    
    # Check that class was unlocked
    classes = db_session.query(PlayerClass).filter(PlayerClass.user_id == user_id).all()
    assert len(classes) > 0
    
    # Check that it's a tinkerer class
    tinkerer_class = None
    for pc in classes:
        if pc.unlock_condition_id == "unlock_craft_100_unique":
            tinkerer_class = pc
            break
    
    assert tinkerer_class is not None
    assert "tinkerer" in tinkerer_class.class_data["id"] or "tinkerer" in tinkerer_class.class_data["name"].lower()


def test_rule_evaluation():
    """Test rule evaluation logic"""
    rule = {
        "id": "test_rule",
        "match": {"event_name": "test_event"},
        "agg": "count",
        "threshold": 10
    }
    
    # Test count aggregation
    player_stats = {
        "test_event": {"count": 15, "distinct_count": 5, "distinct_values": set()}
    }
    assert evaluate_rule(rule, player_stats) == True
    
    player_stats = {
        "test_event": {"count": 5, "distinct_count": 5, "distinct_values": set()}
    }
    assert evaluate_rule(rule, player_stats) == False
    
    # Test distinct_count aggregation
    rule_distinct = {
        "id": "test_rule_distinct",
        "match": {"event_name": "test_event"},
        "agg": "distinct_count",
        "threshold": 3
    }
    
    player_stats = {
        "test_event": {"count": 10, "distinct_count": 5, "distinct_values": set(["a", "b", "c", "d", "e"])}
    }
    assert evaluate_rule(rule_distinct, player_stats) == True

