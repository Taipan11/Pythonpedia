from pydantic import BaseModel, Field, HttpUrl, field_validator


class Item(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    urls: list[str] = Field(default_factory=list)

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, urls: list[str]) -> list[str]:
        validated = []

        for url in urls:
            parsed = HttpUrl(url)
            validated.append(str(parsed))

        return list(dict.fromkeys(validated))


class Topic(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    items: list[Item] = Field(default_factory=list)