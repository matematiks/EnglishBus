"""
EnglishBus - Main FastAPI Application
Spaced Repetition Learning System with Fibonacci Scheduling
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api.endpoints import router
import os

# Create FastAPI app
app = FastAPI(
    title="EnglishBus API",
    description="Spaced Repetition Learning System",
    version="1.0.0"
)

# CORS middleware (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CORS headers to static file responses
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    # Add CORS headers for static assets (audio, images)
    if request.url.path.startswith("/assets"):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Include API routes
app.include_router(router)

# Serve static assets (images, audio)
KURSLAR_PATH = os.path.join(os.path.dirname(__file__), "..", "kurslar")
if os.path.exists(KURSLAR_PATH):
    app.mount("/assets", StaticFiles(directory=KURSLAR_PATH), name="assets")
    print(f"📁 Static files mounted: /assets → {KURSLAR_PATH}")
else:
    print(f"⚠️ Warning: kurslar directory not found at {KURSLAR_PATH}")

# Serve JS and CSS
JS_PATH = os.path.join(os.path.dirname(__file__), "..", "js")
if os.path.exists(JS_PATH):
    app.mount("/js", StaticFiles(directory=JS_PATH), name="js")

CSS_PATH = os.path.join(os.path.dirname(__file__), "..", "css")
if os.path.exists(CSS_PATH):
    app.mount("/css", StaticFiles(directory=CSS_PATH), name="css")

# Include API routes
app.include_router(router, prefix="", tags=["sessions"])

# Admin Panel
from backend.api.admin_endpoints import router as admin_router
app.include_router(admin_router, prefix="/admin", tags=["admin"])

# Auth System
from backend.api.auth_endpoints import router as auth_router
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# Practice System (Sentence Generator)
from backend.api.practice_endpoints import router as practice_router
app.include_router(practice_router, prefix="/practice", tags=["practice"])



@app.get("/admin_panel")
def admin_panel():
    """Serve Admin HTML"""
    admin_path = os.path.join(os.path.dirname(__file__), "..", "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return {"error": "Admin Panel not found"}

# Root endpoint - serve frontend
from fastapi.responses import FileResponse

@app.get("/")
def root():
    """Serve frontend HTML"""
    index_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "EnglishBus API",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/modern")
def modern_ui():
    """Serve modern HTML interface"""
    modern_path = os.path.join(os.path.dirname(__file__), "..", "index_modern.html")
    if os.path.exists(modern_path):
        return FileResponse(modern_path)
    return {"error": "index_modern.html not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)

# ==========================================
# ADMIN PANEL
# ==========================================
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from backend.database import engine, Course, Unit, Word, User
from backend.api.security_utils import verify_password, create_access_token, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
import sqlite3

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # Verify against DB
        # We need a fresh connection or engine logic here
        # Since we have 'engine', let's use it roughly or just connect
        # For simplicity in this sync/async mix:
        
        # NOTE: In production optimized way is better, but this works for SQLite
        with sqlite3.connect(os.path.join(os.path.dirname(os.path.dirname(__file__)), "englishbus.db")) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_hash, is_admin FROM Users WHERE username = ?", (username,))
            user = cursor.fetchone()
            
        if not user:
            return False
            
        user_id, pwd_hash, is_admin = user
        
        if not is_admin:
            return False
            
        if not verify_password(password, pwd_hash):
            return False

        # Session
        request.session.update({"token": "admin_logged_in", "admin_user": username})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True

authentication_backend = AdminAuth(secret_key=SECRET_KEY)

class CourseAdmin(ModelView, model=Course):
    column_list = [Course.id, Course.name, Course.total_words, Course.order_number]
    icon = "fa-solid fa-book"
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

class UnitAdmin(ModelView, model=Unit):
    column_list = [Unit.id, Unit.name, Unit.course_id, Unit.word_count]
    column_sortable_list = [Unit.order_number, Unit.course_id]
    column_searchable_list = [Unit.name]
    icon = "fa-solid fa-layer-group"

class WordAdmin(ModelView, model=Word):
    column_list = [Word.id, Word.english, Word.turkish, Word.unit_id]
    column_searchable_list = [Word.english, Word.turkish]
    list_per_page = 50
    icon = "fa-solid fa-language"

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.active_course_id, User.is_admin]
    column_searchable_list = [User.username]
    icon = "fa-solid fa-user"
    can_create = True
    can_edit = True
    can_delete = True

# Initialize Admin
admin = Admin(app, engine, authentication_backend=authentication_backend)
admin.add_view(CourseAdmin)
admin.add_view(UnitAdmin)
admin.add_view(WordAdmin)
admin.add_view(UserAdmin)
