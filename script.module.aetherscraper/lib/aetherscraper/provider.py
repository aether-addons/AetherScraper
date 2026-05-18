from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from .config import ProviderConfig, SearchOptions
from .kodi.settings import KodiSettings, provider_enabled_setting
from .models import SearchQuery, SourceResult


class BaseProvider(ABC):
    config = ProviderConfig(id="base", name="Base Provider", enabled=False)

    def __init__(
        self,
        config: ProviderConfig | None = None,
        settings: KodiSettings | None = None,
    ) -> None:
        if config is not None:
            self.config = config
        self.settings = settings

    @property
    def id(self):
        return self.config.id

    @property
    def name(self):
        return self.config.name

    def is_enabled(self):
        if self.settings is None:
            return self.config.enabled
        return self.settings.get_bool(
            provider_enabled_setting(self.id), self.config.enabled
        )

    def supports(self, query: SearchQuery):
        if not query.title:
            return False
        if query.media_type == "movie" and not self.config.has_movies:
            return False
        if query.media_type == "episode" and not self.config.has_episodes:
            return False
        if query.media_type in {"season", "show"} and not self.config.pack_capable:
            return False
        return (
            not self.config.media_types or query.media_type in self.config.media_types
        )

    def http_client(self, options: SearchOptions | None = None):
        from .http import HttpClient, options_from_provider

        return HttpClient(options_from_provider(self.config, options))

    @abstractmethod
    def search(
        self, query: SearchQuery, options: SearchOptions
    ) -> Iterable[SourceResult]:
        raise NotImplementedError
