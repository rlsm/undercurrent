"""
Undercurrent — Database models

Works with two backends:
  - SQLite (default, zero setup) — good for trying it on your own machine
  - Postgres (set DATABASE_URL env var) — what you'll use on Render

Render gives you a free Postgres instance and an env var called DATABASE_URL
automatically once you attach it to your web service. This file detects it
and switches automatically — you don't need to change any other file.
"""
import os
import sqlite3
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL")
USING_POSTGRES = bool(DATABASE_URL)

if USING_POSTGRES:
    import psycopg2
    import psycopg2.extras
    # Render's DATABASE_URL sometimes starts with postgres:// — psycopg2 wants postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

SQLITE_PATH = "undercurrent.db"


class PostgresWrapper:
    """
    Makes psycopg2 behave enough like sqlite3's connection that the rest of
    the app (models.py / scraper.py / app.py) doesn't need two code paths.
    Translates '?' placeholders to '%s' and SQLite-isms to Postgres at query time.
    """
    def __init__(self, conn):
        self.conn = conn

    def execute(self, query, params=()):
        cur = self.conn.cursor()
        query = query.replace("?", "%s")
        query = query.replace("AUTOINCREMENT", "")
        query = query.replace("INTEGER PRIMARY KEY", "SERIAL PRIMARY KEY")
        query = query.replace("CURRENT_TIMESTAMP", "NOW()")
        cur.execute(query, params)
        return cur

    def commit(self):
        self.conn.commit()


@contextmanager
def get_db():
    if USING_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield PostgresWrapper(conn)
            conn.commit()
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                source_id TEXT,
                title TEXT NOT NULL,
                venue TEXT,
                city TEXT,
                event_date TEXT,
                lineup TEXT,
                genres TEXT,
                ticket_url TEXT,
                raw_description TEXT,

                ai_summary TEXT,
                ai_verdict TEXT,
                ai_reasoning TEXT,

                status TEXT DEFAULT 'pending',
                editor_note TEXT,

                scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TEXT,
                published_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                tier TEXT DEFAULT 'free',
                draw_entries INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_status ON events(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_source_id ON events(source, source_id)")


if __name__ == "__main__":
    init_db()
    backend = "Postgres" if USING_POSTGRES else "SQLite"
    print(f"Database initialized using {backend}.")
