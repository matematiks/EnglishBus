import os
import sys
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin

# Add parent dir to path if needed (standard for these setups)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.api.endpoints import router as api_router
from backend.api.admin_endpoints import router as new_admin_router
from backend.api.auth_endpoints import router as auth_router
from backend.api.practice_endpoints import router as practice_router
from backend.api.audio_endpoints import router as audio_router
from backend.api.teacher_approval_endpoints import router as teacher_approval_router
from backend.api.admin_message_endpoints import router as admin_message_router
from backend.api.system_endpoints import router as system_router
from backend.api.settings_endpoints import router as settings_router
# from backend.api.study_endpoints import router as study_router
from backend.database import engine

# Admin Imports
from backend.database import User, Course, Unit, Word
from sqladmin import Admin, ModelView, BaseView, expose
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import HTMLResponse
import sqlite3
from backend.api.security_utils import verify_password

# Setup App
app = FastAPI(title="EnglishBus Local")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key="super-secret-key", same_site="Lax", https_only=False)

# === STUDENT MESSAGES ENDPOINTS ===
def get_db():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "englishbus.db")
    conn = sqlite3.connect(db_path)
    try:
        yield conn
    finally:
        conn.close()

@app.get("/messages/student/{user_id}")
async def get_student_messages(user_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Get messages for a specific student"""
    try:
        messages = db.execute("""
            SELECT id, message_type, subject, message, sent_at, read_at
            FROM TeacherMessages
            WHERE student_id = ?
            ORDER BY sent_at DESC
            LIMIT 50
        """, (user_id,)).fetchall()
        
        return {"messages": [{
            "id": m[0],
            "message_type": m[1],
            "subject": m[2],
            "message": m[3],
            "sent_at": m[4],
            "read_at": m[5]
        } for m in messages]}
    except Exception as e:
        print(f"Get messages error: {e}")
        return {"messages": []}

@app.post("/messages/{message_id}/read")
async def mark_message_as_read(message_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Mark a message as read"""
    try:
        from datetime import datetime
        db.execute("""
            UPDATE TeacherMessages 
            SET read_at = ? 
            WHERE id = ? AND read_at IS NULL
        """, (datetime.now().isoformat(), message_id))
        db.commit()
        return {"success": True}
    except Exception as e:
        print(f"Mark as read error: {e}")
        return {"success": False}

# Mount Static
base_dir = os.path.dirname(os.path.dirname(__file__))
for folder in ["kurslar", "js", "css"]:
    p = os.path.join(base_dir, folder)
    if os.path.exists(p):
        app.mount(f"/assets" if folder == "kurslar" else f"/{folder}", StaticFiles(directory=p), name=folder)

# Routers
app.include_router(api_router)
app.include_router(teacher_approval_router, prefix="/admin/teachers", tags=["teacher-approval"])
app.include_router(admin_message_router, prefix="/admin/messages", tags=["admin-messages"])
app.include_router(new_admin_router, prefix="/api", tags=["api"])
app.include_router(new_admin_router, prefix="/admin/api", tags=["admin-api"])
app.include_router(system_router, prefix="/admin/api/system", tags=["system"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(practice_router, prefix="/practice", tags=["practice"])
app.include_router(audio_router, prefix="/audio", tags=["audio"])
app.include_router(teacher_approval_router, prefix="/admin/teachers", tags=["teacher-approval"])

# Teacher Panel
from backend.api.teacher_endpoints import teacher_router
app.include_router(teacher_router, prefix="/teacher", tags=["teacher"])


# Study
# app.include_router(study_router, prefix="/api/study", tags=["study"])

# Settings
app.include_router(settings_router, tags=["settings"])

# Root - Serve Index
@app.get("/")
def root():
    index_path = os.path.join(base_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Index not found</h1>")

# Admin Page - Serve admin.html
@app.get("/admin")
def admin_page():
    admin_path = os.path.join(base_dir, "admin.html")
    if os.path.exists(admin_path):
        with open(admin_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Admin panel not found</h1>", status_code=404)

# --- ADMIN SETUP (Copied from deferred_main) ---
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        
        try:
            db_path = os.path.join(base_dir, "englishbus.db")
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, password_hash, is_admin FROM Users WHERE username = ?", (username,))
                user_row = cursor.fetchone()
        except Exception as e:
            print(f"DB Auth Error: {e}")
            return False

        if not user_row:
            return False
            
        user_id, pwd_hash, is_admin = user_row
        
        # Ensure is_admin is treated as truthy (sqlite stores 0/1)
        if not is_admin:
            return False
            
        if not verify_password(password, pwd_hash):
            return False

        request.session.update({"token": "admin_logged_in", "user": username})
        return True
    
    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request) -> bool:
        return "token" in request.session

admin = Admin(app, engine, base_url="/admin/db", authentication_backend=AdminAuth(secret_key="local_secret"), templates_dir="backend/templates")



class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.is_admin]
admin.add_view(UserAdmin)

class CourseAdmin(ModelView, model=Course):
    column_list = [Course.id, Course.name, Course.total_words, Course.order_number]
admin.add_view(CourseAdmin)

class UnitAdmin(ModelView, model=Unit):
    column_list = [Unit.id, Unit.course_id, Unit.name, Unit.order_number, Unit.word_count]
admin.add_view(UnitAdmin)

class WordAdmin(ModelView, model=Word):
    column_list = [Word.id, Word.english, Word.turkish, Word.course_id, Word.unit_id]
admin.add_view(WordAdmin)
