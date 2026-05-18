from __future__ import annotations

from aetherscraper.config import ProviderConfig
from aetherscraper.provider import BaseProvider
from aetherscraper.torrent import torrent_to_source
from aetherscraper.torznab import build_torznab_params, parse_torznab


class TorznabProvider(BaseProvider):
    """Generic authorized Torznab/RSS provider.

    Required settings: base URL and optional API key owned by user.
    Capabilities: movie, episode, season/show packs when indexer supports them.
    Timeout: provider timeout setting or per-call override.
    Safe use: no challenge bypass; API key is read from settings/config and never logged.
    """

    config = ProviderConfig(
        id="torznab",
        name="Generic Torznab",
        enabled=False,
        priority=50,
        timeout=10,
        retries=1,
        provider_type="torrent",
        pack_capable=True,
        has_movies=True,
        has_episodes=True,
        media_types=["movie", "episode", "season", "show"],
    )

    def __init__(self, config=None, settings=None):
        super().__init__(config=config, settings=settings)
        self.base_url = self._setting("base_url", self.config.base_url)
        self.api_key = self._setting("api_key", self.config.params.get("api_key", ""))
        self.categories = _int_list(
            self._setting("categories", self.config.params.get("categories", ""))
        )

    def search(self, query, options):
        if not self.base_url:
            return []
        params = build_torznab_params(query, self.api_key, self.categories)
        xml_text = self.http_client(options).get_text(self.base_url, params=params)
        return [
            torrent_to_source(self.id, item)
            for item in parse_torznab(xml_text, self.base_url)
        ]

    def _setting(self, name: str, default: str = "") -> str:
        if self.settings is None:
            return default
        return self.settings.get_string(f"provider.{self.id}.{name}", default)


class ProwlarrProvider(TorznabProvider):
    """Prowlarr Torznab provider for user-owned Prowlarr indexers.

    Required settings: Prowlarr Torznab endpoint URL or root URL plus indexer ID;
    optional API key and categories.
    Capabilities: movie, episode, season/show packs when selected indexer supports them.
    Timeout: provider timeout setting or per-call override.
    Auth/API key: optional user-owned Prowlarr API key from Kodi settings.
    Parser assumptions: Torznab-compatible RSS from Prowlarr indexer endpoint.
    Safe use: no challenge, CAPTCHA, Cloudflare, or access-control bypass.
    """

    config = ProviderConfig(
        id="prowlarr",
        name="Prowlarr",
        enabled=False,
        priority=40,
        timeout=10,
        retries=1,
        provider_type="torrent",
        pack_capable=True,
        has_movies=True,
        has_episodes=True,
        media_types=["movie", "episode", "season", "show"],
    )

    def __init__(self, config=None, settings=None):
        super().__init__(config=config, settings=settings)
        self.indexer_id = self._setting("indexer_id", "").strip().strip("/")
        if (
            self.base_url
            and self.indexer_id
            and not self.base_url.rstrip("/").endswith("/api")
        ):
            self.base_url = f"{self.base_url.rstrip('/')}/{self.indexer_id}/api"


class TorBoxTorznabProvider(TorznabProvider):
    """TorBox Torznab provider for user-owned TorBox API access."""

    config = ProviderConfig(
        id="torbox_torznab",
        name="TorBox Torznab",
        enabled=False,
        priority=45,
        timeout=10,
        retries=1,
        provider_type="torrent",
        pack_capable=True,
        has_movies=True,
        has_episodes=True,
        media_types=["movie", "episode", "season", "show"],
    )


def _int_list(value) -> list[int]:
    if isinstance(value, list):
        raw = value
    else:
        raw = str(value or "").split(",")
    items = []
    for item in raw:
        try:
            items.append(int(str(item).strip()))
        except ValueError:
            continue
    return items
