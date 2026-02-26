import sqlite3
from datetime import datetime
from models import Observation

class DatabaseManager:
    def __init__(self, db_path="astro_dat.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        query = """
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_name TEXT NOT NULL,
                ra TEXT NOT NULL,
                declination TEXT NOT NULL,
                notes TEXT,
                created_at TEXT
            )
        """
        with self._get_connection() as conn:
            conn.execute(query)

    def get_recent_observations(self, limit=50, offset=0):
        with self._get_connection() as conn:
            query = "SELECT * FROM observations ORDER BY created_at DESC LIMIT ? OFFSET ?"
            cursor = conn.execute(query, (limit, offset))
            return [Observation.from_row(row) for row in cursor.fetchall()]

    def get_total_count(self):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM observations")
            return cursor.fetchone()[0]

    def add_observation(self, name, ra, dec, notes):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO observations (target_name, ra, declination, notes, created_at) VALUES (?, ?, ?, ?, ?)",
                (name, ra, dec, notes, timestamp)
            )
            new_id = cursor.lastrowid
            conn.commit()
            return Observation(new_id, name, ra, dec, notes, timestamp) # type: ignore

    def delete_observation(self, target_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM observations WHERE id = ?", (target_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def search_observations(self, query: str, limit=50, offset=0) -> list[Observation]:
        with self._get_connection() as conn:
            sql = "SELECT * FROM observations WHERE target_name LIKE ? ORDER BY created_at DESC LIMIT ? OFFSET ?"
            search_term = f"%{query}%"
            cursor = conn.execute(sql, (search_term, limit, offset))
            return [Observation.from_row(row) for row in cursor.fetchall()]
        