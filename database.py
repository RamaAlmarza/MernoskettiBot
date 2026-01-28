import sqlite3
import datetime

DB_NAME = "commands.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Warnings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reason TEXT,
            staff_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    # Notes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT,
            staff_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    # Moderation Logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moderation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            reason TEXT,
            timestamp TEXT NOT NULL,
            extra_data TEXT
        )
    """)

    conn.commit()
    conn.close()

# --- Warnings ---

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
        SELECT id, reason, staff_id, timestamp FROM warnings WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def remove_warning(warn_id, user_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if user_id:
        cursor.execute("DELETE FROM warnings WHERE id = ? AND user_id = ?", (warn_id, user_id))
    else:
        cursor.execute("DELETE FROM warnings WHERE id = ?", (warn_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

# --- Notes ---

def add_note(user_id, text, staff_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO notes (user_id, text, staff_id, timestamp)
        VALUES (?, ?, ?, ?)
    """, (user_id, text, staff_id, timestamp))
    conn.commit()
    conn.close()

def get_notes(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, text, staff_id, timestamp FROM notes WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_note(note_id, user_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if user_id:
        cursor.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
    else:
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def clear_notes(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def edit_note(note_id, new_text, user_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if user_id:
        cursor.execute("UPDATE notes SET text = ? WHERE id = ? AND user_id = ?", (new_text, note_id, user_id))
    else:
        cursor.execute("UPDATE notes SET text = ? WHERE id = ?", (new_text, note_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

# --- Moderation Logs ---

def log_action(action, user_id, staff_id, reason, extra_data=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO moderation_logs (action, user_id, staff_id, reason, timestamp, extra_data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (action, user_id, staff_id, reason, timestamp, extra_data))
    case_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return case_id

def get_mod_logs(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, action, staff_id, reason, timestamp, extra_data FROM moderation_logs WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_case(case_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, action, user_id, staff_id, reason, timestamp, extra_data FROM moderation_logs WHERE id = ?
    """, (case_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_mod_stats(staff_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action, COUNT(*) FROM moderation_logs WHERE staff_id = ? GROUP BY action
    """, (staff_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_recent_moderations(limit=50):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT action, user_id, staff_id, reason, timestamp FROM moderation_logs ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# Initialize DB on module load (or call it explicitly in main)
init_db()
