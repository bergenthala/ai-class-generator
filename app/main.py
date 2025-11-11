"""FastAPI application entrypoint"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from contextlib import asynccontextmanager
import os
from app.database import get_db, init_db
from app.schemas import (
    EventCreate, EventResponse, PlayerFeatures, PlayerClassResponse, UnlockCheckResponse,
    StoryGenerationRequest, StoryGenerationResponse
)
from app.models import Player, PlayerClass, PlayerStats
from app.event_service import ingest_event
from app.unlock_engine import check_unlocks, get_player_stats
from app.story_service import generate_story_text
from app.debug import router as debug_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    init_db()
    yield
    # Shutdown (if needed in future)


# Initialize FastAPI app
app = FastAPI(
    title="AI Class Generator API",
    description="AI-driven system for dynamically generating player classes based on behavior",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include debug router
app.include_router(debug_router)


@app.get("/game")
async def game_page():
    """Serve the interactive game page"""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Game page not found")


@app.get("/debug")
async def debug_page():
    """Serve the debug unlock tree page"""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    debug_path = os.path.join(static_dir, "debug.html")
    if os.path.exists(debug_path):
        return FileResponse(debug_path)
    raise HTTPException(status_code=404, detail="Debug page not found")


@app.get("/")
async def root():
    """Root endpoint - redirects to game or shows API info"""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "AI Class Generator API",
        "version": "1.0.0",
        "game": "/game",
        "api_docs": "/docs",
        "endpoints": {
            "POST /events": "Ingest a player event",
            "GET /player/{id}/features": "Get player statistics",
            "GET /player/{id}/classes": "Get unlocked classes",
            "POST /check-unlocks/{id}": "Manually trigger unlock check"
        }
    }


@app.post("/events", response_model=EventResponse)
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """
    Ingest a player event.
    
    This will:
    1. Store the event
    2. Update player statistics
    3. Check for new unlocks and generate classes if needed
    """
    try:
        db_event = ingest_event(
            db=db,
            user_id=event.user_id,
            event_name=event.event_name,
            metadata=event.metadata,
            timestamp=event.timestamp
        )
        # Map event_metadata to metadata for API response (SQLAlchemy reserves 'metadata' name)
        event_dict = {
            "id": db_event.id,
            "user_id": db_event.user_id,
            "event_name": db_event.event_name,
            "metadata": db_event.event_metadata,
            "timestamp": db_event.timestamp
        }
        return EventResponse(**event_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting event: {str(e)}")


@app.get("/player/{player_id}/features", response_model=PlayerFeatures)
async def get_player_features(player_id: str, db: Session = Depends(get_db)):
    """
    Get player features/statistics (aggregated event counts).
    Returns empty stats if player doesn't exist yet.
    """
    # Refresh the session to get latest data
    db.expire_all()
    
    # Query stats fresh from database
    stats = get_player_stats(db, player_id)
    
    # Convert sets to lists for JSON serialization
    serializable_stats = {}
    for event_name, data in stats.items():
        serializable_stats[event_name] = {
            "count": data["count"],
            "distinct_count": data["distinct_count"],
            "distinct_values": list(data["distinct_values"])
        }
    
    return PlayerFeatures(
        user_id=player_id,
        event_counts=serializable_stats
    )


@app.get("/player/{player_id}/classes", response_model=List[PlayerClassResponse])
async def get_player_classes(player_id: str, db: Session = Depends(get_db)):
    """
    Get all unlocked classes for a player.
    Returns empty list if player doesn't exist yet.
    """
    classes = db.query(PlayerClass).filter(PlayerClass.user_id == player_id).all()
    
    result = []
    for pc in classes:
        result.append(PlayerClassResponse(
            id=pc.id,
            user_id=pc.user_id,
            class_data=pc.class_data,
            unlock_condition_id=pc.unlock_condition_id,
            unlocked_at=pc.unlocked_at
        ))
    
    return result


@app.post("/check-unlocks/{player_id}", response_model=UnlockCheckResponse)
async def check_player_unlocks(player_id: str, db: Session = Depends(get_db)):
    """
    Manually trigger unlock evaluation for a player.
    
    This will check all unlock rules and generate classes for any newly met conditions.
    """
    try:
        newly_unlocked = check_unlocks(db, player_id)
        
        if newly_unlocked:
            message = f"Unlocked {len(newly_unlocked)} new class(es): {', '.join(newly_unlocked)}"
        else:
            message = "No new unlocks found"
        
        return UnlockCheckResponse(
            player_id=player_id,
            new_unlocks=newly_unlocked,
            message=message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking unlocks: {str(e)}")


@app.post("/generate-story", response_model=StoryGenerationResponse)
async def generate_story(
    request: StoryGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered story text.
    
    Uses Hugging Face Inference API (free tier) if HUGGINGFACE_API_TOKEN is set.
    Falls back to hardcoded text if no token is provided.
    """
    try:
        context = request.context
        player_class = request.player_class
        action = request.action
        player_id = request.player_id
        
        player_stats = None
        if player_id:
            stats = get_player_stats(db, player_id)
            # Convert to serializable format
            player_stats = {}
            for event_name, data in stats.items():
                player_stats[event_name] = {
                    "count": data["count"],
                    "distinct_count": data["distinct_count"]
                }
        
        story_text = await generate_story_text(
            context=context,
            player_class=player_class,
            action=action,
            player_stats=player_stats
        )
        
        return {"story_text": story_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating story: {str(e)}")

