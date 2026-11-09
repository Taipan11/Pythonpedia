
"""Interrogation du réseau connu et réplication locale."""

import asyncio
import json

from urllib.parse import quote

import httpx
from pydantic import HttpUrl

from app.config import get_settings

from app.models.peer import Peer, NetworkConfig
from app.models.synchronization import SyncResult

from app.services.catalog_service import CatalogService
from app.services.peer_service import (
    PeerService,
    normalize_peer_url,
)

from app.parsers.network import (
    parse_topics,
    parse_topic_content,
    parse_directory,
)


class SyncService:
    """Communication et synchronisation entre serveurs Pythonpédia."""

    def __init__(
        self,
        catalog: CatalogService,
        peers: PeerService,
        config: NetworkConfig | None = None,
    ):
        self.catalog = catalog
        self.peers = peers
        self.config = config or NetworkConfig()
        self.settings = get_settings()

    def _get_approved_address(self, peer: Peer) -> str:
        """Vérifie qu'un serveur est approuvé."""

        address = normalize_peer_url(peer.url)

        approved = self.peers.get_peer_urls(
            approved_only=True
        )

        if address not in approved:
            raise ValueError(
                f"Serveur non approuvé : {address}"
            )

        return address

    def _create_client(self) -> httpx.AsyncClient:
        """Construit le client HTTP utilisé pour les échanges."""

        return httpx.AsyncClient(
            timeout=self.settings.REQUEST_TIMEOUT,
            follow_redirects=False,
            trust_env=False,
        )

    async def _get_json(
        self,
        client: httpx.AsyncClient,
        url: str,
    ) -> object:
        """Récupère une réponse JSON avec une limite de taille."""

        async with client.stream("GET", url) as response:
            response.raise_for_status()

            data = bytearray()

            async for chunk in response.aiter_bytes():
                data.extend(chunk)

                if len(data) > self.settings.MAX_RESPONSE_BYTES:
                    raise ValueError(
                        "Réponse distante trop volumineuse"
                    )

        return json.loads(data)

    # =========================================================
    # INTERROGATION DES SERVEURS
    # =========================================================

    async def fetch_topics(self, peer: Peer) -> list[str]:
        """Récupère les topics d'un serveur approuvé."""

        address = self._get_approved_address(peer)

        async with self._create_client() as client:
            raw = await self._get_json(
                client,
                f"{address}/ws/topics",
            )

        return parse_topics(raw)

    async def fetch_topic(
        self,
        peer: Peer,
        topic_name: str,
    ) -> dict[str, list[str]]:
        """Récupère les ressources d'un topic distant."""

        address = self._get_approved_address(peer)

        if not topic_name.strip() or len(topic_name) > 100:
            raise ValueError("Nom de topic invalide")

        encoded = quote(topic_name, safe="")

        async with self._create_client() as client:
            raw = await self._get_json(
                client,
                f"{address}/ws/topic/{encoded}",
            )

        return parse_topic_content(raw)

    async def fetch_directory(self, peer: Peer) -> list[str]:
        """Récupère l'annuaire d'un serveur distant."""

        address = self._get_approved_address(peer)

        async with self._create_client() as client:
            raw = await self._get_json(
                client,
                f"{address}/ws/annuaire",
            )

        return parse_directory(raw)

    # =========================================================
    # RECHERCHE FÉDÉRÉE — SANS ENREGISTREMENT
    # =========================================================

    async def search_network(self, query: str) -> dict:
        """Recherche dans les topics et items des serveurs approuvés.

        - Aucune modification du catalogue local.
        - Requêtes concurrentes et limitées.
        - Fusion des références identiques.
        - Conservation des serveurs d'origine.
        """

        text = query.strip().casefold()

        empty = {
            "results": [],
            "errors": [],
            "servers_checked": 0,
        }

        if not text or len(text) > 100:
            return empty

        addresses = list(dict.fromkeys(
            self.peers.get_peer_urls(approved_only=True)
        ))

        if not addresses:
            return empty

        # Limites pour éviter les recherches trop coûteuses.
        max_topics_per_peer = 30
        timeout_per_peer = max(
            5.0,
            min(20.0, float(self.settings.REQUEST_TIMEOUT) * 4),
        )

        semaphore = asyncio.Semaphore(
            self.config.max_concurrent_requests
        )

        async def search_peer(
            address: str,
            client: httpx.AsyncClient,
        ) -> tuple[list[dict], list[dict]]:
            """Interroge un serveur sans enregistrer ses ressources."""

            found: list[dict] = []
            errors: list[dict] = []

            try:
                async with semaphore:
                    async with asyncio.timeout(timeout_per_peer):

                        peer = Peer(
                            url=HttpUrl(address),
                            approved=True,
                        )

                        base_url = self._get_approved_address(peer)

                        # 1. Récupérer les topics disponibles.
                        raw = await self._get_json(
                            client,
                            f"{base_url}/ws/topics",
                        )
                        topics = list(dict.fromkeys(parse_topics(raw)))

                        # 2. Prioriser les noms de topics correspondants.
                        direct_matches = [
                            name for name in topics
                            if text in name.casefold()
                        ]

                        other_topics = [
                            name for name in topics
                            if text not in name.casefold()
                        ]

                        # On recherche également dans les items,
                        # mais avec une limite de requêtes.
                        selected = (
                            direct_matches + other_topics
                        )[:max_topics_per_peer]

                        # 3. Examiner le contenu des topics sélectionnés.
                        for topic in selected:
                            try:
                                encoded = quote(topic, safe="")

                                raw_content = await self._get_json(
                                    client,
                                    f"{base_url}/ws/topic/{encoded}",
                                )

                                content = parse_topic_content(
                                    raw_content
                                )

                                topic_matches = (
                                    text in topic.casefold()
                                )

                                item_matches = any(
                                    text in name.casefold()
                                    for name in content
                                )

                                if not (topic_matches or item_matches):
                                    continue

                                if topic.casefold() == text:
                                    score = 3
                                elif topic_matches:
                                    score = 2
                                else:
                                    score = 1

                                found.append({
                                    "peer": base_url,
                                    "topic": topic,
                                    "items": content,
                                    "sources": [base_url],
                                    "score": score,
                                })

                            except (
                                httpx.HTTPError,
                                ValueError,
                                TypeError,
                            ) as error:
                                errors.append({
                                    "peer": base_url,
                                    "error": f"{topic}: {error}",
                                })

            except TimeoutError:
                errors.append({
                    "peer": address,
                    "error": "Délai de recherche dépassé",
                })

            except (
                httpx.HTTPError,
                ValueError,
                TypeError,
            ) as error:
                errors.append({
                    "peer": address,
                    "error": str(error),
                })

            return found, errors

        # 4. Utiliser un client HTTP partagé.
        async with self._create_client() as client:
            responses = await asyncio.gather(
                *(
                    search_peer(address, client)
                    for address in addresses
                )
            )

        # 5. Fusionner les résultats par topic.
        merged: dict[str, dict] = {}
        errors: list[dict] = []

        for found, failures in responses:
            errors.extend(failures)

            for result in found:
                key = result["topic"].casefold()

                if key not in merged:
                    merged[key] = {
                        "peer": result["peer"],
                        "topic": result["topic"],
                        "items": {},
                        "sources": [],
                        "score": result["score"],
                    }

                target = merged[key]

                target["score"] = max(
                    target["score"],
                    result["score"],
                )

                # Conserver tous les serveurs sources.
                if result["peer"] not in target["sources"]:
                    target["sources"].append(result["peer"])

                # Fusionner les items et leurs URL.
                for item_name, urls in result["items"].items():
                    existing = target["items"].setdefault(
                        item_name,
                        [],
                    )

                    for url in urls:
                        if url not in existing:
                            existing.append(url)

        # 6. Classer les résultats par pertinence.
        results = sorted(
            merged.values(),
            key=lambda result: (
                -result["score"],
                result["topic"].casefold(),
            ),
        )

        return {
            "results": results,
            "errors": errors,
            "servers_checked": len(addresses),
        }

    # =========================================================
    # SYNCHRONISATION — AVEC ENREGISTREMENT
    # =========================================================

    async def synchronize_peer(self, peer: Peer) -> SyncResult:
        """Réplique les ressources et l'annuaire d'un serveur."""

        address = self._get_approved_address(peer)

        report = SyncResult(peer_url=address)

        # 1. Récupérer les topics
        try:
            topics = await self.fetch_topics(peer)

        except (httpx.HTTPError, ValueError, TypeError) as error:
            report.errors.append(
                f"/ws/topics : {error}"
            )
            topics = []

        # 2. Récupérer et fusionner les ressources
        for topic in topics:
            try:
                content = await self.fetch_topic(peer, topic)

                previous = self.catalog.get_topic(topic)

                report.urls_added += (
                    self.catalog.merge_remote_content(
                        topic,
                        content,
                    )
                )

                if previous is None:
                    report.topics_added += 1

            except (httpx.HTTPError, ValueError, TypeError) as error:
                report.errors.append(
                    f"/ws/topic/{topic} : {error}"
                )

        # 3. Découvrir de nouveaux serveurs
        try:
            directory = await self.fetch_directory(peer)

            report.peers_discovered = (
                self.peers.merge_directory(directory)
            )

        except (httpx.HTTPError, ValueError, TypeError) as error:
            report.errors.append(
                f"/ws/annuaire : {error}"
            )

        report.success = not report.errors

        return report

    async def synchronize(self) -> list[SyncResult]:
        """Synchronise les serveurs approuvés en parallèle."""

        addresses = self.peers.get_peer_urls(
            approved_only=True
        )

        semaphore = asyncio.Semaphore(
            self.config.max_concurrent_requests
        )

        async def run(address: str) -> SyncResult:
            async with semaphore:
                try:
                    peer = Peer(
                        url=HttpUrl(address),
                        approved=True,
                    )

                    return await self.synchronize_peer(peer)

                except Exception as error:
                    return SyncResult(
                        peer_url=address,
                        success=False,
                        errors=[str(error)],
                    )

        return list(
            await asyncio.gather(
                *(run(address) for address in addresses)
            )
        )
