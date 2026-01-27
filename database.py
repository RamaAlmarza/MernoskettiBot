import sqlite3
import datetime

DB_NAME = "warnings.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reason TEXT,
            staff_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_warning(user_id, reason, staff_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO warnings (user_id, reason, staff_id, timestamp)
        VALUES (?, ?, ?, ?)
    """, (user_id, reason, staff_id, timestamp))
    conn.commit()
    conn.close()

def get_warnings(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reason, staff_id, timestamp FROM warnings WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# Initialize DB on module load (or call it explicitly in main)
init_db()
