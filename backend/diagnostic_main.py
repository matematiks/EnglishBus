import sys
import os
from a2wsgi import ASGIMiddleware

# --- FALLBACK WSGI APP ---
def fallback_wsgi(environ, start_response):
    """Raw WSGI app to display errors if FastAPI fails to load"""
    status = '200 OK'
    headers = [('Content-type', 'text/plain; charset=utf-8')]
    output = b"Startup failed (Fallback Mode). Check error logs."
    start_response(status, headers)
    return [output]

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    
    # Init App
    fastapi_app = FastAPI(title="Diagnostic Mode")

    @fastapi_app.get("/")
    def read_root():
        results = {
            "status": "Diagnostic App Running (via a2wsgi)",
            "db_check": "Not run yet"
        }
        
        # Test Database Connection
        try:
            from backend.database import engine
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            results["db_check"] = "✅ Connection Successful"
        except Exception as e:
            results["db_check"] = f"❌ DB Connection Failed: {str(e)}"
            
        return results

    # WRAP IN WSGI ADAPTER
    application = ASGIMiddleware(fastapi_app)

except Exception as e:
    print(f"Critical Error in diagnostic_main: {e}")
    # Create a crude WSGI app that prints the error
    def error_wsgi(environ, start_response):
        status = '200 OK'
        headers = [('Content-type', 'text/plain; charset=utf-8')]
        output = f"CRITICAL DIAGNOSTIC ERROR:\n{str(e)}".encode('utf-8')
        start_response(status, headers)
        return [output]
    application = error_wsgi
