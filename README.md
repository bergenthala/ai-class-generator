# AI Superintelligence Game Class Generator

An AI-driven system for dynamically generating **player classes**, **skills**, **rarities**, and **unlock conditions** based on player behavior. This system uses a rule-based engine to detect player achievements and generates unique, data-driven classes with stats, skills, and rarity.

## 🎯 Overview

The system tracks player events (e.g., reading books, killing monsters, crafting items) and automatically generates custom classes when players meet certain thresholds. Each generated class includes:

- **Base stats** (HP, MP, STR, INT, DEX)
- **Growth per rank** (stat increases per level)
- **Skills** (active and passive abilities)
- **Rarity** (Common through Forbidden)
- **Dynamic naming** (with random adjectives)
- **AI-powered story generation** (optional, using Hugging Face free API)

## 🏗️ Architecture

The system consists of 4 main modules:

1. **Event System** - Ingests and stores player events, aggregates statistics
2. **Unlock Engine** - Evaluates unlock rules against player statistics
3. **Class Generator** - Generates classes based on templates and rarity system
4. **API Layer** - RESTful endpoints for event ingestion and data retrieval
5. **Story Service** - AI-powered story generation (optional)

## 📋 Requirements

- Python 3.10+
- SQLite (included with Python)
- Dependencies listed in `requirements.txt`
- (Optional) Hugging Face API token for AI story generation

## 🚀 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database (Optional)

By default, the system uses SQLite at `./game_classes.db`. To use a different database, set the `DATABASE_URL` environment variable:

```bash
# SQLite (default)
export DATABASE_URL=sqlite:///./game_classes.db

# PostgreSQL (example)
export DATABASE_URL=postgresql://user:password@localhost/dbname
```

### 3. (Optional) Enable AI Story Generation

To enable AI-powered story generation, get a free Hugging Face API token:

1. Sign up at [huggingface.co](https://huggingface.co) (free, no credit card)
2. Go to your profile → Access Tokens → Create new token
3. Set the environment variable:

```bash
# Windows PowerShell
$env:HUGGINGFACE_API_TOKEN="your_token_here"

# Linux/Mac
export HUGGINGFACE_API_TOKEN="your_token_here"
```

**Note:** If no token is provided, the system will use hardcoded story text (still fully functional).

### 4. Run the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 5. Play the Interactive Game

Once the server is running, visit:
- **Interactive Game**: `http://localhost:8000/` or `http://localhost:8000/game`
- **API Documentation**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

The interactive game provides a story-based interface where you can:
- Choose your starting class (Warrior, Priest, Mage, Thief, or Wanderer)
- Perform actions (read books, fight monsters, craft items, etc.)
- Watch your progress and see new classes unlock automatically
- View detailed stats and unlocked classes in real-time
- Experience AI-generated story text (if API token is configured)

## 📡 API Endpoints

### `POST /events`

Ingest a player event. This will:
1. Store the event
2. Update player statistics
3. Check for new unlocks and generate classes if needed

**Request:**
```json
{
  "user_id": "player_123",
  "event_name": "read_book",
  "metadata": {
    "book_id": "b_778",
    "length_pages": 462
  },
  "timestamp": "2025-11-10T21:00:00Z"
}
```

### `POST /generate-story`

Generate AI-powered story text (optional, requires Hugging Face token).

**Request:**
```json
{
  "context": "Starting a new adventure",
  "player_class": "warrior",
  "action": "read_book",
  "player_id": "player_123"
}
```

**Response:**
```json
{
  "story_text": "You open the ancient tome, its pages glowing with arcane knowledge..."
}
```

### `GET /player/{id}/features`

Get player statistics (aggregated event counts).

### `GET /player/{id}/classes`

Get all unlocked classes for a player.

### `POST /check-unlocks/{id}`

Manually trigger unlock evaluation for a player.

## 🎮 Example Usage

### Using cURL

```bash
# Ingest a book reading event
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "player_1",
    "event_name": "read_book",
    "metadata": {"book_id": "b1", "length_pages": 462}
  }'

# Generate AI story
curl -X POST http://localhost:8000/generate-story \
  -H "Content-Type: application/json" \
  -d '{
    "context": "The player just read a book",
    "player_class": "mage",
    "action": "read_book"
  }'
```

## 🔓 Unlock Rules

The system includes 3 hardcoded unlock rules:

1. **Read 10,000 books** → Epic "The Wise One" class
   - High INT, MP-focused
   - Knowledge and magic skills

2. **Kill 5,000 monsters** → Rare "The Slayer" class
   - High STR, HP-focused
   - Combat and damage skills

3. **Craft 100 unique items** → Uncommon "The Tinkerer" class
   - Balanced DEX/INT
   - Crafting and engineering skills

Rules are defined in `app/rules.py` and can be easily extended.

## 💎 Rarity System

Classes are generated with one of 10 rarity tiers:

| Rarity | Weight | Stat Multiplier |
|--------|--------|----------------|
| Common | 54.899% | 1.0x |
| Uncommon | 25.0% | 1.1x |
| Magic | 8.0% | 1.2x |
| Rare | 4.0% | 1.35x |
| Epic | 3.0% | 1.5x |
| Unique | 2.5% | 1.7x |
| Legendary | 2.0% | 2.0x |
| Mythic | 0.5% | 2.5x |
| God | 0.1% | 3.0x |
| Forbidden | 0.001% | 4.0x |

Higher rarity classes have better base stats and more skills.

## 🧪 Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app tests/
```

### Test Coverage

- **test_unlocks.py**: Tests unlock rule evaluation and class generation triggers
- **test_generator.py**: Tests class generation logic and rarity system
- **test_api.py**: Tests API endpoints and integration

## 📁 Project Structure

```
ai-class-generator/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entrypoint
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # Database setup
│   ├── rules.py             # Unlock rules
│   ├── generator.py         # Class generation logic
│   ├── unlock_engine.py     # Unlock evaluation
│   ├── event_service.py     # Event ingestion
│   ├── story_service.py    # AI story generation
│   ├── utils.py             # Utilities (rarity, naming)
│   └── static/              # Web interface
│       ├── index.html
│       ├── style.css
│       └── script.js
│
├── tests/
│   ├── __init__.py
│   ├── test_unlocks.py
│   ├── test_generator.py
│   └── test_api.py
│
├── requirements.txt
├── README.md
└── game_classes.db          # SQLite database (created on first run)
```

## 🔮 Future Roadmap

### Phase 2: Enhanced LLM Integration
- Better prompt engineering for story generation
- Support for multiple LLM providers (OpenAI, Anthropic, etc.)
- Story memory/context tracking

### Phase 3: Machine Learning
- `/train` endpoint for fine-tuning models
- Player behavior prediction
- Personalized class recommendations

### Phase 4: Scalability
- Redis integration for caching
- PostgreSQL support for production
- Task queue (Celery) for async processing
- Configuration file for tuning rarity weights and thresholds

## 🛠️ Extension Points

The codebase is designed with extension in mind:

1. **Add new unlock rules**: Edit `app/rules.py`
2. **Add class templates**: Edit `app/generator.py` → `CLASS_TEMPLATES`
3. **Add skill themes**: Edit `app/generator.py` → `SKILL_TEMPLATES`
4. **Custom rarity weights**: Edit `app/utils.py` → `RARITY_WEIGHTS`
5. **AI story models**: Edit `app/story_service.py` → `DEFAULT_MODEL`
6. **Database migration**: Use Alembic (not included, but compatible)

## 📝 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

This is a standalone project, but suggestions and improvements are welcome!

---

**Happy Class Generating! 🎮✨**
