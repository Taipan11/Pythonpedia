
"""Interface locale de gestion de Pythonpédia.

Utilisation :
    python -m app.cli seed
    python -m app.cli add-peer http://127.0.0.1:8889
    python -m app.cli peers
    python -m app.cli topics
    python -m app.cli sync
"""

import argparse
import asyncio
import json

from app.config import get_settings
from app.data.seed import INITIAL_TOPICS

from app.dependencies import (
    get_catalog_repository,
    get_peer_repository,
)

from app.services.catalog_service import CatalogService
from app.services.peer_service import PeerService
from app.services.sync_service import SyncService


def get_services() -> tuple[CatalogService, PeerService]:
    """Construit les services avec les repositories configurés."""

    catalog = CatalogService(get_catalog_repository())
    peers = PeerService(get_peer_repository())

    return catalog, peers


def seed_catalog(catalog: CatalogService) -> None:
    """Ajoute les références initiales à notre encyclopédie."""

    for topic in INITIAL_TOPICS:
        added = catalog.add_topic(topic)

        print(
            f"{topic.name}: {added} nouvelle(s) URL"
        )


def register_peer(peers: PeerService, url: str) -> None:
    """Enregistre et approuve un serveur."""

    created = peers.register(
        url,
        approved=True,
    )

    if created:
        print(f"Serveur ajouté et approuvé : {url}")
    else:
        print(f"Serveur déjà connu, approbation mise à jour : {url}")


def list_peers(peers: PeerService) -> None:
    """Affiche l'annuaire local."""

    records = peers.get_peers()

    if not records:
        print("Aucun serveur enregistré.")
        return

    for peer in records:
        status = "[OK]" if peer.approved else "[À approuver]"
        print(f"{status} {peer.url}")


def list_topics(catalog: CatalogService) -> None:
    """Affiche les topics disponibles localement."""

    topics = catalog.get_topics()

    if not topics:
        print("Aucun topic disponible.")
        return

    for topic in topics:
        print(f"- {topic}")


async def synchronize(
    catalog: CatalogService,
    peers: PeerService,
) -> None:
    """Synchronise les serveurs approuvés."""

    if not peers.get_peer_urls(approved_only=True):
        print(
            "Aucun serveur approuvé. "
            "Utiliser add-peer URL."
        )
        return

    service = SyncService(
        catalog=catalog,
        peers=peers,
    )

    reports = await service.synchronize()

    for report in reports:
        print(
            json.dumps(
                report.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gestion locale de Pythonpédia"
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    commands.add_parser("seed")
    commands.add_parser("topics")
    commands.add_parser("peers")
    commands.add_parser("sync")

    register = commands.add_parser("add-peer")
    register.add_argument("url")

    args = parser.parse_args()

    catalog, peers = get_services()

    if args.command == "seed":
        seed_catalog(catalog)

    elif args.command == "topics":
        list_topics(catalog)

    elif args.command == "add-peer":
        register_peer(peers, args.url)

    elif args.command == "peers":
        list_peers(peers)

    elif args.command == "sync":
        asyncio.run(
            synchronize(catalog, peers)
        )


if __name__ == "__main__":
    main()
