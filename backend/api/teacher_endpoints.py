from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from starlette.requests import Request
import sqlite3
import os
from .dependencies import get_db
from .security_utils import verify_password

teacher_router = APIRouter()

# Teacher authentication dependency
async def get_teacher_user(request: Request, db: sqlite3.Connection = Depends(get_db)):
    """Verify user is logged in and has teacher role"""
    user = None
    try:
        if request.session.get("token") == "admin_logged_in":
            username = request.session.get("user")
            if username:
                user_row = db.execute("SELECT id, username, is_admin, is_teacher FROM Users WHERE username = ?", (username,)).fetchone()
                if user_row and (user_row[2] or user_row[3]):  # is_admin or is_teacher
                    user = user_row
    except Exception:
        pass
    
    if not user:
        raise HTTPException(status_code=401, detail="Teacher authentication required")
    return user

@teacher_router.get("/")
async def serve_teacher_dashboard(request: Request, db: sqlite3.Connection = Depends(get_db)):
    """Serve teacher panel or redirect to login"""
    user = None
    try:
        if request.session.get("token") == "admin_logged_in":
            username = request.session.get("user")
            if username:
                user_row = db.execute("SELECT id, username, is_admin, is_teacher FROM Users WHERE username = ?", (username,)).fetchone()
                if user_row and (user_row[2] or user_row[3]):  # is_admin or is_teacher
                    user = user_row
    except:
        pass
    
    if not user:
        # Redirect to admin login (we'll reuse it)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        login_path = os.path.join(base_dir, "login.html")
        if os.path.exists(login_path):
            with open(login_path, "r", encoding="utf-8") as f:
                return HTMLResponse(f.read())
        return HTMLResponse("<h1>Login Page Not Found</h1>", status_code=404)
    
    # Serve teacher panel
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    teacher_path = os.path.join(base_dir, "teacher.html")
    if os.path.exists(teacher_path):
        with open(teacher_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Teacher Panel Not Found</h1>", status_code=404)

# Dashboard endpoints
@teacher_router.get("/dashboard-stats")
async def get_teacher_dashboard_stats(user=Depends(get_teacher_user), db: sqlite3.Connection = Depends(get_db)):
    """Get summary statistics for teacher dashboard"""
    teacher_id = user[0]
    
    try:
        # Get assigned students
        assigned_students = db.execute(
            "SELECT COUNT(*) FROM TeacherStudents WHERE teacher_id = ?", (teacher_id,)
        ).fetchone()[0]
        
        # Get all students if teacher, or assigned students if specific teacher
        if user[2]:  # is_admin - can see all
            total_students = db.execute("SELECT COUNT(*) FROM Users WHERE is_admin = 0 AND is_teacher = 0").fetchone()[0]
            new_this_month = db.execute(
                "SELECT COUNT(*) FROM Users WHERE is_admin = 0 AND is_teacher = 0 AND created_at >= date('now', 'start of month')"
            ).fetchone()[0]
        else:
            total_students = assigned_students
            # New students assigned this month
            new_this_month = db.execute(
                "SELECT COUNT(*) FROM TeacherStudents WHERE teacher_id = ? AND assigned_date >= date('now', 'start of month')",
                (teacher_id,)
            ).fetchone()[0]
        
        # Get active courses (courses that have students enrolled)
        active_courses = db.execute(
            "SELECT COUNT(DISTINCT active_course_id) FROM Users WHERE active_course_id IS NOT NULL AND is_admin = 0"
        ).fetchone()[0]
        
        # Most popular course
        popular_course = db.execute(
            "SELECT c.name FROM Courses c JOIN Users u ON c.id = u.active_course_id WHERE u.is_admin = 0 GROUP BY c.id ORDER BY COUNT(*) DESC LIMIT 1"
        ).fetchone()
        popular_course_name = popular_course[0] if popular_course else "-"
        
        # Weekly words learned (approximate from UserProgress)
        weekly_words = db.execute(
            "SELECT COUNT(*) FROM UserProgress WHERE repetition_count > 0"
        ).fetchone()[0]
        
        return {
            "total_students": total_students,
            "new_this_month": new_this_month,
            "active_courses": active_courses,
            "popular_course": popular_course_name,
            "weekly_words": weekly_words
        }
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        return {
            "total_students": 0,
            "new_this_month": 0,
            "active_courses": 0,
            "popular_course": "-",
            "weekly_words": 0
        }

@teacher_router.get("/daily-activity")
async def get_daily_activity(user=Depends(get_teacher_user), db: sqlite3.Connection = Depends(get_db)):
    """Get today's activity statistics"""
    try:
        # Students active today (based on last_login)
        active_today = db.execute(
            "SELECT COUNT(*) FROM Users WHERE is_admin = 0 AND is_teacher = 0 AND DATE(last_login) = DATE('now')"
        ).fetchone()[0]
        
        total_students = db.execute(
            "SELECT COUNT(*) FROM Users WHERE is_admin = 0 AND is_teacher = 0"
        ).fetchone()[0]
        
        # Approximate words learned today (this is simplified without activity log)
        words_today = db.execute(
            "SELECT COUNT(*) FROM UserProgress WHERE repetition_count > 0"
        ).fetchone()[0] if total_students > 0 else 0
        
        return {
            "active_today": active_today,
            "total_students": total_students,
            "words_learned": min(words_today, active_today * 20),  # Approximate
            "units_completed": active_today * 2  # Approximate
        }
    except:
        return {
            "active_today": 0,
            "total_students": 0,
            "words_learned": 0,
            "units_completed": 0
        }

@teacher_router.get("/weekly-trend")
async def get_weekly_trend(user=Depends(get_teacher_user), db: sqlite3.Connection = Depends(get_db)):
    """Get 7-day activity trend for chart"""
    try:
        # Generate data for last 7 days
        days = []
        counts = []
        
        for i in range(6, -1, -1):
            day = db.execute(
                f"SELECT COUNT(*) FROM Users WHERE is_admin = 0 AND DATE(last_login) = DATE('now', '-{i} days')"
            ).fetchone()[0]
            
            days.append(["Pzt", "Sal", "Çrş", "Prş", "Cum", "Cmt", "Paz"][(6-i) % 7])
            counts.append(day)
        
        return {
            "labels": days,
            "data": counts
        }
    except:
        return {
            "labels": ["Pzt", "Sal", "Çrş", "Prş", "Cum", "Cmt", "Paz"],
            "data": [0, 0, 0, 0, 0, 0, 0]
        }

@teacher_router.get("/alerts")
async def get_alerts(user=Depends(get_teacher_user), db: sqlite3.Connection = Depends(get_db)):
    """Get students requiring attention"""
    try:
        # Inactive 5+ days
        inactive = db.execute(
            "SELECT COUNT(*) FROM Users WHERE is_admin = 0 AND is_teacher = 0 AND (last_login IS NULL OR DATE(last_login) <= DATE('now', '-5 days'))"
        ).fetchone()[0]
        
        # Below daily goal (simplified - assume goal is 10 words/day)
        # This is approximate without detailed activity tracking
        below_goal = db.execute(
            "SELECT COUNT(*) FROM Users WHERE is_admin = 0 AND is_teacher = 0"
        ).fetchone()[0] // 3  # Rough estimate
        
        # Above goal
        above_goal = db.execute(
            "SELECT COUNT(*) FROM Users WHERE is_admin = 0 AND is_teacher = 0 AND DATE(last_login) = DATE('now')"
        ).fetchone()[0]
        
        # Completed unit recently (simplified)
        completed_unit = 0
        
        return {
            "inactive_5days": inactive,
            "below_goal": below_goal,
            "above_goal": above_goal,
            "completed_unit": completed_unit
        }
    except:
        return {
            "inactive_5days": 0,
            "below_goal": 0,
            "above_goal": 0,
            "completed_unit": 0
        }

@teacher_router.get("/students")
async def get_students_list(
    status: str = "all",
    search: str = "",
    user=Depends(get_teacher_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get list of students with filtering and search"""
    teacher_id = user[0]
    
    try:
        # Base query for students
        query = """
            SELECT 
                u.id,
                u.username,
                u.created_at,
                u.last_login,
                c.name as course_name,
                (SELECT COUNT(*) FROM UserProgress WHERE user_id = u.id AND repetition_count > 0) as learned_words
            FROM Users u
            LEFT JOIN Courses c ON u.active_course_id = c.id
            WHERE u.is_admin = 0 AND u.is_teacher = 0
        """
        
        # Add search filter
        if search:
            query += f" AND u.username LIKE '%{search}%'"
        
        cursor = db.execute(query)
        students = []
        
        for row in cursor.fetchall():
            student_id, username, created_at, last_login, course_name, learned_words = row
            
            # Calculate status
            if last_login:
                from datetime import datetime, timedelta
                last_login_date = datetime.fromisoformat(str(last_login))
                days_inactive = (datetime.now() - last_login_date).days
            else:
                days_inactive = 999
            
            if days_inactive >= 7:
                student_status = "risk"
            elif days_inactive >= 3:
                student_status = "inactive"
            else:
                student_status = "active"
            
            # Filter by status
            if status != "all" and student_status != status:
                continue
            
            # Calculate streak (simplified)
            streak = 0 if days_inactive > 1 else 5  # Simplified
            
            students.append({
                "id": student_id,
                "username": username,
                "email": f"{username}@email.com",  # Simplified
                "created_at": created_at,
                "last_login": last_login or "Hiç giriş yapmadı",
                "course_name": course_name or "Kurs seçilmemiş",
                "learned_words": learned_words,
                "streak": streak,
                "status": student_status,
                "days_inactive": days_inactive
            })
        
        return {"students": students}
    except Exception as e:
        print(f"Students list error: {e}")
        return {"students": []}

@teacher_router.get("/students/{student_id}")
async def get_student_detail(
    student_id: int,
    user=Depends(get_teacher_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get detailed information about a specific student"""
    try:
        # Get student basic info
        student = db.execute("""
            SELECT 
                u.id,
                u.username,
                u.created_at,
                u.last_login,
                c.name as course_name,
                c.id as course_id
            FROM Users u
            LEFT JOIN Courses c ON u.active_course_id = c.id
            WHERE u.id = ?
        """, (student_id,)).fetchone()
        
        if not student:
            raise HTTPException(404, "Student not found")
        
        # Get learning progress
        learned_words = db.execute("""
            SELECT COUNT(*) FROM UserProgress
            WHERE user_id = ? AND repetition_count > 0
        """, (student_id,)).fetchone()[0]
        
        # Calculate Repetition Breakdown (New/Mid/Mastered)
        rep_stats = db.execute("""
            SELECT 
                COUNT(CASE WHEN repetition_count BETWEEN 1 AND 5 THEN 1 END) as new_count,
                COUNT(CASE WHEN repetition_count BETWEEN 6 AND 10 THEN 1 END) as mid_count,
                COUNT(CASE WHEN repetition_count >= 11 THEN 1 END) as mastered_count
            FROM UserProgress
            WHERE user_id = ?
        """, (student_id,)).fetchone()

        total_words = db.execute("""
            SELECT COUNT(*) FROM Words WHERE course_id = ?
        """, (student[5],)).fetchone()[0] if student[5] else 0
        
        # Get recent words
        recent_words = db.execute("""
            SELECT w.english, w.turkish, uwp.repetition_count, uwp.next_review_step
            FROM UserProgress uwp
            JOIN Words w ON uwp.word_id = w.id
            WHERE uwp.user_id = ?
            ORDER BY uwp.last_updated DESC LIMIT 10
        """, (student_id,)).fetchall()
        
        learned_list = [{
            "english": row[0],
            "turkish": row[1],
            "repetition": row[2],
            "next_review": f"Adım {row[3]}"
        } for row in recent_words]
        
        progress_percent = int((learned_words / total_words * 100)) if total_words > 0 else 0
        
        return {
            "id": student[0],
            "username": student[1],
            "email": f"{student[1]}@email.com",
            "created_at": student[2],
            "last_login": student[3] or "Hiç giriş yapmadı",
            "course_name": student[4] or "Kurs seçilmemiş",
            "learned_words": learned_words,
            "repetition_stats": {
                "new": rep_stats[0] or 0,
                "mid": rep_stats[1] or 0,
                "mastered": rep_stats[2] or 0
            },
            "total_words": total_words,
            "progress_percent": progress_percent,
            "recent_words": learned_list,
            "streak": 5  # Simplified
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Student detail error: {e}")
        raise HTTPException(500, str(e))

# === CLASS STATISTICS ===
@teacher_router.get("/class-stats")
async def get_class_stats(
    user=Depends(get_teacher_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get comprehensive class-wide statistics"""
    teacher_id = user[0]
    is_admin = user[4]
    
    try:
        # Get student IDs based on role
        if is_admin:
            students = db.execute("SELECT id FROM Users WHERE is_admin = 0").fetchall()
        else:
            students = db.execute("""
                SELECT student_id FROM TeacherStudents WHERE teacher_id = ?
            """, (teacher_id,)).fetchall()
        
        student_ids = [s[0] for s in students]
        
        if not student_ids:
            return {
                "total_students": 0,
                "class_average": 0,
                "top_performer": None,
                "most_improved": None,
                "average_words_per_student": 0,
                "completion_rate": 0
            }
        
        # Calculate class statistics
        placeholders = ','.join('?' * len(student_ids))
        
        # Average words learned
        avg_words = db.execute(f"""
            SELECT AVG(word_count) FROM (
                SELECT COUNT(DISTINCT word_id) as word_count
                FROM UserProgress
                WHERE user_id IN ({placeholders}) AND repetition_count > 0
                GROUP BY user_id
            )
        """, student_ids).fetchone()[0] or 0
        
        # Top performer
        top = db.execute(f"""
            SELECT u.id, u.username, COUNT(DISTINCT uwp.word_id) as words
            FROM Users u
            LEFT JOIN UserProgress uwp ON u.id = uwp.user_id AND uwp.repetition_count > 0
            WHERE u.id IN ({placeholders})
            GROUP BY u.id
            ORDER BY words DESC
            LIMIT 1
        """, student_ids).fetchone()
        
        # Completion rate (students with active course)
        completion = db.execute(f"""
            SELECT 
                COUNT(CASE WHEN active_course_id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*)
            FROM Users WHERE id IN ({placeholders})
        """, student_ids).fetchone()[0] or 0
        
        return {
            "total_students": len(student_ids),
            "class_average": round(avg_words, 1),
            "top_performer": {"id": top[0], "name": top[1], "words": top[2]} if top else None,
            "average_words_per_student": round(avg_words, 1),
            "completion_rate": round(completion, 1)
        }
    except Exception as e:
        print(f"Class stats error: {e}")
        raise HTTPException(500, str(e))

@teacher_router.get("/leaderboard")
async def get_leaderboard(
    limit: int = 10,
    user=Depends(get_teacher_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get student leaderboard ranked by learned words"""
    teacher_id = user[0]
    is_admin = user[4]
    
    try:
        if is_admin:
            rows = db.execute("""
                SELECT 
                    u.id, u.username, u.last_login,
                    COUNT(DISTINCT uwp.word_id) as learned_words
                FROM Users u
                LEFT JOIN UserProgress uwp ON u.id = uwp.user_id AND uwp.repetition_count > 0
                WHERE u.is_admin = 0
                GROUP BY u.id
                ORDER BY learned_words DESC
                LIMIT ?
            """, (limit,)).fetchall()
        else:
            rows = db.execute("""
                SELECT 
                    u.id, u.username, u.last_login,
                    COUNT(DISTINCT uwp.word_id) as learned_words
                FROM TeacherStudents ts
                JOIN Users u ON ts.student_id = u.id
                LEFT JOIN UserProgress uwp ON u.id = uwp.user_id AND uwp.repetition_count > 0
                WHERE ts.teacher_id = ?
                GROUP BY u.id
                ORDER BY learned_words DESC
                LIMIT ?
            """, (teacher_id, limit)).fetchall()
        
        return {"leaderboard": [{
            "rank": idx + 1,
            "id": r[0],
            "username": r[1],
            "last_login": r[2],
            "learned_words": r[3]
        } for idx, r in enumerate(rows)]}
    except Exception as e:
        print(f"Leaderboard error: {e}")
        return {"leaderboard": []}

@teacher_router.get("/comparison")
async def get_student_comparison(
    user=Depends(get_teacher_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get comparative table of all students"""
    teacher_id = user[0]
    is_admin = user[4]
    
    try:
        if is_admin:
            rows = db.execute("""
                SELECT 
                    u.id, u.username, u.created_at, u.last_login,
                    c.name as course_name,
                    COUNT(DISTINCT uwp.word_id) as learned_words
                FROM Users u
                LEFT JOIN Courses c ON u.active_course_id = c.id
                LEFT JOIN UserProgress uwp ON u.id = uwp.user_id AND uwp.repetition_count > 0
                WHERE u.is_admin = 0
                GROUP BY u.id
                ORDER BY learned_words DESC
            """).fetchall()
        else:
            rows = db.execute("""
                SELECT 
                    u.id, u.username, u.created_at, u.last_login,
                    c.name as course_name,
                    COUNT(DISTINCT uwp.word_id) as learned_words
                FROM TeacherStudents ts
                JOIN Users u ON ts.student_id = u.id
                LEFT JOIN Courses c ON u.active_course_id = c.id
                LEFT JOIN UserProgress uwp ON u.id = uwp.user_id AND uwp.repetition_count > 0
                WHERE ts.teacher_id = ?
                GROUP BY u.id
                ORDER BY learned_words DESC
            """, (teacher_id,)).fetchall()
        
        # Calculate days since last login
        from datetime import datetime
        comparison = []
        for r in rows:
            days_inactive = 0
            if r[3]:
                try:
                    last_login = datetime.fromisoformat(r[3])
                    days_inactive = (datetime.now() - last_login).days
                except:
                    days_inactive = 999
            else:
                days_inactive = 999
            
            comparison.append({
                "id": r[0],
                "username": r[1],
                "joined": r[2],
                "last_login": r[3] or "Hiç giriş yapmadı",
                "course": r[4] or "Kurs yok",
                "learned_words": r[5],
                "days_inactive": days_inactive
            })
        
        return {"students": comparison}
    except Exception as e:
        print(f"Comparison error: {e}")
        return {"students": []}

# Teacher Notes Management
@teacher_router.get("/notes/{student_id}")
async def get_teacher_notes(
    student_id: int,
    user=Depends(get_teacher_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get teacher notes for a specific student"""
    teacher_id = user[0]
    try:
        notes = db.execute("""
            SELECT id, note, created_at
            FROM TeacherNotes
            WHERE teacher_id = ? AND student_id = ?
            ORDER BY created_at DESC
        """, (teacher_id, student_id)).fetchall()
        
        return {"notes": [{"id": n[0], "note": n[1], "created_at": n[2]} for n in notes]}
    except:
        return {"notes": []}

# === CLASS GOALS ===
@teacher_router.get("/class-goals")
async def get_class_goals(
    user=Depends(get_teacher_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get class-wide goals"""
    teacher_id = user[0]
    
    try:
        goals = db.execute("""
            SELECT id, goal_name, target_value, current_value, deadline, completed
            FROM ClassGoals
            WHERE teacher_id = ?
            ORDER BY deadline ASC
        """, (teacher_id,)).fetchall()
        
        from datetime import datetime, date
        result_goals = []
        for g in goals:
            deadline = datetime.fromisoformat(g[4]).date() if g[4] else None
            days_remaining = (deadline - date.today()).days if deadline else 0
            
            result_goals.append({
                "id": g[0],
                "goal_name": g[1],
                "target_value": g[2],
                "current_value": g[3],
                "deadline": g[4],
                "completed": g[5],
                "days_remaining": days_remaining,
                "notified": False  # Would be tracked in DB
            })
        
        return {"goals": result_goals}
    except Exception as e:
        print(f"Get class goals error: {e}")
        return {"goals": []}

@teacher_router.post("/class-goals")
async def create_class_goal(
    goal_data: dict,
    user=Depends(get_teacher_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """Create a new class-wide goal"""
    teacher_id = user[0]
    
    try:
        goal_name = goal_data.get('goal_name')
        target_value = goal_data.get('target_value')
        deadline = goal_data.get('deadline')
        
        if not goal_name or not target_value or not deadline:
            raise HTTPException(400, "Missing required fields")
        
        # Create ClassGoals table if not exists
        db.execute("""
            CREATE TABLE IF NOT EXISTS ClassGoals (
                id INTEGER PRIMARY KEY,
                teacher_id INTEGER NOT NULL,
                goal_name TEXT NOT NULL,
                target_value INTEGER NOT NULL,
                current_value INTEGER DEFAULT 0,
                deadline DATE,
                completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES Users(id)
            )
        """)
        
        db.execute("""
            INSERT INTO ClassGoals (teacher_id, goal_name, target_value, deadline)
            VALUES (?, ?, ?, ?)
        """, (teacher_id, goal_name, target_value, deadline))
        db.commit()
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Create class goal error: {e}")
        raise HTTPException(500, str(e))

@teacher_router.post("/notes")
async def add_teacher_note(
    student_id: int,
    note: str,
    user=Depends(get_teacher_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """Add a new teacher note"""
    teacher_id = user[0]
    try:
        db.execute("""
            INSERT INTO TeacherNotes (teacher_id, student_id, note)
            VALUES (?, ?, ?)
        """, (teacher_id, student_id, note))
        db.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(500, str(e))

@teacher_router.delete("/notes/{note_id}")
async def delete_teacher_note(
    note_id: int,
    user=Depends(get_teacher_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """Delete a teacher note"""
    try:
        db.execute("DELETE FROM TeacherNotes WHERE id = ?", (note_id,))
        db.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(500, str(e))

# Student Goals Management
@teacher_router.get("/goals/{student_id}")
async def get_student_goals(
    student_id: int,
    user=Depends(get_teacher_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """Get goals for a specific student"""
    try:
        goals = db.execute("""
            SELECT id, goal_type, target_value, current_value, deadline, completed
            FROM StudentGoals
            WHERE student_id = ?
            ORDER BY completed, deadline
        """, (student_id,)).fetchall()
        
        return {"goals": [{
            "id": g[0],
            "type": g[1],
            "target": g[2],
            "current": g[3],
            "deadline": g[4],
            "completed": bool(g[5])
        } for g in goals]}
    except:
        return {"goals": []}

@teacher_router.post("/goals")
async def create_student_goal(
    student_id: int,
    goal_type: str,
    target_value: int,
    deadline: str = None,
    user=Depends(get_teacher_user),
    db: sqlite3.Connection = Depends(get_db)
):
    """Create a new goal for student"""
    teacher_id = user[0]
    try:
        db.execute("""
            INSERT INTO StudentGoals (student_id, teacher_id, goal_type, target_value, deadline)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, teacher_id, goal_type, target_value, deadline))
        db.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(500, str(e))
