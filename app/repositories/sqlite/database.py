"""Connexion et initialisation de SQLite."""

import sqlite3

from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator

from app.config import get_settings


@contextmanager
def connect(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Ouvre une connexion SQLite transactionnelle."""

    path = db_path or get_settings().DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path, timeout=5)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        yield connection

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def initialize(db_path: Path | None = None) -> None:
    """Crée les tables si elles n'existent pas."""

    with connect(db_path) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS links (
                topic TEXT NOT NULL,
                item TEXT NOT NULL,
                url TEXT NOT NULL,
                PRIMARY KEY (topic, item, url)
            );

            CREATE TABLE IF NOT EXISTS peers (
                url TEXT PRIMARY KEY,
                approved INTEGER NOT NULL DEFAULT 0
                    CHECK(approved IN (0, 1))
            );
        """)