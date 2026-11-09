
"""Administration des communications entre serveurs."""

from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import (
    get_peer_service,
    get_sync_service,
    get_discovery_service,
)

from app.models.peer import Peer
from app.security import require_admin

from app.services.peer_service import PeerService
from app.services.sync_service import SyncService
from app.services.discovery_service import DiscoveryService


router = APIRouter(
    prefix="/admin/network",
    tags=["Network"],
    dependencies=[Depends(require_admin)],
)

PeerDep = Annotated[
    PeerService,
    Depends(get_peer_service),
]

SyncDep = Annotated[
    SyncService,
    Depends(get_sync_service),
]

DiscoveryDep = Annotated[
    DiscoveryService,
    Depends(get_discovery_service),
]


# ============================================================
# GESTION DES SERVEURS
# ============================================================

@router.get("/peers", response_model=list[Peer])
def list_peers(peers: PeerDep):
    """Liste les serveurs enregistrés."""
    return peers.get_peers()


@router.post("/peers")
def register_peer(
    peer: Peer,
    peers: PeerDep,
):
    """Enregistre et approuve manuellement un serveur."""

    created = peers.register(
        str(peer.url),
        approved=True,
    )

    return {"created": created}


@router.patch("/peers/{peer_id}/approve")
def approve_peer(
    peer_id: int,
    peers: PeerDep,
):
    """Approuve un serveur découvert."""

    approved = peers.approve_peer(peer_id)

    if not approved:
        raise HTTPException(
            status_code=404,
            detail="Serveur inconnu",
        )

    return {
        "approved": True,
        "peer_id": peer_id,
    }


# ============================================================
# CONSULTATION DES SERVEURS
# ============================================================

@router.get("/peers/{peer_id}/topics")
async def fetch_peer_topics(
    peer_id: int,
    peers: PeerDep,
    sync: SyncDep,
):
    """Consulte les topics d'un serveur approuvé."""

    peer = peers.get_peer(peer_id)

    if peer is None:
        raise HTTPException(
            status_code=404,
            detail="Serveur inconnu",
        )

    if not peer.approved:
        raise HTTPException(
            status_code=403,
            detail="Serveur non approuvé",
        )

    try:
        return await sync.fetch_topics(peer)

    except (httpx.HTTPError, ValueError, TypeError) as error:
        raise HTTPException(
            status_code=502,
            detail="Serveur distant indisponible",
        ) from error


# ============================================================
# DÉCOUVERTE RÉSEAU — BONUS
# ============================================================

@router.post("/discover")
async def discover_network(
    discovery: DiscoveryDep,
):
    """Découvre les serveurs Pythonpédia compatibles."""

    try:
        return await discovery.discover()

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


# ============================================================
# SYNCHRONISATION
# ============================================================

@router.post("/sync")
async def synchronize(sync: SyncDep):
    """Synchronise tous les serveurs approuvés."""
    return await sync.synchronize()


@router.post("/peers/{peer_id}/sync")
async def synchronize_peer(
    peer_id: int,
    peers: PeerDep,
    sync: SyncDep,
):
    """Synchronise uniquement le serveur sélectionné."""

    peer = peers.get_peer(peer_id)

    if peer is None:
        raise HTTPException(
            status_code=404,
            detail="Serveur inconnu",
        )

    if not peer.approved:
        raise HTTPException(
            status_code=403,
            detail="Serveur non approuvé",
        )

    try:
        return await sync.synchronize_peer(peer)

    except (httpx.HTTPError, ValueError, TypeError) as error:
        raise HTTPException(
            status_code=502,
            detail="Synchronisation impossible",
        ) from error
