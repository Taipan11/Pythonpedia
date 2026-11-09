"""Contrats des réponses publiques de Pythonpédia."""

from typing import TypeAlias

TopicsResponse: TypeAlias = list[str]

TopicContentResponse: TypeAlias = dict[str, list[str]]

DirectoryResponse: TypeAlias = list[str]