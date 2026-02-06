
import sys
import os
import traceback

# ==========================================
# DEFERRED LOADING (LAZY LOAD) - THE ULTIMATE FIX
# ==========================================
# This script does NOT import FastAPI at the top.
# It imports it only when a user visits the site.
# This prevents "Startup Timeouts" 100%.
# ==========================================

# Global variable to cache the app after first load
_cached_app = None

def application(environ, start_response):
    global _cached_app
    
    # If app is already loaded, run it!
    if _cached_app:
        return _cached_app(environ, start_response)
        
    # First time loading (Request Time)
    try:
        # ----------------------------------------------------
        # 1. ATTEMPT REAL IMPORTS HERE (Inside the request)
        # ----------------------------------------------------
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import HTMLResponse
        from fastapi.staticfiles import StaticFiles
        from a2wsgi import ASGIMiddleware
        
        # 2. LOCAL IMPORTS (The likely failure points)
        # Using local import to avoid top-level crashes
        from backend.api.endpoints import router as api_router
        from backend.api.admin_endpoints import router as admin_router
        from backend.api.auth_endpoints import router as auth_router
        from backend.api.practice_endpoints import router as practice_router
        from backend.database import engine

        # 3. SETUP APP
        fastapi_app = FastAPI(title="EnglishBus (Lazy Loaded)")
        
        fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        fastapi_app.include_router(api_router)
        fastapi_app.include_router(admin_router, prefix="/admin", tags=["admin"])
        fastapi_app.include_router(auth_router, prefix="/auth", tags=["auth"])
        fastapi_app.include_router(practice_router, prefix="/practice", tags=["practice"])

        # Static Files
        base_dir = os.path.dirname(os.path.dirname(__file__))
        for folder in ["kurslar", "js", "css"]:
            p = os.path.join(base_dir, folder)
            if os.path.exists(p):
                fastapi_app.mount(f"/assets" if folder == "kurslar" else f"/{folder}", StaticFiles(directory=p), name=folder)

        # Admin Panel
        try:
            from sqladmin import Admin, ModelView, BaseView, expose
            from backend.database import User, Course, Unit, Word
            from sqladmin.authentication import AuthenticationBackend
            from starlette.requests import Request
            from starlette.responses import HTMLResponse
            import sqlite3
            from backend.api.security_utils import verify_password
            
            class AdminAuth(AuthenticationBackend):
                async def login(self, request: Request) -> bool:
                    form = await request.form()
                    username = form.get("username")
                    password = form.get("password")
                    
                    try:
                        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "englishbus.db")
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

            admin = Admin(fastapi_app, engine, authentication_backend=AdminAuth(secret_key="secure_lazy_mode"))
            
            # Custom View for Import Dashboard
            class ImportView(BaseView):
                name = "Yönetim Paneli (Özel)"
                icon = "fa-chart-pie"

                @expose("/dashboard", methods=["GET"])
                async def dashboard_page(self, request):
                    # Serve admin.html
                    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "admin.html")
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            return HTMLResponse(f.read())
                    return HTMLResponse("admin.html not found", status_code=404)
            
            admin.add_view(ImportView)

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
        except Exception as e:
            print(f"Admin Load Failed: {e}")

        # Root Endpoint
        from fastapi.responses import HTMLResponse
        # Root Endpoint - Serve Real App
        from fastapi.responses import HTMLResponse
        @fastapi_app.get("/")
        def root():
            # Try to load index.html from parent dir
            try:
                index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html")
                if os.path.exists(index_path):
                    with open(index_path, "r", encoding="utf-8") as f:
                        return HTMLResponse(f.read())
            except:
                pass
            return HTMLResponse("<h1>EnglishBus API is Running</h1><p>Frontend (index.html) not found.</p>")

        # 4. WRAP IN A2WSGI
        _cached_app = ASGIMiddleware(fastapi_app)
        
        # Run the newly created app immediately for this request
        return _cached_app(environ, start_response)

    except Exception:
        # 5. CATCH ANY ERROR DURING LOADING
        status = '200 OK'
        headers = [('Content-type', 'text/html; charset=utf-8')]
        error_msg = traceback.format_exc()
        
        html = f"""
        <html>
        <body style="background: #fff0f0; padding: 20px; font-family: monospace;">
            <h1 style="color: red;">Startup Failed (Request Time)</h1>
            <p>We avoided the timeout, but the code crashed while loading.</p>
            <hr>
            <pre style="background: white; padding: 15px; border: 1px solid #ccc; overflow: auto;">{error_msg}</pre>
        </body>
        </html>
        """.encode('utf-8')
        
        start_response(status, headers)
        return [html]
