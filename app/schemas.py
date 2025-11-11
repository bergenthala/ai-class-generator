"""Pydantic schemas for API requests and responses"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


# Event Schemas
class EventCreate(BaseModel):
    """Schema for creating an event"""
    user_id: str = Field(..., description="Player ID")
    event_name: str = Field(..., description="Name of the event (e.g., 'read_book')")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional event metadata")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp (defaults to now)")


class EventResponse(BaseModel):
    """Schema for event response"""
    id: str
    user_id: str
    event_name: str
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime

    class Config:
        from_attributes = True


# Player Stats Schemas
class PlayerFeatures(BaseModel):
    """Schema for player features/stats"""
    user_id: str
    event_counts: Dict[str, Dict[str, Any]]


# Class Schemas
class Skill(BaseModel):
    """Schema for a skill"""
    id: str
    name: str
    type: str  # "active" or "passive"
    rarity: str
    effect: str


class ClassResponse(BaseModel):
    """Schema for a generated class"""
    id: str
    name: str
    rarity: str
    description: str
    base_stats: Dict[str, int]
    growth_per_rank: Dict[str, int]
    skills: List[Skill]
    unlock_condition_id: str


class PlayerClassResponse(BaseModel):
    """Schema for player's unlocked class (includes metadata)"""
    id: str
    user_id: str
    class_data: ClassResponse
    unlock_condition_id: Optional[str]
    unlocked_at: datetime

    class Config:
        from_attributes = True


# Unlock Schemas
class UnlockCheckResponse(BaseModel):
    """Schema for unlock check response"""
    player_id: str
    new_unlocks: List[str]  # List of class IDs that were just unlocked
    message: str


# Story Generation Schemas
class StoryGenerationRequest(BaseModel):
    """Schema for story generation request"""
    context: str
    player_class: str
    action: Optional[str] = None
    player_id: Optional[str] = None


class StoryGenerationResponse(BaseModel):
    """Schema for story generation response"""
    story_text: str

