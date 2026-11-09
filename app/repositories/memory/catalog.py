"""Catalogue en mémoire, sans persistance entre redémarrages."""
from copy import deepcopy
from app.models.topic import Topic, Item


class MemoryCatalogRepository:
    def __init__(self, initial_topics: list[Topic] | None = None):
        self._topics: dict[str, Topic] = {}
        for topic in initial_topics or []:
            self.add_topic(topic)

    def get_topics(self) -> list[str]:
        return sorted(self._topics)

    def get_topic(self, name: str) -> Topic | None:
        topic = self._topics.get(name)
        return deepcopy(topic) if topic is not None else None

    def add_topic(self, topic: Topic) -> int:
        current = self._topics.setdefault(topic.name, Topic(name=topic.name, items=[]))
        inserted = 0
        for source in topic.items:
            target = next((item for item in current.items if item.name == source.name), None)
            if target is None:
                target = Item(name=source.name, urls=[])
                current.items.append(target)
            seen = set(target.urls)
            for url in source.urls:
                if url not in seen:
                    target.urls.append(url)
                    seen.add(url)
                    inserted += 1
        return inserted
