"""Point d'entrée de l'application Pythonpédia."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.routers import public, admin, network, pages

from contextlib import asynccontextmanager

from app.config import get_settings
from app.data.seed import INITIAL_TOPICS
from app.dependencies import (
    get_catalog_repository,
    get_peer_repository,
)

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise le stockage au démarrage de Pythonpédia."""

    settings = get_settings()

    if settings.STORAGE_BACKEND == "sqlite":
        # Création automatique de la base et de ses tables.
        catalog = get_catalog_repository()
        get_peer_repository()

        # Insertion des topics initiaux sans doublons.
        for topic in INITIAL_TOPICS:
            catalog.add_topic(topic)

    yield

app = FastAPI(
    title="Pythonpédia",
    description="Encyclopédie distribuée de références Python",
    version="0.1.0",
    lifespan=lifespan
)


# API REST
app.include_router(public.router)
app.include_router(admin.router)
app.include_router(network.router)
app.include_router(pages.router)

# Fichiers statiques
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


# Templates HTML
templates = Jinja2Templates(
    directory=BASE_DIR / "templates",
)


@app.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def home(request: Request):
    """Page d'accueil et documentation publique."""

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )