import sqlite3
from typing import Set
from pathlib import Path

class ReleaseStorage:
    def __init__(self, db_file: str = "releases/releases.db"):
        self.db_file = Path(db_file)
        # Ensure the parent directory exists
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database and create the releases table if it doesn't exist."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS releases (
                    mod_id TEXT,
                    version TEXT,
                    release_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (mod_id, version)
                )
            ''')
            conn.commit()

    def is_version_released(self, mod_id: str, version: str) -> bool:
        """Check if a specific version of a mod has been released."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT 1 FROM releases WHERE mod_id = ? AND version = ?',
                (mod_id, version)
            )
            return cursor.fetchone() is not None

    def mark_version_released(self, mod_id: str, version: str) -> None:
        """Mark a specific version of a mod as released."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR IGNORE INTO releases (mod_id, version) VALUES (?, ?)',
                (mod_id, version)
            )
            conn.commit()

    def get_released_versions(self, mod_id: str) -> Set[str]:
        """Get all released versions for a specific mod."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT version FROM releases WHERE mod_id = ?',
                (mod_id,)
            )
            return {row[0] for row in cursor.fetchall()}

    def get_latest_releases(self, limit: int = 10) -> list:
        """Get the most recent releases."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT mod_id, version, release_date 
                FROM releases 
                ORDER BY release_date DESC 
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
