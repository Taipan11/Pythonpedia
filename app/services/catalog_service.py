
"""Logique métier de l'encyclopédie Pythonpédia."""

from app.models.topic import Topic, Item
from app.repositories.catalog_repository import CatalogRepository


class CatalogService:
    """Gestion des ressources indépendamment du stockage."""

    def __init__(self, repository: CatalogRepository):
        self.repository = repository

    def get_topics(self) -> list[str]:
        return self.repository.get_topics()

    def get_topic(self, name: str) -> Topic | None:
        return self.repository.get_topic(name)

    def get_topic_public(
        self,
        name: str,
    ) -> dict[str, list[str]] | None:
        topic = self.get_topic(name)

        if topic is None:
            return None

        return {
            item.name: item.urls
            for item in topic.items
        }

    def add_topic(self, topic: Topic) -> int:
        """Ajoute un topic ou enrichit son contenu."""
        return self.repository.add_topic(topic)

    def add_item(self, topic_name: str, item: Item) -> int:
        """Ajoute un item ou de nouvelles références."""
        return self.add_topic(
            Topic(name=topic_name, items=[item])
        )

    def merge_remote_content(
        self,
        name: str,
        payload: object,
    ) -> int:
        """Valide les données distantes avant fusion."""

        if not isinstance(payload, dict) or len(payload) > 100:
            raise ValueError(
                "Un topic distant doit contenir "
                "100 items maximum."
            )

        items: list[Item] = []

        for item_name, urls in payload.items():
            if (
                not isinstance(item_name, str)
                or not isinstance(urls, list)
                or len(urls) > 500
            ):
                raise ValueError(
                    "Format ou taille des items incorrects."
                )

            items.append(
                Item(name=item_name, urls=urls)
            )

        return self.add_topic(
            Topic(name=name, items=items)
        )

    
    def search_topics(self, query: str) -> list[str]:
        """Recherche dans les noms des topics et de leurs items."""

        text = query.strip().casefold()

        if not text or len(text) > 100:
            return []

        results: list[tuple[int, str]] = []

        for name in self.get_topics():
            topic = self.get_topic(name)

            if topic is None:
                continue

            # Correspondance exacte avec le topic.
            if name.casefold() == text:
                score = 3

            # Correspondance partielle avec le topic.
            elif text in name.casefold():
                score = 2

            # Correspondance avec le nom d'un item.
            elif any(
                text in item.name.casefold()
                for item in topic.items
            ):
                score = 1

            else:
                continue

            results.append((score, name))

        # Les correspondances les plus pertinentes arrivent en premier.
        results.sort(
            key=lambda result: (
                -result[0],
                result[1].casefold(),
            )
        )

        return [
            name
            for _, name in results
        ]
