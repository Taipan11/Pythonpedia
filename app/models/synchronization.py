from datetime import datetime, timezone

from pydantic import BaseModel, Field


class SyncResult(BaseModel):
    """Bilan d'une synchronisation avec un serveur."""

    peer_url: str
    success: bool = False

    topics_added: int = Field(default=0, ge=0)
    urls_added: int = Field(default=0, ge=0)
    peers_discovered: int = Field(default=0, ge=0)

    errors: list[str] = Field(default_factory=list)

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )