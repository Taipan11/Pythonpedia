from pathlib import Path

from app.config import get_settings
from app.models.peer import Peer

from .database import connect, initialize


class SQLitePeerRepository:

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or get_settings().DB_PATH
        initialize(self.db_path)

    def get_peers(self) -> list[Peer]:
        with connect(self.db_path) as db:
            rows = db.execute(
                "SELECT url, approved FROM peers ORDER BY url"
            ).fetchall()

        return [
            Peer(url=url, approved=bool(approved))
            for url, approved in rows
        ]

    def add_peer(self, peer: Peer) -> bool:
        url = str(peer.url).rstrip("/")

        with connect(self.db_path) as db:
            result = db.execute(
                """
                INSERT OR IGNORE INTO peers(url, approved)
                VALUES (?, ?)
                """,
                (url, int(peer.approved)),
            )

            created = result.rowcount > 0

            if peer.approved:
                db.execute(
                    "UPDATE peers SET approved = 1 WHERE url = ?",
                    (url,),
                )

            return created

    def approve_peer(self, url: str) -> bool:
        """Approuve un serveur enregistré dans SQLite."""

        key = url.rstrip("/")

        with connect(self.db_path) as db:
            result = db.execute(
                """
                UPDATE peers
                SET approved = 1
                WHERE url = ?
                """,
                (key,),
            )

            return result.rowcount > 0