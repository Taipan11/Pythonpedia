
"""Découverte des serveurs Pythonpédia sur le réseau."""

import asyncio
import json

import httpx

from app.config import get_settings
from app.parsers.network import parse_topics
from app.services.peer_service import (
    PeerService,
    normalize_peer_url,
)


class DiscoveryService:
    """Détecte les serveurs Pythonpédia parmi les candidats autorisés."""

    def __init__(self, peers: PeerService):
        self.peers = peers
        self.settings = get_settings()

    async def discover(self) -> dict:
        """Recherche des serveurs compatibles et enrichit l'annuaire."""

        candidates = list(dict.fromkeys(
            self.settings.DISCOVERY_CANDIDATES
        ))

        if len(candidates) > 30:
            raise ValueError(
                "30 serveurs candidats maximum."
            )

        semaphore = asyncio.Semaphore(5)

        async def probe(
            client: httpx.AsyncClient,
            address: str,
        ) -> tuple[str | None, str | None]:
            """Vérifie qu'une adresse héberge une API Pythonpédia."""

            async with semaphore:
                try:
                    url = normalize_peer_url(address)

                    async with client.stream(
                        "GET",
                        f"{url}/ws/topics",
                    ) as response:
                        response.raise_for_status()

                        data = bytearray()

                        async for chunk in response.aiter_bytes():
                            data.extend(chunk)

                            if len(data) > self.settings.MAX_RESPONSE_BYTES:
                                raise ValueError(
                                    "Réponse distante trop volumineuse"
                                )

                    raw = json.loads(data)

                    # Valide le format attendu : list[str].
                    parse_topics(raw)

                    return url, None

                except (
                    httpx.HTTPError,
                    ValueError,
                    TypeError,
                    UnicodeError,
                ) as error:
                    return None, f"{address}: {error}"

        # Vérification des adresses en parallèle.
        async with httpx.AsyncClient(
            timeout=self.settings.REQUEST_TIMEOUT,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            responses = await asyncio.gather(
                *(
                    probe(client, address)
                    for address in candidates
                )
            )

        compatible = list(dict.fromkeys(
            url
            for url, error in responses
            if url is not None
        ))

        errors = [
            error
            for url, error in responses
            if error is not None
        ]

        # Enregistrer uniquement les nouveaux serveurs.
        known = set(self.peers.get_peer_urls())

        discovered: list[str] = []

        for url in compatible:
            if url in known:
                continue

            self.peers.register(
                url,
                approved=False,
            )

            known.add(url)
            discovered.append(url)

        return {
            "candidates_checked": len(candidates),
            "compatible": compatible,
            "discovered": discovered,
            "added_count": len(discovered),
            "errors": errors,
        }
