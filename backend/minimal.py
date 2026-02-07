from fastapi import FastAPI
import os
import sys

# Ensure backend folder is recognized in path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "status": "Minimal App Working", 
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "path": sys.path
    }
