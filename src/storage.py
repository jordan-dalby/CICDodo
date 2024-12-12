import sqlite3
from typing import Set
from pathlib import Path
import logging

class ReleaseStorage:
    def __init__(self, db_file: str = "releases/releases.db"):
        logging.debug(f"Initializing ReleaseStorage with db_file: {db_file}")
        self.db_file = Path(db_file)
        # Ensure the parent directory exists
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        logging.debug(f"Created database directory: {self.db_file.parent}")
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database and create the releases table if it doesn't exist."""
        logging.debug("Initializing database and creating releases table if needed")
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
            logging.debug("Database initialization complete")

    def is_version_released(self, mod_id: str, version: str) -> bool:
        """Check if a specific version of a mod has been released."""
        logging.debug(f"Checking if version {version} of mod {mod_id} is released")
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT 1 FROM releases WHERE mod_id = ? AND version = ?',
                (mod_id, version)
            )
            result = cursor.fetchone() is not None
            logging.debug(f"Version {version} of mod {mod_id} is {'already' if result else 'not'} released")
            return result

    def mark_version_released(self, mod_id: str, version: str) -> None:
        """Mark a specific version of a mod as released."""
        logging.debug(f"Marking version {version} of mod {mod_id} as released")
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR IGNORE INTO releases (mod_id, version) VALUES (?, ?)',
                (mod_id, version)
            )
            conn.commit()
            logging.debug(f"Successfully marked version {version} of mod {mod_id} as released")

    def get_released_versions(self, mod_id: str) -> Set[str]:
        """Get all released versions for a specific mod."""
        logging.debug(f"Getting all released versions for mod {mod_id}")
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT version FROM releases WHERE mod_id = ?',
                (mod_id,)
            )
            versions = {row[0] for row in cursor.fetchall()}
            logging.debug(f"Found {len(versions)} released versions for mod {mod_id}")
            return versions

    def get_latest_releases(self, limit: int = 10) -> list:
        """Get the most recent releases."""
        logging.debug(f"Getting latest {limit} releases")
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT mod_id, version, release_date 
                FROM releases 
                ORDER BY release_date DESC 
                LIMIT ?
            ''', (limit,))
            releases = cursor.fetchall()
            logging.debug(f"Retrieved {len(releases)} latest releases")
            return releases
