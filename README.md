# Social Media Backend (FastAPI)

A full-featured social media backend built with **FastAPI** and **PostgreSQL**, including:

- Users and authentication (JWT)
- Posts with comments and likes
- Follow system, profiles, and feed
- 1‑to‑1 encrypted messaging
- Notifications (follows, likes, comments, messages)
- Basic rate limiting
- Full pytest integration tests

## Requirements

- Python 3.11+
- PostgreSQL running locally (or adjust `DATABASE_URL`)

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Configuration (.env)

Create a `.env` file in the project root. Example:

```env
# Database
DATABASE_URL=postgresql://postgres:yourpassword@localhost/fastapi

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Chat encryption key
# Generate with:
#   from cryptography.fernet import Fernet
#   print(Fernet.generate_key().decode())
CHAT_ENCRYPTION_KEY=your-fernet-key
```

## Running the app

From the project root:

```bash
uvicorn app.main:app --reload
```

Open the interactive docs:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Use the **Authorize** button in Swagger to paste your JWT (from `POST /login`) as a Bearer token.

## Testing

Run the pytest suite:

```bash
python -m pytest -vv
```

Tests cover:

- Authentication
- User creation
- Posts, comments, likes, and feed
- Follow + profiles
- Messaging (conversations, messages, unread count, mark read)
- Notifications (creation, list, mark read / mark all)

## Project Structure

```text
app/
  main.py          # FastAPI app, router includes, OpenAPI tags
  models.py        # SQLAlchemy models (re-export from model.py)
  schemas.py       # Pydantic schemas (re-export from schema.py)
  core/
    db.py          # DB engine, SessionLocal, get_db
    security.py    # JWT + password helpers, get_current_user
    rate_limiter.py
    crypto_util.py # Fernet encryption for messages
  api/
    auth.py        # /login, /logout
    users.py       # /create_user
    posts.py       # Posts, comments, likes
    follow_profile.py
    messaging.py
    notifications.py

(legacy root files like `main.py`, `model.py`, etc. are still present but the primary entrypoint is `app/main.py`.)
