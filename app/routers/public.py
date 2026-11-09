
"""API publique de Pythonpédia."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import (
    get_catalog_service,
    get_peer_service,
)

from app.models.responses import (
    TopicsResponse,
    TopicContentResponse,
    DirectoryResponse,
)

from app.services.catalog_service import CatalogService
from app.services.peer_service import PeerService


router = APIRouter(
    prefix="/ws",
    tags=["Public API"],
)

CatalogDep = Annotated[
    CatalogService,
    Depends(get_catalog_service),
]

PeerDep = Annotated[
    PeerService,
    Depends(get_peer_service),
]


@router.get("/topics", response_model=TopicsResponse)
def get_topics(catalog: CatalogDep) -> TopicsResponse:
    return catalog.get_topics()


@router.get(
    "/topic/{topic_name}",
    response_model=TopicContentResponse,
)
def get_topic(
    topic_name: str,
    catalog: CatalogDep,
) -> TopicContentResponse:

    content = catalog.get_topic_public(topic_name)

    if content is None:
        raise HTTPException(
            status_code=404,
            detail="Topic introuvable",
        )

    return content


@router.get("/annuaire", response_model=DirectoryResponse)
def get_annuaire(peers: PeerDep) -> DirectoryResponse:
    return peers.get_peer_urls()

