from pathlib import Path

from app.config import get_settings
from app.models.topic import Topic, Item

from .database import connect, initialize


class SQLiteCatalogRepository:

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or get_settings().DB_PATH
        initialize(self.db_path)

    def get_topics(self) -> list[str]:
        with connect(self.db_path) as db:
            rows = db.execute(
                "SELECT DISTINCT topic FROM links ORDER BY topic"
            ).fetchall()

        return [row[0] for row in rows]

    def get_topic(self, name: str) -> Topic | None:
        with connect(self.db_path) as db:
            rows = db.execute(
                "SELECT item, url FROM links WHERE topic = ?",
                (name,),
            ).fetchall()

        if not rows:
            return None

        items: dict[str, list[str]] = {}

        for item_name, url in rows:
            items.setdefault(item_name, []).append(url)

        return Topic(
            name=name,
            items=[
                Item(name=item_name, urls=urls)
                for item_name, urls in items.items()
            ],
        )

    def add_topic(self, topic: Topic) -> int:
        rows = [
            (topic.name, item.name, url)
            for item in topic.items
            for url in item.urls
        ]

        with connect(self.db_path) as db:
            before = db.total_changes

            db.executemany(
                """
                INSERT OR IGNORE INTO links(topic, item, url)
                VALUES (?, ?, ?)
                """,
                rows,
            )

            return db.total_changes - before