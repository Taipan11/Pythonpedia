
"""Administration locale des ressources Pythonpédia."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import get_catalog_service
from app.models.topic import Topic, Item
from app.security import require_admin
from app.services.catalog_service import CatalogService


router = APIRouter(
    prefix="/admin",
    tags=["Administration"],
    dependencies=[Depends(require_admin)],
)

CatalogDep = Annotated[
    CatalogService,
    Depends(get_catalog_service),
]


@router.post(
    "/topics",
    status_code=status.HTTP_201_CREATED,
)
def create_topic(
    topic: Topic,
    catalog: CatalogDep,
):
    """Ajoute un topic et ses ressources."""

    added = catalog.add_topic(topic)

    return {
        "urls_added": added,
    }


@router.post("/topics/{topic_name}/items")
def add_item(
    topic_name: str,
    item: Item,
    catalog: CatalogDep,
):
    """Ajoute un item ou enrichit un item existant."""

    added = catalog.add_item(
        topic_name,
        item,
    )

    return {
        "urls_added": added,
    }
