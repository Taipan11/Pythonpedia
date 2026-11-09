
"""Dépendances partagées de l'application Pythonpédia."""

import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.data.seed import INITIAL_TOPICS

from app.repositories.catalog_repository import CatalogRepository
from app.repositories.peer_repository import PeerRepository

from app.repositories.memory.catalog import MemoryCatalogRepository
from app.repositories.memory.peer import MemoryPeerRepository

from app.repositories.sqlite.catalog import SQLiteCatalogRepository
from app.repositories.sqlite.peer import SQLitePeerRepository

from app.services.catalog_service import CatalogService
from app.services.peer_service import PeerService
from app.services.sync_service import SyncService
from app.config import get_settings

from app.services.discovery_service import DiscoveryService


# ============================================================
# REPOSITORIES
# ============================================================

@lru_cache(maxsize=1)
def get_catalog_repository() -> CatalogRepository:
    """Retourne le repository du catalogue."""

    backend = get_settings().STORAGE_BACKEND

    if backend == "memory":
        return MemoryCatalogRepository(INITIAL_TOPICS)

    if backend == "sqlite":
        return SQLiteCatalogRepository()

    raise ValueError(
        f"Backend de stockage inconnu : {backend}"
    )


@lru_cache(maxsize=1)
def get_peer_repository() -> PeerRepository:
    """Retourne le repository des serveurs."""

    backend = get_settings().STORAGE_BACKEND

    if backend == "memory":
        return MemoryPeerRepository()

    if backend == "sqlite":
        return SQLitePeerRepository()

    raise ValueError(
        f"Backend de stockage inconnu : {backend}"
    )


# ============================================================
# SERVICES
# ============================================================

def get_catalog_service(
    repository: Annotated[
        CatalogRepository,
        Depends(get_catalog_repository),
    ],
) -> CatalogService:
    return CatalogService(repository)


def get_peer_service(
    repository: Annotated[
        PeerRepository,
        Depends(get_peer_repository),
    ],
) -> PeerService:
    return PeerService(repository)


def get_sync_service(
    catalog: Annotated[
        CatalogService,
        Depends(get_catalog_service),
    ],
    peers: Annotated[
        PeerService,
        Depends(get_peer_service),
    ],
) -> SyncService:
    return SyncService(
        catalog=catalog,
        peers=peers,
    )


def get_discovery_service(
    peers: Annotated[
        PeerService,
        Depends(get_peer_service),
    ],
) -> DiscoveryService:
    """Retourne le service de découverte réseau."""
    return DiscoveryService(peers=peers)
