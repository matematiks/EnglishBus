import sys
import os

def check_import(module_name):
    try:
        __import__(module_name)
        return "OK"
    except ImportError as e:
        return f"MISSING ({e})"
    except Exception as e:
        return f"ERROR ({e})"

def application(environ, start_response):
    output = []
    output.append("=== ENGLISHBUS ENVIRONMENT CHECK ===")
    output.append(f"Python Version: {sys.version}")
    output.append(f"Current Directory: {os.getcwd()}")
    output.append(f"Sys Path: {sys.path}")
    output.append("-" * 30)
    
    modules_to_check = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "jose",
        "passlib",
        "multipart",
        "a2wsgi"
    ]
    
    for mod in modules_to_check:
        status = check_import(mod)
        output.append(f"{mod.ljust(15)}: {status}")
        
    output.append("-" * 30)
    output.append("=== CHECK COMPLETE ===")
    
    response_body = "\n".join(output).encode('utf-8')
    status = '200 OK'
    response_headers = [
        ('Content-type', 'text/plain; charset=utf-8'),
        ('Content-Length', str(len(response_body)))
    ]
    start_response(status, response_headers)
    return [response_body]
