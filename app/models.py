from pydantic import BaseModel, Field, HttpUrl, RootModel, field_validator


class TopicNames(RootModel[list[str]]):
    @field_validator('root')
    @classmethod
    def validate_names(cls, names: list[str]) -> list[str]:
        if len(names) > 1000 or any(not n.strip() or len(n) > 120 for n in names):
            raise ValueError('Liste de topics invalide')
        return names


class TopicContent(RootModel[dict[str, list[HttpUrl]]]):
    @field_validator('root')
    @classmethod
    def validate_items(cls, items: dict[str, list[HttpUrl]]) -> dict[str, list[HttpUrl]]:
        if len(items) > 100 or any(not name.strip() or len(name) > 120 or len(urls) > 500 for name, urls in items.items()):
            raise ValueError('Contenu de topic invalide')
        return items


class PeerDirectory(RootModel[list[HttpUrl]]):
    @field_validator('root')
    @classmethod
    def validate_count(cls, peers: list[HttpUrl]) -> list[HttpUrl]:
        if len(peers) > 1000:
            raise ValueError('Annuaire trop grand')
        return peers


class SyncReport(BaseModel):
    peer: str
    topics_received: int = 0
    links_added: int = 0
    discovered_peers: int = 0
    errors: list[str] = Field(default_factory=list)
