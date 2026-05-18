from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SearchQuery:
    title: str
    media_type: str = "movie"  # movie, episode, channel, clip, other
    year: int | None = None
    season: int | None = None
    episode: int | None = None
    imdb_id: str | None = None
    tmdb_id: str | None = None
    aliases: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceResult:
    provider: str
    title: str
    url: str
    quality: str = "unknown"
    media_type: str = "unknown"
    size: int | None = None
    language: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    score: float = 0.0
    direct: bool = False
    metadata: dict[str, str] = field(default_factory=dict)
