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

    # Starboard table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS starboard (
            message_id INTEGER PRIMARY KEY,
            star_message_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            count INTEGER NOT NULL
        )
    """)

    # Guild Config table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_config (
            guild_id INTEGER PRIMARY KEY,
            prefix TEXT DEFAULT '!',
            autorole_id INTEGER DEFAULT 0
        )
    """)

    # Migration: Check if autorole_id column exists
    cursor.execute("PRAGMA table_info(guild_config)")
    columns = [info[1] for info in cursor.fetchall()]
    if "autorole_id" not in columns:
        cursor.execute("ALTER TABLE guild_config ADD COLUMN autorole_id INTEGER DEFAULT 0")

    # Ranking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ranking (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            points INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

# --- Warnings ---

def get_config(guild_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT prefix, autorole_id FROM guild_config WHERE guild_id = ?", (guild_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"prefix": row[0], "autorole_id": row[1]}
    return {"prefix": "!", "autorole_id": 0}

def set_config(guild_id, prefix=None, autorole_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT prefix, autorole_id FROM guild_config WHERE guild_id = ?", (guild_id,))
    row = cursor.fetchone()

    if row:
        curr_prefix, curr_autorole = row
        new_prefix = prefix if prefix is not None else curr_prefix
        new_autorole = autorole_id if autorole_id is not None else curr_autorole
        cursor.execute("UPDATE guild_config SET prefix = ?, autorole_id = ? WHERE guild_id = ?", (new_prefix, new_autorole, guild_id))
    else:
        new_prefix = prefix if prefix is not None else "!"
        new_autorole = autorole_id if autorole_id is not None else 0
        cursor.execute("INSERT INTO guild_config (guild_id, prefix, autorole_id) VALUES (?, ?, ?)", (guild_id, new_prefix, new_autorole))

    conn.commit()
    conn.close()

# --- Ranking ---

def update_points(user_id, username, points):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ranking (user_id, username, points) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET points = points + ?, username = ?", (user_id, username, points, points, username))
    conn.commit()
    conn.close()

def set_points(user_id, username, points):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ranking (user_id, username, points) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET points = ?, username = ?", (user_id, username, points, points, username))
    conn.commit()
    conn.close()

def get_points(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM ranking WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def get_ranking():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, points FROM ranking ORDER BY points DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

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

def get_all_warnings():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, reason, staff_id, timestamp FROM warnings ORDER BY id DESC")
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

# --- Starboard ---

def get_starboard_entry(message_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT star_message_id, channel_id, count FROM starboard WHERE message_id = ?", (message_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_starboard_entry(message_id, star_message_id, channel_id, count):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO starboard (message_id, star_message_id, channel_id, count) VALUES (?, ?, ?, ?)",
                   (message_id, star_message_id, channel_id, count))
    conn.commit()
    conn.close()

def update_starboard_entry(message_id, count):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE starboard SET count = ? WHERE message_id = ?", (count, message_id))
    conn.commit()
    conn.close()

# Initialize DB on module load (or call it explicitly in main)
init_db()
