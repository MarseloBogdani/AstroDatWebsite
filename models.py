from dataclasses import dataclass
import sqlite3

@dataclass
class Observation:
    id: int
    user_id: int
    target_name: str
    ra: str
    declination: str
    notes: str
    created_at: str
    

    @classmethod
    def from_row(cls, row: sqlite3.Row):
        return cls(
            id=row['id'],
            user_id=row['id_user'],
            target_name=row['target_name'],
            ra=row['ra'],
            declination=row['declination'],
            notes=row['notes'],
            created_at=row['created_at']
        )
    
@dataclass
class User:
    id: int
    username: str
    password: str
    created_at: str

    @classmethod
    def from_row(cls, row:sqlite3.Row):
        return cls(
        id=row['id'],
        username=row['username'],
        password=row['password'],
        created_at=row['created_at']
        )