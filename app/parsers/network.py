
"""Validation des réponses provenant des serveurs Pythonpédia."""

from pydantic import TypeAdapter, HttpUrl

from app.models.topic import Item
from app.models.peer import Peer

from app.models.responses import (
    TopicsResponse,
    TopicContentResponse,
    DirectoryResponse,
)

TOPICS_ADAPTER = TypeAdapter(TopicsResponse)
CONTENT_ADAPTER = TypeAdapter(TopicContentResponse)
DIRECTORY_ADAPTER = TypeAdapter(DirectoryResponse)

def parse_topics(data: object) -> list[str]:
    """Valide GET /ws/topics."""

    if not isinstance(data, list) or len(data) > 1000:
        raise ValueError("Format des topics invalide")

    topics = TOPICS_ADAPTER.validate_python(data)

    if any(
        not topic.strip() or len(topic) > 100
        for topic in topics
    ):
        raise ValueError("Nom de topic invalide")

    return list(dict.fromkeys(topics))


def parse_topic_content(data: object) -> dict[str, list[str]]:
    """Valide GET /ws/topic/{topic}."""

    if not isinstance(data, dict) or len(data) > 100:
        raise ValueError("Format du topic invalide")

    content = CONTENT_ADAPTER.validate_python(data)

    result: dict[str, list[str]] = {}

    for name, urls in content.items():

        if len(urls) > 500:
            raise ValueError("Trop d'URL dans un item")

        # Notre modèle Item valide et normalise les URL.
        item = Item(name=name, urls=urls)

        result[item.name] = item.urls

    return result


def parse_directory(data: object) -> list[str]:
    """Valide GET /ws/annuaire."""

    if not isinstance(data, list) or len(data) > 1000:
        raise ValueError("Format de l'annuaire invalide")

    addresses = DIRECTORY_ADAPTER.validate_python(data)

    peers = [
        Peer(url=HttpUrl(url), approved=False)
        for url in addresses
    ]

    return list(
        dict.fromkeys(
            str(peer.url).rstrip("/")
            for peer in peers
        )
    )