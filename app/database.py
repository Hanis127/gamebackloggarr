import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "/data/gamebackloggarr.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            igdb_id INTEGER UNIQUE,
            title TEXT NOT NULL,
            cover_url TEXT,
            summary TEXT,
            genres TEXT,
            platforms TEXT,
            release_year INTEGER,
            rating REAL,
            status TEXT DEFAULT 'backlog',
            suggested_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id),
            value INTEGER NOT NULL CHECK(value IN (-1, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(game_id, user_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def migrate_db():
    """Run any pending migrations on existing DB."""
    import os
    db_path = os.getenv("DB_PATH", "/data/gamebackloggarr.db")
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path, check_same_thread=False)
    try:
        conn.execute("ALTER TABLE games ADD COLUMN game_modes TEXT")
        conn.commit()
    except Exception:
        pass  # already exists
    conn.close()