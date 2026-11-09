from pydantic import BaseModel, Field, HttpUrl


class Peer(BaseModel):
    """Serveur participant à Pythonpédia."""

    url: HttpUrl
    name: str | None = None
    approved: bool = False


class PeerResponse(BaseModel):
    """Résultat d'une communication réseau."""

    peer: Peer
    success: bool
    status_code: int | None = None
    error: str | None = None


class NetworkConfig(BaseModel):
    """Configuration réseau."""

    timeout: float = Field(default=5.0, gt=0, le=30)
    max_concurrent_requests: int = Field(default=10, ge=1, le=50)