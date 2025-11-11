"""SQLAlchemy models for database tables"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Player(Base):
    """Player model"""
    __tablename__ = "players"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    events = relationship("Event", back_populates="player")
    classes = relationship("PlayerClass", back_populates="player")
    stats = relationship("PlayerStats", back_populates="player", uselist=False)


class Event(Base):
    """Event model for player actions"""
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("players.id"), nullable=False, index=True)
    event_name = Column(String, nullable=False, index=True)
    event_metadata = Column("metadata", JSON, nullable=True)  # Column name is "metadata" in DB, but attribute is "event_metadata"
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    player = relationship("Player", back_populates="events")


class PlayerStats(Base):
    """Aggregated player statistics"""
    __tablename__ = "player_stats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("players.id"), unique=True, nullable=False)
    
    # Store aggregated counts as JSON for flexibility
    # Format: {"event_name": {"count": int, "distinct_count": int, "distinct_values": set}}
    event_counts = Column(JSON, default=dict)

    # Relationships
    player = relationship("Player", back_populates="stats")


class PlayerClass(Base):
    """Unlocked classes for players"""
    __tablename__ = "classes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("players.id"), nullable=False, index=True)
    class_data = Column(JSON, nullable=False)  # Full class JSON
    unlock_condition_id = Column(String, nullable=True)
    unlocked_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    player = relationship("Player", back_populates="classes")

