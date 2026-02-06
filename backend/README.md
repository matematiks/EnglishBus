# FastAPI Backend - Quick Start Guide

## 🚀 Starting the Server

```bash
cd backend
python3 -m uvicorn main:app --reload
```

## 📋 Access Points

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **Health Check:** http://127.0.0.1:8000/health

## 🧪 Quick Test Sequence

### 1. Health Check
```http
GET /health
```

Expected: `{"status": "ok", "version": "1.0.0"}`

### 2. Start Session
```http
POST /session/start
Content-Type: application/json

{
  "user_id": 1,
  "course_id": 1
}
```

Expected: List of NEW words (step 1 words)

### 3. Complete Session
```http
POST /session/complete
Content-Type: application/json

{
  "user_id": 1,
  "course_id": 1,
  "completed_word_ids": [1, 2, 3]
}
```

Expected: `{"status": "success", "new_step": 2, "words_updated": 3}`

## 📁 Project Structure

```
backend/
├── main.py              # FastAPI app
├── session_manager.py   # Atomic session logic
├── api/
│   ├── __init__.py
│   ├── models.py        # Pydantic schemas
│   ├── endpoints.py     # Route handlers
│   └── dependencies.py  # DB connection
├── API_CONTRACT.md      # API specification
└── requirements.txt     # Dependencies
```

## ⚙️ Configuration

- **Database:** `../englishbus.db` (project root)
- **Port:** 8000
- **Host:** 127.0.0.1 (localhost)
- **CORS:** Enabled for all origins (development)

## 🔍 Troubleshooting

**ImportError for session_manager:**
- Ensure `session_manager.py` is in `backend/` directory

**Database not found:**
- Check path in `api/dependencies.py`
- Verify `englishbus.db` exists in project root

**Port already in use:**
- Change port: `uvicorn main:app --port 8001`
