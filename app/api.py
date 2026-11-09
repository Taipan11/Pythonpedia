from fastapi import APIRouter, HTTPException
from .database import topics, topic_content, peer_urls

router = APIRouter(prefix='/ws', tags=['Public'])


@router.get('/topics', response_model=list[str])
def get_topics() -> list[str]:
    return topics()


@router.get('/topic/{topic}', response_model=dict[str, list[str]])
def get_topic(topic: str) -> dict[str, list[str]]:
    result = topic_content(topic)
    if result is None:
        raise HTTPException(status_code=404, detail='Topic inconnu')
    return result


@router.get('/annuaire', response_model=list[str])
def get_directory() -> list[str]:
    return peer_urls()
