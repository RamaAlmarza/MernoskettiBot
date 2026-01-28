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
            language TEXT DEFAULT 'es',
            prefix TEXT DEFAULT '?'
        )
    """)

    # Ranking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ranking (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            points INTEGER DEFAULT 0
        )
    """)

    # Reaction Roles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reaction_roles (
            message_id INTEGER PRIMARY KEY,
            emoji TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()

# --- Guild Config ---

def get_config(guild_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT language, prefix FROM guild_config WHERE guild_id = ?", (guild_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"language": row[0], "prefix": row[1]}
    return {"language": "es", "prefix": "?"}

def set_config(guild_id, language=None, prefix=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check if exists
    cursor.execute("SELECT language, prefix FROM guild_config WHERE guild_id = ?", (guild_id,))
    row = cursor.fetchone()

    if row:
        curr_lang, curr_prefix = row
        new_lang = language if language else curr_lang
        new_prefix = prefix if prefix else curr_prefix
        cursor.execute("UPDATE guild_config SET language = ?, prefix = ? WHERE guild_id = ?", (new_lang, new_prefix, guild_id))
    else:
        new_lang = language if language else "es"
        new_prefix = prefix if prefix else "?"
        cursor.execute("INSERT INTO guild_config (guild_id, language, prefix) VALUES (?, ?, ?)", (guild_id, new_lang, new_prefix))

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

def get_ranking():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, points FROM ranking ORDER BY points DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def reset_ranking():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ranking")
    conn.commit()
    conn.close()

# --- Reaction Roles ---

def add_reaction_role(message_id, emoji, role_id, channel_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO reaction_roles (message_id, emoji, role_id, channel_id) VALUES (?, ?, ?, ?)", (message_id, emoji, role_id, channel_id))
    conn.commit()
    conn.close()

def get_reaction_role(message_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT emoji, role_id, channel_id FROM reaction_roles WHERE message_id = ?", (message_id,))
    row = cursor.fetchone()
    conn.close()
    return row

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
