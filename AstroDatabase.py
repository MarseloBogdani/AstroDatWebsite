from queue import Full
import sqlite3
from datetime import datetime
from typing import Optional
from models import Observation,User
from my_exceptions import *

class DatabaseManager:
    def __init__(self, db_path="astro_dat.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        query1 = """
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_user INTEGER,
                target_name TEXT NOT NULL,
                ra TEXT NOT NULL,
                declination TEXT NOT NULL,
                notes TEXT,
                likes_count INTEGER,
                created_at TEXT
            )
        """
        query2 = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL
        )"""

        with self._get_connection() as conn:
            conn.execute(query1)
            conn.execute(query2)

    def get_recent_observations(self, limit=50, offset=0):
        with self._get_connection() as conn:
            query = "SELECT * FROM observations ORDER BY created_at DESC LIMIT ? OFFSET ?"
            cursor = conn.execute(query, (limit, offset))
            return [Observation.from_row(row) for row in cursor.fetchall()]

    def get_total_count(self):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM observations")
            return cursor.fetchone()[0]

    def add_observation(self, name, ra, dec, notes, user_id):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO observations (id_user,target_name,ra,declination,notes,created_at) VALUES (?,?,?,?,?,?)",
                (user_id,name, ra, dec, notes, timestamp)
            )
            new_id = cursor.lastrowid
            if new_id is None:
                raise DatabaseError("Failed to retrieve new observation id")
            conn.commit()
            return Observation(new_id, user_id, name, ra, dec, notes, timestamp)

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
            search_term = f"{query}%"
            cursor = conn.execute(sql, (search_term, limit, offset))
            return [Observation.from_row(row) for row in cursor.fetchall()]
        
    def add_user(self, username: str, hashed_password: str) -> Optional[User]:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = self._get_connection()
        try:

            with conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, password, created_at) VALUES (?,?,?)",
                    (username, hashed_password, timestamp)
                )
                new_id = cursor.lastrowid
            
            if new_id:
                return User(new_id, username, hashed_password, timestamp)
            return None
        except sqlite3.IntegrityError:
            raise UserAlreadyExistsError()
        finally:
            conn.close()  
        
    def delete_user(self, target_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM users WHERE id = ?", (target_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def get_user(self, username: str) -> Optional[User]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT id, username, password, created_at FROM users WHERE username = ? LIMIT 1", (username,))
            row = cursor.fetchone()

            if not row:
                return None
            return User.from_row(row)
            
    def search_users_recent_observations(self, user_id: int) -> list[Observation]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM observations WHERE id_user = ? ORDER BY created_at DESC ", 
                                  (user_id,))
            return [Observation.from_row(row) for row in cursor.fetchall()]
        
    def count_users_exoplanets(self, user_id: int) -> int:
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM observations WHERE id_user = ? AND target_name LIKE '%Exoplanet%'", 
                (user_id,)
            )
            return cursor.fetchone()[0]
        
    def add_like(self,observation_id: int) -> bool:

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute("UPDATE targets SET likes_count = likes_count + 1 WHERE id = ?", (observation_id,))
                return True
        except Exception as e:
            raise Exception("Problem with adding like.Try again later")
        finally:
            conn.close()

    def upvote_like(self,observation_id: int) -> bool:

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute("UPDATE targets SET likes_count = likes_count + 1 WHERE id = ?", (observation_id,))
                return True
        except Exception as e:
            raise Exception("Problem with adding like.Try again later")
        finally:
            conn.close()

    def downvote_like(self,observation_id: int) -> bool:
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute("UPDATE targets SET likes_count = GREATEST(0, likes_count - 1) WHERE id = ?", (observation_id,))
                return True
        except Exception as e:
            raise Exception("Problem with adding like.Try again later")
        finally:
            conn.close()
        
            
