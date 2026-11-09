
"""Gestion de l'annuaire des serveurs Pythonpédia."""

from pydantic import HttpUrl, TypeAdapter

from app.models.peer import Peer
from app.repositories.peer_repository import PeerRepository


_URL_LIST = TypeAdapter(list[HttpUrl])


def normalize_peer_url(url: str | HttpUrl) -> str:
    """Valide et normalise l'adresse d'un serveur."""

    parsed = HttpUrl(str(url))

    if (
        parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        raise ValueError("URL de serveur invalide")

    return str(parsed).rstrip("/")


class PeerService:
    """Gestion des serveurs indépendamment du stockage."""

    def __init__(self, repository: PeerRepository):
        self.repository = repository

    def get_peers(self) -> list[Peer]:
        """Retourne les serveurs connus."""
        return self.repository.get_peers()

    def get_peer_urls(
        self,
        approved_only: bool = False,
    ) -> list[str]:
        """Retourne les adresses des serveurs."""

        return [
            str(peer.url).rstrip("/")
            for peer in self.get_peers()
            if not approved_only or peer.approved
        ]

    def get_peer(self, peer_id: int) -> Peer | None:
        """Récupère un serveur à partir de son index."""

        peers = self.get_peers()

        if 0 <= peer_id < len(peers):
            return peers[peer_id]

        return None

    def register(
        self,
        url: str,
        approved: bool = False,
    ) -> bool:
        """Enregistre un serveur dans l'annuaire."""

        address = normalize_peer_url(url)

        return self.repository.add_peer(
            Peer(
                url=HttpUrl(address),
                approved=approved,
            )
        )

    def merge_directory(self, data: object) -> int:
        """Intègre les serveurs découverts dans un annuaire."""

        if not isinstance(data, list) or len(data) > 1000:
            raise ValueError("Annuaire invalide")

        urls = _URL_LIST.validate_python(data)

        # Validation complète avant insertion
        addresses = [
            normalize_peer_url(url)
            for url in urls
        ]

        count = 0

        for address in dict.fromkeys(addresses):
            if self.register(address, approved=False):
                count += 1

        return count

    def approve_peer(self, peer_id: int) -> bool:
        """Approuve un serveur déjà présent dans l'annuaire."""

        peer = self.get_peer(peer_id)

        if peer is None:
            return False

        return self.repository.approve_peer(str(peer.url))