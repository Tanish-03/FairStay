# FairStay

A tenant complaint management system with AI-powered classification and summarization. FairStay enables tenants to submit complaints, which are automatically categorized, severity-scored, and summarized using a local LLM (Ollama).

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Module Documentation](#module-documentation)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Setup &amp; Installation](#setup--installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Development](#development)

## Overview

FairStay is a full-stack application designed to help tenants submit and manage complaints. The system uses AI (via Ollama/LangChain) to automatically:

- **Classify** complaints into predefined categories
- **Assess severity** on a scale of 1-5
- **Generate summaries** for quick review

The application consists of:

- **Backend API**: FastAPI-based REST API with PostgreSQL database
- **Web UI**: Streamlit-based interface for complaint submission and browsing
- **AI Agent**: LangChain integration with Ollama for complaint processing

## Architecture

```
┌─────────────┐
│  Streamlit  │  ← User Interface
│     UI      │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────┐
│  FastAPI    │  ← REST API Server
│   Backend   │
└──────┬──────┘
       │
       ├───► PostgreSQL Database
       │
       └───► Ollama LLM (AI Agent)
```

## Technology Stack

### Backend

- **FastAPI** (0.116.1+): Modern, fast web framework for building APIs
- **SQLAlchemy** (2.0.42+): ORM for database operations
- **PostgreSQL**: Relational database with psycopg2-binary driver
- **Pydantic** (2.11.7+): Data validation and serialization
- **Uvicorn**: ASGI server for running FastAPI

### AI/ML

- **LangChain Community** (0.3.27+): LLM framework and abstractions
- **Ollama**: Local LLM runtime (requires separate installation)

### Frontend

- **Streamlit** (1.48.0+): Rapid web app development framework

### Utilities

- **python-dotenv**: Environment variable management

## Project Structure

```
FairStay/
├── backend/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application and routes
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic schemas for validation
│   ├── database.py          # Database connection and session management
│   ├── crud.py              # Database CRUD operations
│   ├── ai_agent.py          # AI classification and summarization logic
│   └── ui/
│       └── app.py           # Streamlit web interface
├── main.py                  # Root entry point (placeholder)
├── pyproject.toml           # Project dependencies and metadata
├── requirements.txt         # Python dependencies (empty, use pyproject.toml)
├── uv.lock                  # Dependency lock file (uv package manager)
└── README.md               # This file
```

## Module Documentation

### `backend/main.py`

**Purpose**: FastAPI application entry point and route definitions.

**Key Components**:

- **FastAPI App**: Initializes the FastAPI application with title "FairSaty API" (v0.1)
- **Database Initialization**: Creates all database tables on startup via `Base.metadata.create_all()`
- **Dependency Injection**: `get_db()` function provides database session management
- **Routes**:
  - `GET /health`: Health check endpoint
  - `GET /complaints/{complaint_id}`: Retrieve a specific complaint by ID
  - `GET /complaints`: List recent complaints with optional limit parameter
  - `POST /submit_complaint`: Submit a new complaint (function defined but route decorator missing - see Development notes)

**Dependencies**:

- FastAPI, SQLAlchemy ORM, Pydantic schemas, CRUD operations, AI agent

---

### `backend/models.py`

**Purpose**: SQLAlchemy ORM models defining the database schema.

**Models**:

#### `Complaint`

Represents a tenant complaint record in the database.

**Fields**:

- `id` (Integer, Primary Key): Auto-incrementing unique identifier
- `user_id` (String, Indexed, Nullable): Optional identifier for the submitting user
- `complaint_text` (Text, Required): The full text of the complaint
- `category` (String, Nullable): AI-classified category (harassment, discrimination, access, noise, property_damage, other)
- `severity_score` (Integer, Nullable): AI-assessed severity (1-5 scale)
- `generated_summary` (Text, Nullable): AI-generated summary (≤60 words)
- `submitted_at` (TIMESTAMP, Required): Auto-populated timestamp of submission

**Database Table**: `complaints`

---

### `backend/schemas.py`

**Purpose**: Pydantic models for request/response validation and serialization.

**Schemas**:

#### `ComplaintCreate`

Input schema for creating a new complaint.

**Fields**:

- `user_id` (Optional[str]): User identifier
- `complaint_text` (str): Complaint description (required)
- `category` (Optional[str]): Pre-classified category (usually auto-generated)
- `severity_score` (Optional[int]): Pre-assessed severity (usually auto-generated)

#### `ComplaintUpdate`

Schema for updating existing complaints (all fields optional).

#### `ComplaintOut`

Output schema for API responses, includes all fields plus:

- `id` (int): Database ID
- `submitted_at` (datetime): Submission timestamp

**Configuration**: Uses Pydantic v2 `ConfigDict(from_attributes=True)` for ORM compatibility.

---

### `backend/database.py`

**Purpose**: Database connection configuration and session management.

**Components**:

- **Database URL**: Constructs PostgreSQL connection URL using SQLAlchemy's `URL.create()`
  - Default: `postgresql+psycopg2://postgres:Tanish@123@localhost:5432/FairStayServer`
  - **Note**: Password is hardcoded - should be moved to environment variables
- **Engine**: SQLAlchemy engine with connection pooling and pre-ping enabled
- **SessionLocal**: Session factory for database operations
- **Base**: Declarative base class for ORM models

**Security Note**: Database credentials should be externalized to environment variables.

---

### `backend/crud.py`

**Purpose**: Database CRUD (Create, Read, Update, Delete) operations.

**Functions**:

#### `create_complaint(db: Session, complaint_in: ComplaintCreate, ai_payload: dict) -> Complaint`

Creates a new complaint record in the database.

**Parameters**:

- `db`: SQLAlchemy session
- `complaint_in`: Pydantic schema with user input
- `ai_payload`: Dictionary containing AI-generated fields (`category`, `severity`, `summary`)

**Returns**: Created `Complaint` model instance

**Process**:

1. Creates new `Complaint` object from input schema
2. Populates AI-generated fields from `ai_payload`
3. Adds to session, commits, and refreshes
4. Returns the persisted object

#### `get_complaint(db: Session, complaint_id: int) -> Complaint | None`

Retrieves a single complaint by ID.

**Returns**: `Complaint` object or `None` if not found

#### `list_recent(db: Session, limit: int = 20) -> List[Complaint]`

Retrieves the most recent complaints, ordered by ID descending.

**Parameters**:

- `limit`: Maximum number of records to return (default: 20)

**Returns**: List of `Complaint` objects

---

### `backend/ai_agent.py`

**Purpose**: AI-powered complaint classification and summarization using LangChain and Ollama.

**Key Components**:

#### Configuration

- **Model**: Configurable via `OLLAMA_MODEL` environment variable (default: "llama3")
- **Timeout**: 8-second hard timeout to prevent API hangs
- **Allowed Categories**: `{harassment, discrimination, access, noise, property_damage, other}`

#### Prompt Template

Uses LangChain's `PromptTemplate` to instruct the LLM to:

- Classify complaints into predefined categories
- Assign severity scores (1-5)
- Generate neutral, factual summaries (≤60 words)
- Return structured JSON output

#### Functions

##### `classify_and_summarize(complaint: str) -> Dict`

**Main entry point** for the AI processing pipeline.

**Process**:

1. Formats the prompt with complaint text
2. Executes LLM call with 8-second timeout using `ThreadPoolExecutor`
3. Extracts JSON from LLM response using regex
4. Validates and normalizes:
   - Category: Ensures it's in the allowed set, defaults to "other"
   - Severity: Clamps to 1-5 range, defaults to 3
   - Summary: Truncates to 60 words max, 500 characters max
5. Returns fallback response if any step fails

**Returns**: Dictionary with keys:

- `category` (str): Normalized category
- `severity` (int): Severity score (1-5)
- `summary` (str): Generated summary

##### Helper Functions

- `_fallback(complaint: str)`: Returns safe default values if AI processing fails
- `_normalize_category(cat: str, default_text: str)`: Validates category against allowed set
- `_extract_json(raw: str)`: Extracts JSON from LLM response using regex, handles common formatting issues
- `_llm_call(prompt: str)`: Invokes Ollama LLM with zero temperature for deterministic output

**Error Handling**: All exceptions are caught and fallback values are returned to ensure API reliability.

---

### `backend/ui/app.py`

**Purpose**: Streamlit-based web interface for complaint submission and browsing.

**Features**:

#### Settings Sidebar

- **API URL Configuration**: Configurable backend API endpoint (default: `http://127.0.0.1:8000`)
- **Health Check**: Real-time API connectivity status indicator
- **Usage Tips**: Instructions for starting the API server

#### Complaint Submission Form

- **User ID Input**: Optional identifier field
- **Complaint Text Area**: Multi-line input for complaint description
- **Character Counter**: Real-time character count display
- **Submission**: Validates input and posts to `/submit_complaint` endpoint
- **AI Analysis Display**: Shows category, severity score, and generated summary after submission

#### Complaint Browsing

- **Fetch by ID**: Retrieve specific complaint by database ID
- **Load Recent**: Display recent complaints with configurable limit (5-50)
- **Severity Filter**: Interactive slider to filter by minimum severity (1-5)
- **Data Table**: Formatted dataframe with column configuration for readability

**Dependencies**: `streamlit`, `requests`

**Usage**: Run with `streamlit run backend/ui/app.py`

---

## API Endpoints

### `GET /health`

Health check endpoint.

**Response**:

```json
{
  "status": "ok"
}
```

---

### `GET /complaints/{complaint_id}`

Retrieve a specific complaint by ID.

**Parameters**:

- `complaint_id` (path, int): Database ID of the complaint

**Response**: `ComplaintOut` schema

```json
{
  "id": 1,
  "user_id": "anon-123",
  "complaint_text": "Full complaint text...",
  "category": "noise",
  "severity_score": 4,
  "generated_summary": "AI-generated summary...",
  "submitted_at": "2024-01-15T10:30:00Z"
}
```

**Errors**:

- `404`: Complaint not found

---

### `GET /complaints`

List recent complaints.

**Query Parameters**:

- `limit` (int, optional): Maximum number of records (default: 20)

**Response**: Array of `ComplaintOut` objects

---

### `POST /submit_complaint`

Submit a new complaint for processing.

**Request Body**: `ComplaintCreate` schema

```json
{
  "user_id": "anon-123",
  "complaint_text": "Description of the issue..."
}
```

**Response**: `ComplaintOut` schema with AI-generated fields populated

**Errors**:

- `400`: Missing or empty `complaint_text`

**Note**: This endpoint function exists but may need the `@app.post` decorator added (see Development section).

---

## Database Schema

### Table: `complaints`

| Column                | Type      | Constraints             | Description                         |
| --------------------- | --------- | ----------------------- | ----------------------------------- |
| `id`                | INTEGER   | PRIMARY KEY, INDEX      | Auto-incrementing unique identifier |
| `user_id`           | VARCHAR   | INDEX, NULLABLE         | Optional user identifier            |
| `complaint_text`    | TEXT      | NOT NULL                | Full complaint description          |
| `category`          | VARCHAR   | NULLABLE                | AI-classified category              |
| `severity_score`    | INTEGER   | NULLABLE                | AI-assessed severity (1-5)          |
| `generated_summary` | TEXT      | NULLABLE                | AI-generated summary                |
| `submitted_at`      | TIMESTAMP | NOT NULL, DEFAULT NOW() | Submission timestamp                |

---

## Setup & Installation

### Prerequisites

- Python 3.10 or higher
- PostgreSQL database server
- Ollama installed and running locally
- `uv` package manager (recommended) or `pip`

### Step 1: Install Dependencies

Using `uv` (recommended):

```bash
uv sync
```

Using `pip`:

```bash
pip install -r requirements.txt
# Or install from pyproject.toml:
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic python-dotenv langchain-community streamlit requests
```

### Step 2: Set Up PostgreSQL Database

1. Create a PostgreSQL database:

```sql
CREATE DATABASE "FairStayServer";
```

2. Update database credentials in `backend/database.py` or use environment variables (recommended).

### Step 3: Install and Configure Ollama

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Pull the required model:

```bash
ollama pull llama3
```

3. Verify Ollama is running:

```bash
ollama list
```

### Step 4: Environment Variables

Create a `.env` file in the project root:

```env
OLLAMA_MODEL=llama3
# Database credentials (if externalized)
# DB_USER=postgres
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=FairStayServer
```

---

## Configuration

### Database Configuration

Currently hardcoded in `backend/database.py`. For production, externalize to environment variables:

```python
import os
from dotenv import load_dotenv

load_dotenv()

url = URL.create(
    "postgresql+psycopg2",
    username=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 5432)),
    database=os.getenv("DB_NAME", "FairStayServer"),
)
```

### AI Model Configuration

Set `OLLAMA_MODEL` in `.env` to use a different model (e.g., `llama3.2`, `mistral`, etc.).

---

## Running the Application

### Start the Backend API

```bash
# From project root
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://127.0.0.1:8000`

API documentation (Swagger UI): `http://127.0.0.1:8000/docs`

### Start the Streamlit UI

```bash
# From project root
streamlit run backend/ui/app.py
```

The UI will open in your browser at `http://localhost:8501`

### Verify Setup

1. Check API health: `curl http://127.0.0.1:8000/health`
2. Verify Ollama is accessible and the model is available
3. Test database connection by submitting a complaint through the UI

---

## Development

### Known Issues / TODO

1. **Missing Route Decorator**: The `submit_complaint` function in `backend/main.py` (line 35) is defined but not decorated with `@app.post("/submit_complaint")`. This needs to be added:

   ```python
   @app.post("/submit_complaint", response_model=schemas.ComplaintOut)
   def submit_complaint(payload: schemas.ComplaintCreate, db: Session = Depends(get_db)):
       # ... existing code ...
   ```
2. **Duplicate Route**: There are two `GET /complaints` route definitions (lines 31 and 43). The second one should be kept as it includes the `limit` parameter.
3. **Security**: Database credentials are hardcoded in `backend/database.py`. Should be moved to environment variables.
4. **Error Handling**: Consider adding more comprehensive error handling and logging throughout the application.

### Development Workflow

1. Make code changes
2. The FastAPI server will auto-reload (if started with `--reload`)
3. Streamlit UI requires manual refresh or restart
4. Test endpoints using the Swagger UI at `/docs`

### Testing

Consider adding:

- Unit tests for CRUD operations
- Integration tests for API endpoints
- Mock tests for AI agent functionality
- End-to-end tests for the UI

---

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
