"""Tests for API endpoints"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app


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


@pytest.fixture
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data


def test_create_event(client):
    """Test POST /events endpoint"""
    event_data = {
        "user_id": "test_player_api",
        "event_name": "read_book",
        "metadata": {"book_id": "book_1", "length_pages": 462}
    }
    
    response = client.post("/events", json=event_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["user_id"] == "test_player_api"
    assert data["event_name"] == "read_book"
    assert "id" in data
    assert "timestamp" in data


def test_get_player_features(client):
    """Test GET /player/{id}/features endpoint"""
    user_id = "test_player_features"
    
    # Create some events first
    for i in range(10):
        client.post("/events", json={
            "user_id": user_id,
            "event_name": "read_book",
            "metadata": {"book_id": f"book_{i}"}
        })
    
    response = client.get(f"/player/{user_id}/features")
    assert response.status_code == 200
    
    data = response.json()
    assert data["user_id"] == user_id
    assert "event_counts" in data
    assert "read_book" in data["event_counts"]
    assert data["event_counts"]["read_book"]["count"] == 10


def test_get_player_classes(client):
    """Test GET /player/{id}/classes endpoint"""
    user_id = "test_player_classes"
    
    # First, ensure player exists
    client.post("/events", json={
        "user_id": user_id,
        "event_name": "read_book",
        "metadata": {"book_id": "book_1"}
    })
    
    response = client.get(f"/player/{user_id}/classes")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_check_unlocks_endpoint(client):
    """Test POST /check-unlocks/{id} endpoint"""
    user_id = "test_player_unlocks"
    
    # Create some events
    for i in range(5):
        client.post("/events", json={
            "user_id": user_id,
            "event_name": "read_book",
            "metadata": {"book_id": f"book_{i}"}
        })
    
    response = client.post(f"/check-unlocks/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["player_id"] == user_id
    assert "new_unlocks" in data
    assert "message" in data


def test_event_triggers_class_generation(client):
    """Test that ingesting enough events triggers class generation"""
    user_id = "test_player_auto_unlock"
    
    # Ingest exactly 10000 book reading events (should trigger unlock)
    for i in range(10000):
        response = client.post("/events", json={
            "user_id": user_id,
            "event_name": "read_book",
            "metadata": {"book_id": f"book_{i}"}
        })
        assert response.status_code == 200
    
    # Check that class was unlocked
    response = client.get(f"/player/{user_id}/classes")
    assert response.status_code == 200
    
    classes = response.json()
    assert len(classes) > 0
    
    # Verify it's the bookworm unlock
    bookworm_found = any(
        pc["unlock_condition_id"] == "unlock_read_10000" 
        for pc in classes
    )
    assert bookworm_found

