
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
import sqlite3
import sys
import os
import csv
import glob
import shutil
import zipfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.dependencies import get_db
from api.security_utils import verify_password, get_password_hash # Ensure these are available or use auth middleware logic
#Ideally we should use a proper auth dependency from auth_endpoints or similar
# For now, let's replicate/import the logic
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from api.security_utils import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: sqlite3.Connection = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub") # In login we used sub=user_id, wait. Let's check logic.
        # Login endpoint: token = create_access_token({"sub": str(user_id), "username": username})
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    user = db.execute("SELECT id, username, is_admin FROM Users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_current_admin_user(current_user: tuple = Depends(get_current_user_from_token)):
    # user is a tuple/Row: (id, username, is_admin)
    if not current_user[2]: # is_admin index
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

router = APIRouter(
    dependencies=[Depends(get_current_admin_user)]
)

KURSLAR_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "kurslar")
WORDS_PER_UNIT = 50

class ImportRequest(BaseModel):
    folder_name: str

@router.get("/scan")
def scan_courses():
    """Scan kurslar directory for valid course folders"""
    courses = []
    if not os.path.exists(KURSLAR_PATH):
        os.makedirs(KURSLAR_PATH, exist_ok=True)

    for item in os.listdir(KURSLAR_PATH):
        item_path = os.path.join(KURSLAR_PATH, item)
        if os.path.isdir(item_path):
            csv_path = os.path.join(item_path, "words.csv")
            if os.path.exists(csv_path):
                # Count words
                try:
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        row_count = sum(1 for row in f) - 1 # minus header
                except:
                    row_count = 0
                    
                courses.append({
                    "folder": item,
                    "name": item.replace("_", " "),
                    "word_count": row_count,
                    "valid": True
                })
    return {"courses": courses}

@router.post("/upload_course")
async def upload_course(file: UploadFile = File(...)):
    """Upload a .zip file containing a course folder"""
    if not file.filename.endswith('.zip'):
        raise HTTPException(400, "Only .zip files are allowed")
    
    try:
        # Save temp zip
        temp_zip = os.path.join(KURSLAR_PATH, "temp_upload.zip")
        with open(temp_zip, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Extract
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(KURSLAR_PATH)
            
        # Cleanup
        os.remove(temp_zip)
        
        return {"status": "success", "message": f"Course uploaded and extracted successfully. Go to Scan tab to import it."}
    except Exception as e:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)
        raise HTTPException(500, f"Extraction failed: {str(e)}")

@router.post("/import_course")
def import_course(
    request: ImportRequest,
    db: sqlite3.Connection = Depends(get_db)
):
    """Import a course from filesystem (CSV)"""
    folder = request.folder_name
    course_path = os.path.join(KURSLAR_PATH, folder)
    csv_path = os.path.join(course_path, "words.csv")
    
    if not os.path.exists(csv_path):
        raise HTTPException(404, "words.csv not found")

    try:
        # 1. Ensure Course Exists
        course_name = folder.replace("_", " ")
        cursor = db.execute("SELECT id FROM Courses WHERE name = ?", (course_name,))
        row = cursor.fetchone()
        
        if row:
            course_id = row[0]
        else:
            db.execute("INSERT INTO Courses (name, total_words, order_number) VALUES (?, 0, 1)", (course_name,))
            course_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

        # 2. Process CSV
        total_imported = 0
        units_touched = set()
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # Normalize headers (strip spaces)
            try:
                reader.fieldnames = [name.strip() for name in reader.fieldnames]
            except:
                pass # empty file
            
            for row in reader:
                try:
                    # Parse Row
                    # Handle 'id' or 'order' alias
                    order_str = row.get('order', row.get('id'))
                    if not order_str or not str(order_str).strip():
                        continue # Skip empty rows
                        
                    order = int(str(order_str).strip())
                    
                    english = row.get('english', '').strip()
                    turkish = row.get('turkish', '').strip()
                    image = row.get('image_file', '').strip()
                    audio_en = row.get('audio_en_file', '').strip()
                    audio_tr = row.get('audio_tr_file', '').strip()
                    
                    if not english: continue

                    # 3. Calculate Unit
                    # Logical Unit based on COUNT, not ID gaps
                    # This ensures 50 words per unit even if IDs are 1, 10, 100...
                    unit_order = (total_imported // WORDS_PER_UNIT) + 1
                    
                    # Ensure Unit Exists
                    if unit_order not in units_touched:
                        unit_name = f"Unit {unit_order}" # Simple Naming
                        
                        # Check exist
                        u_row = db.execute(
                            "SELECT id FROM Units WHERE course_id = ? AND order_number = ?", 
                            (course_id, unit_order)
                        ).fetchone()
                        
                        if not u_row:
                            db.execute(
                                "INSERT INTO Units (course_id, name, order_number, word_count) VALUES (?, ?, ?, 0)",
                                (course_id, unit_name, unit_order)
                            )
                            unit_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                        else:
                            unit_id = u_row[0]
                            
                        units_touched.add(unit_order)
                        
                    # Get Unit Id again (inefficient but safe)
                    unit_id = db.execute(
                        "SELECT id FROM Units WHERE course_id = ? AND order_number = ?", 
                        (course_id, unit_order)
                    ).fetchone()[0]

                    # 4. Upsert Word
                    # Try to find by ORDER NUMBER within Course
                    # This preserves ID if order matches
                    w_row = db.execute(
                        "SELECT id FROM Words WHERE course_id = ? AND order_number = ?",
                        (course_id, order)
                    ).fetchone()
                    
                    # Path prefixes
                    img_path = f"/assets/{folder}/images/{image}" if image else None
                    aud_en_path = f"/assets/{folder}/ing_audio/{audio_en}" if audio_en else None
                    aud_tr_path = f"/assets/{folder}/tr_audio/{audio_tr}" if audio_tr else None

                    if w_row:
                        # UPDATE
                        db.execute("""
                            UPDATE Words SET 
                            unit_id=?, english=?, turkish=?, image_url=?, audio_en_url=?, audio_tr_url=?
                            WHERE id=?
                        """, (unit_id, english, turkish, img_path, aud_en_path, aud_tr_path, w_row[0]))
                    else:
                        # INSERT
                        db.execute("""
                            INSERT INTO Words 
                            (course_id, unit_id, english, turkish, image_url, audio_en_url, audio_tr_url, order_number)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (course_id, unit_id, english, turkish, img_path, aud_en_path, aud_tr_path, order))
                        
                    total_imported += 1
                    
                except ValueError as e:
                    print(f"Skipping row {row}: {e}")
                    continue

        # 5. Update Counts
        db.execute("UPDATE Courses SET total_words = ? WHERE id = ?", (total_imported, course_id))
        
        # Update Unit Counts
        for u_order in units_touched:
            db.execute("""
                UPDATE Units 
                SET word_count = (SELECT COUNT(*) FROM Words WHERE unit_id = Units.id)
                WHERE course_id = ? AND order_number = ?
            """, (course_id, u_order))

        db.commit()
        return {
            "status": "success", 
            "message": f"Imported {total_imported} words into {len(units_touched)} units",
            "course_id": course_id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

@router.get("/dashboard")
def get_admin_dashboard(db: sqlite3.Connection = Depends(get_db)):
    """Get admin stats"""
    try:
        users = db.execute("SELECT COUNT(*) FROM Users").fetchone()[0]
        units = db.execute("SELECT COUNT(*) FROM Units").fetchone()[0]
        words = db.execute("SELECT COUNT(*) FROM Words").fetchone()[0]
        
        return {
            "total_users": users,
            "total_units": units,
            "total_words": words
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
