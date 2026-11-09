"""Contrat de stockage du catalogue."""
from typing import Protocol
from app.models.topic import Topic


class CatalogRepository(Protocol):
    def get_topics(self) -> list[str]: ...

    def get_topic(self, name: str) -> Topic | None: ...

    def add_topic(self, topic: Topic) -> int:
        """Fusionne le topic et retourne le nombre d'URL nouvelles."""
        ...
