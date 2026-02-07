import sys
import os
import traceback

# ==========================================
# ROBUST DEFERRED LOADING (LAZY LOAD)
# ==========================================
# This script does NOT import the heavy backend.main at the top level.
# It imports it only when a user visits the site (inside the request).
# This prevents "Startup Timeouts" on PythonAnywhere.
# It also catches startup errors and prints them to the browser.
# ==========================================

# Global variable to cache the app after first load
_app_cache = None

def application(environ, start_response):
    global _app_cache

    # If app is already loaded, run it!
    if _app_cache:
        return _app_cache(environ, start_response)

    # First time loading (Request Time)
    try:
        # -------------------------------------------------------
        # 1. LAZY IMPORT: Import main app only on first request
        # -------------------------------------------------------
        # Ensure project path is in sys.path (just in case)
        project_home = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_home not in sys.path:
            sys.path.insert(0, project_home)

        from backend.main import app as fastapi_app
        from a2wsgi import ASGIMiddleware
        
        # 2. WRAP IN A2WSGI
        _app_cache = ASGIMiddleware(fastapi_app)
        
        # Run the newly created app immediately for this request
        return _app_cache(environ, start_response)

    except Exception:
        # -------------------------------------------------------
        # 3. ERROR HANDLING: Show error in browser instead of 502
        # -------------------------------------------------------
        error_msg = traceback.format_exc()
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/html; charset=utf-8')]
        
        html = f"""
        <html>
        <head>
            <title>Startup Failed</title>
            <meta charset="utf-8">
        </head>
        <body style="font-family: monospace; padding: 20px; background: #fff0f0; color: #333;">
            <h1 style="color: #d32f2f;">Application Startup Failed</h1>
            <p>The application crashed or timed out during the initial import. Here is the traceback:</p>
            <hr>
            <pre style="background: #fff; border: 1px solid #ccc; padding: 15px; overflow: auto; font-size: 14px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">{error_msg}</pre>
            <hr>
            <p><em>Please ensure all dependencies are installed and the database is accessible.</em></p>
        </body>
        </html>
        """
        start_response(status, response_headers)
        return [html.encode('utf-8')]
