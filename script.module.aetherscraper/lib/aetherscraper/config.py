from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderConfig:
    id: str
    name: str
    enabled: bool = True
    priority: int = 100
    timeout: int = 10
    retries: int = 1
    provider_type: str = "generic"
    pack_capable: bool = False
    has_movies: bool = True
    has_episodes: bool = True
    media_types: list[str] = field(default_factory=lambda: ["movie", "episode"])
    base_url: str = ""
    user_agent: str = "AetherScraper/0.1"
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] = field(default_factory=dict)
    limits: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchOptions:
    timeout: int | None = None
    max_results: int = 50
    min_quality: str | None = None
    languages: list[str] = field(default_factory=list)
    include_disabled: bool = False
    provider_ids: list[str] = field(default_factory=list)
    allow_hevc: bool = True
    allow_av1: bool = True
    allow_dolby_vision: bool = True
    allow_hdr: bool = True
    allow_foreign_audio: bool = True
    undesirable_keywords: list[str] = field(default_factory=list)
    use_default_undesirables: bool = True
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GlobalConfig:
    concurrent: bool = False
    max_results: int = 100
    provider_timeout: int = 10
    provider_retries: int = 1
    scrape_timeout: int = 30
    debug_logging: bool = False
    fail_fast: bool = False
    allow_hevc: bool = True
    allow_av1: bool = True
    allow_dolby_vision: bool = True
    allow_hdr: bool = True
    allow_foreign_audio: bool = True
    languages: list[str] = field(default_factory=list)
    undesirable_keywords: list[str] = field(default_factory=list)
    use_default_undesirables: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def to_search_options(self) -> SearchOptions:
        return SearchOptions(
            max_results=self.max_results,
            allow_hevc=self.allow_hevc,
            allow_av1=self.allow_av1,
            allow_dolby_vision=self.allow_dolby_vision,
            allow_hdr=self.allow_hdr,
            allow_foreign_audio=self.allow_foreign_audio,
            languages=list(self.languages),
            undesirable_keywords=list(self.undesirable_keywords),
            use_default_undesirables=self.use_default_undesirables,
            extra=dict(self.extra),
        )

    @classmethod
    def from_kodi_settings(cls, settings=None):
        if settings is None:
            from .kodi.settings import KodiSettings

            settings = KodiSettings()
        snapshot = settings.snapshot()
        return cls(
            max_results=snapshot.max_results,
            provider_timeout=snapshot.provider_timeout,
            provider_retries=snapshot.provider_retries,
            scrape_timeout=snapshot.scrape_timeout,
            concurrent=snapshot.concurrent_scraping,
            debug_logging=snapshot.debug_logging,
            allow_hevc=not snapshot.filter_hevc,
            allow_av1=not snapshot.filter_av1,
            allow_dolby_vision=not snapshot.filter_dolby_vision,
            allow_hdr=not snapshot.filter_hdr,
            allow_foreign_audio=not snapshot.filter_foreign_audio,
            languages=list(snapshot.languages),
            undesirable_keywords=list(snapshot.undesirable_keywords),
            use_default_undesirables=snapshot.use_default_undesirables,
        )
