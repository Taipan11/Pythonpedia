"""Tests d'intégration de Pythonpédia, sans accès réseau réel.

Exécution depuis la racine du projet :
    python -m pytest tests/test_server.py -v
"""

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.data.seed import INITIAL_TOPICS
from app.dependencies import (
    get_catalog_service,
    get_peer_service,
    get_sync_service,
)
from app.main import app
from app.repositories.memory.catalog import MemoryCatalogRepository
from app.repositories.memory.peer import MemoryPeerRepository
from app.services.catalog_service import CatalogService
from app.services.peer_service import PeerService
from app.services.sync_service import SyncService


@pytest.fixture
def env(monkeypatch):
    """Configure une clé de test sans dépendre du fichier .env personnel."""
    monkeypatch.setenv("ADMIN_API_KEY", "test-key")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def setup_server(env):
    """Chaque test dispose d'un catalogue et d'un annuaire indépendants."""
    catalog = CatalogService(MemoryCatalogRepository(INITIAL_TOPICS))
    peers = PeerService(MemoryPeerRepository())
    sync = SyncService(catalog=catalog, peers=peers)

    app.dependency_overrides[get_catalog_service] = lambda: catalog
    app.dependency_overrides[get_peer_service] = lambda: peers
    app.dependency_overrides[get_sync_service] = lambda: sync

    with TestClient(app) as client:
        yield client, catalog, peers, sync

    app.dependency_overrides.clear()


def test_public_topics_format(setup_server):
    client, _, _, _ = setup_server
    response = client.get("/ws/topics")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert all(isinstance(topic, str) for topic in response.json())
    assert len(response.json()) >= 3


def test_public_topic_content_format(setup_server):
    client, _, _, _ = setup_server
    topic = client.get("/ws/topics").json()[0]
    response = client.get(f"/ws/topic/{topic}")
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content, dict)
    assert all(
        isinstance(item, str)
        and isinstance(urls, list)
        and all(isinstance(url, str) for url in urls)
        for item, urls in content.items()
    )


def test_unknown_topic_is_404(setup_server):
    client, _, _, _ = setup_server
    response = client.get("/ws/topic/topic-inexistant-pour-test")
    assert response.status_code == 404


def test_public_directory_format(setup_server):
    client, _, _, _ = setup_server
    response = client.get("/ws/annuaire")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert all(isinstance(url, str) for url in response.json())


def test_html_pages(setup_server):
    client, _, _, _ = setup_server
    for path in ("/", "/topics", "/search"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "text/html" in response.headers["content-type"], path


def test_admin_requires_key(setup_server):
    client, _, _, _ = setup_server
    assert client.get("/admin/network/peers").status_code == 403
    assert client.get(
        "/admin/network/peers",
        headers={"X-API-Key": "wrong-key"},
    ).status_code == 403
    assert client.get(
        "/admin/network/peers",
        headers={"X-API-Key": "test-key"},
    ).status_code == 200


@pytest.mark.asyncio
async def test_search_does_not_save_remote_topics(setup_server, monkeypatch):
    _, catalog, peers, sync = setup_server
    peers.register("http://127.0.0.1:8890", approved=True)

    async def fake_get_json(client, url):
        if url.endswith("/ws/topics"):
            return ["topic-distant-test"]
        if url.endswith("/ws/topic/topic-distant-test"):
            return {"asyncio": ["https://docs.python.org/3/library/asyncio.html"]}
        raise AssertionError(f"URL inattendue : {url}")

    monkeypatch.setattr(sync, "_get_json", fake_get_json)
    before = set(catalog.get_topics())
    result = await sync.search_network("asyncio")

    assert result["servers_checked"] == 1
    assert any(entry["topic"] == "topic-distant-test" for entry in result["results"])
    assert set(catalog.get_topics()) == before


@pytest.mark.asyncio
async def test_sync_imports_topics_and_directory(setup_server, monkeypatch):
    _, catalog, peers, sync = setup_server
    peers.register("http://127.0.0.1:8890", approved=True)
    peer = peers.get_peers()[0]

    async def fake_topics(_peer):
        return ["topic-distant-test"]

    async def fake_topic(_peer, _name):
        return {"asyncio": ["https://docs.python.org/3/library/asyncio.html"]}

    async def fake_directory(_peer):
        return ["http://127.0.0.1:8891"]

    monkeypatch.setattr(sync, "fetch_topics", fake_topics)
    monkeypatch.setattr(sync, "fetch_topic", fake_topic)
    monkeypatch.setattr(sync, "fetch_directory", fake_directory)

    first = await sync.synchronize_peer(peer)
    assert first.success is True
    assert catalog.get_topic("topic-distant-test") is not None
    assert "http://127.0.0.1:8891" in peers.get_peer_urls()

    second = await sync.synchronize_peer(peer)
    assert second.urls_added == 0
    assert second.topics_added == 0
