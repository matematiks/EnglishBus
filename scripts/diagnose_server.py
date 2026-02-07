
import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "englishbus.db")
CSV_PATH = os.path.join(BASE_DIR, "kurslar", "A1_Foundation", "words.csv")

print(f"--- DIAGNOSTICS ---")
print(f"Base Dir: {BASE_DIR}")
print(f"DB Path: {DB_PATH}")
print(f"DB Exists: {os.path.exists(DB_PATH)}")
print(f"CSV Path: {CSV_PATH}")
print(f"CSV Exists: {os.path.exists(CSV_PATH)}")

if os.path.exists(DB_PATH):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, name, word_count FROM Units")
        units = c.fetchall()
        print(f"\nUnits Found ({len(units)}):")
        for u in units:
            print(f" - ID: {u[0]} | Name: {u[1]} | Count: {u[2]}")
        
        c.execute("SELECT count(*) FROM Words")
        word_count = c.fetchone()[0]
        print(f"\nTotal Words in DB: {word_count}")
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

if os.path.exists(CSV_PATH):
    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            print(f"\nCSV First Line: {f.readline().strip()}")
            line_count = 1 + sum(1 for line in f)
            print(f"CSV Line Count: {line_count}")
    except Exception as e:
        print(f"CSV Error: {e}")
