from dataclasses import dataclass
import sqlite3

@dataclass
class Observation:
    id: int
    target_name: str
    ra: str
    declination: str
    notes: str
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row):
        return cls(
            id=row['id'],
            target_name=row['target_name'],
            ra=row['ra'],
            declination=row['declination'],
            notes=row['notes'],
            created_at=row['created_at']
        )