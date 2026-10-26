# TaskFlow

A simple task management application with a FastAPI backend and vanilla JS frontend.

## Structure

```
taskflow/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app, routes, CORS
│   │   ├── models.py        # SQLAlchemy Task model
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── crud.py          # Database CRUD operations
│   │   └── database.py      # DB engine, session, init
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py      # Test fixtures (in-memory DB)
│   │   └── test_api.py      # API endpoint tests
│   └── requirements.txt
└── frontend/
    ├── index.html           # Main page
    ├── app.js               # Frontend logic (vanilla JS)
    └── styles.css           # Styling
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/tasks` | List tasks (filter: `completed`, `priority`) |
| POST | `/api/tasks` | Create a task |
| GET | `/api/tasks/search?q=` | Search tasks by title/description |
| GET | `/api/tasks/{id}` | Get a single task |
| PATCH | `/api/tasks/{id}` | Update a task |
| DELETE | `/api/tasks/{id}` | Delete a task |

## Running

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Tests

```bash
cd backend
pytest -v
```

### Frontend

The frontend is served by the backend at `http://localhost:8000/`.

## Task Fields

- `title` (string, required) — Task title
- `description` (string) — Optional description
- `completed` (boolean) — Completion status
- `priority` (string) — `low`, `medium`, or `high`
- `due_date` (string) — ISO date string
- `created_at` (datetime) — Auto-set on creation
- `updated_at` (datetime) — Auto-updated on modification
