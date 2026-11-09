"""Annuaire en mémoire : découverte sans approbation automatique."""
from copy import deepcopy
from app.models.peer import Peer


class MemoryPeerRepository:
    def __init__(self, initial_peers: list[Peer] | None = None):
        self._peers: dict[str, Peer] = {}
        for peer in initial_peers or []:
            self.add_peer(peer)

    def get_peers(self) -> list[Peer]:
        return [deepcopy(self._peers[key]) for key in sorted(self._peers)]

    def add_peer(self, peer: Peer) -> bool:
        key = str(peer.url).rstrip('/')
        existing = self._peers.get(key)
        if existing is None:
            self._peers[key] = deepcopy(peer)
            return True
        if peer.approved:
            existing.approved = True
        if peer.name and not existing.name:
            existing.name = peer.name
        return False

    def approve_peer(self, url: str) -> bool:
        """Approuve un serveur enregistré en mémoire."""

        key = url.rstrip("/")

        peer = self._peers.get(key)

        if peer is None:
            return False

        peer.approved = True
        return True