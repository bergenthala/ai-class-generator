"""Event ingestion and aggregation logic"""
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models import Player, Event, PlayerStats
from app.unlock_engine import check_unlocks
from datetime import datetime


def ingest_event(db: Session, user_id: str, event_name: str, metadata: dict = None, timestamp: datetime = None) -> Event:
    """
    Ingest a player event and update aggregated statistics.
    
    Args:
        db: Database session
        user_id: Player ID
        event_name: Name of the event
        metadata: Optional event metadata
        timestamp: Optional event timestamp (defaults to now)
        
    Returns:
        Created Event object
    """
    # Ensure player exists
    player = db.query(Player).filter(Player.id == user_id).first()
    if not player:
        player = Player(id=user_id)
        db.add(player)
        db.commit()
        db.refresh(player)
    
    # Create event
    event = Event(
        user_id=user_id,
        event_name=event_name,
        event_metadata=metadata or {},
        timestamp=timestamp or datetime.utcnow()
    )
    db.add(event)
    db.flush()  # Flush to get event ID, but don't commit yet
    
    # Update aggregated stats (this will commit)
    update_player_stats(db, user_id, event_name, metadata)
    
    # Commit the event as well
    db.commit()
    db.refresh(event)
    
    # Check for unlocks
    check_unlocks(db, user_id)
    
    return event


def update_player_stats(db: Session, user_id: str, event_name: str, metadata: dict = None):
    """
    Update aggregated player statistics for an event.
    
    Args:
        db: Database session
        user_id: Player ID
        event_name: Event name
        metadata: Event metadata (used for distinct counting)
    """
    # Get or create player stats
    stats = db.query(PlayerStats).filter(PlayerStats.user_id == user_id).first()
    
    if not stats:
        stats = PlayerStats(user_id=user_id, event_counts={})
        db.add(stats)
        db.commit()
        db.refresh(stats)
    
    # Get current counts - make a deep copy to avoid mutation issues
    import copy
    event_counts = copy.deepcopy(stats.event_counts) if stats.event_counts else {}
    
    # Initialize event stats if needed
    if event_name not in event_counts:
        event_counts[event_name] = {
            "count": 0,
            "distinct_count": 0,
            "distinct_values": []
        }
    
    # Update count
    event_counts[event_name]["count"] += 1
    
    # Update distinct count (if metadata has a key we track)
    if metadata:
        # For distinct counting, we'll use a key from metadata (e.g., "book_id", "item_id", "monster_id")
        # Default to first value in metadata if no specific key
        distinct_key = None
        for key in ["book_id", "item_id", "monster_id", "crafted_item_id"]:
            if key in metadata:
                distinct_key = metadata[key]
                break
        
        if not distinct_key:
            # Use first metadata value as fallback
            distinct_key = list(metadata.values())[0] if metadata else None
        
        if distinct_key:
            distinct_values = list(event_counts[event_name].get("distinct_values", []))
            if distinct_key not in distinct_values:
                distinct_values.append(distinct_key)
                event_counts[event_name]["distinct_count"] = len(distinct_values)
                event_counts[event_name]["distinct_values"] = distinct_values
    
    # Save updated stats - assign the new dict
    stats.event_counts = event_counts
    # Tell SQLAlchemy that the JSON field has been modified
    flag_modified(stats, "event_counts")
    db.commit()
    db.refresh(stats)  # Ensure stats are refreshed

