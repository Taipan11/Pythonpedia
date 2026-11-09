
"""Pages HTML publiques de Pythonpédia."""

from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import (
    get_catalog_service,
    get_sync_service,
)
from app.services.catalog_service import CatalogService
from app.services.sync_service import SyncService

router = APIRouter(
    tags=["Pages"],
)

BASE_DIR = Path(__file__).resolve().parents[1]

templates = Jinja2Templates(
    directory=BASE_DIR / "templates",
)

CatalogDep = Annotated[
    CatalogService,
    Depends(get_catalog_service),
]

SyncDep = Annotated[
    SyncService,
    Depends(get_sync_service),
]

@router.get("/topics", response_class=HTMLResponse)
def topics_page(
    request: Request,
    catalog: CatalogDep,
):
    """Affiche les topics disponibles."""

    return templates.TemplateResponse(
        request=request,
        name="topics.html",
        context={
            "topics": catalog.get_topics(),
        },
    )


@router.get("/topics/{topic_name}", response_class=HTMLResponse)
def topic_page(
    topic_name: str,
    request: Request,
    catalog: CatalogDep,
):
    """Affiche les ressources d'un topic."""

    topic = catalog.get_topic(topic_name)

    if topic is None:
        raise HTTPException(
            status_code=404,
            detail="Topic introuvable",
        )

    return templates.TemplateResponse(
        request=request,
        name="topic_detail.html",
        context={
            "topic": topic,
        },
    )






@router.get("/search", response_class=HTMLResponse)
async def search_page(
    request: Request,
    catalog: CatalogDep,
    sync: SyncDep,
    q: str = Query(default="", max_length=100),
    scope: Literal["local", "network"] = "local",
):
    """Recherche locale ou étendue aux serveurs approuvés."""

    query = q.strip()

    local_results = (
        catalog.search_topics(query) if query else []
    )

    network_results = {
        "results": [],
        "errors": [],
        "servers_checked": 0,
    }

    if query and scope == "network":
        network_results = await sync.search_network(query)

    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "query": query,
            "scope": scope,
            "local_results": local_results,
            "remote_results": network_results["results"],
            "network_errors": network_results["errors"],
            "servers_checked": network_results["servers_checked"],
        },
    )

@router.get(
    "/admin/network",
    response_class=HTMLResponse,
)
def network_admin_page(request: Request):
    """Affiche l'interface d'administration du réseau."""

    return templates.TemplateResponse(
        request=request,
        name="admin_network.html",
        context={},
    )