"""Contrat de stockage de l'annuaire."""
from typing import Protocol
from app.models.peer import Peer


class PeerRepository(Protocol):
    def get_peers(self) -> list[Peer]: ...

    def add_peer(self, peer: Peer) -> bool:
        """Crée ou approuve un serveur; True seulement si nouveau."""
        ...

    def approve_peer(self, url: str) -> bool:
        """Approuve un serveur existant et persiste la modification."""
        ...