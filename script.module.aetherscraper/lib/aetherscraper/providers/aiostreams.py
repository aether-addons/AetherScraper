from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from aetherscraper.config import ProviderConfig
from aetherscraper.models import SourceResult
from aetherscraper.provider import BaseProvider
from aetherscraper.torrent import (
    normalize_torrent_item,
    parse_size_candidates,
    torrent_to_source,
)


class AIOStreamsProvider(BaseProvider):
    """Authorized AIOStreams-style JSON provider.

    Required settings: instance URL and optional auth token/header supplied by user.
    Capabilities: movie, episode, season/show only if instance exposes matching data.
    Timeout: provider timeout setting or per-call override.
    Parser assumptions: JSON response is list-like or contains `streams`/`results`/`items`.
    Safe use: auth values are read from settings/config and never logged.
    """

    config = ProviderConfig(
        id="aiostreams",
        name="AIOStreams",
        enabled=False,
        priority=60,
        timeout=10,
        retries=1,
        provider_type="generic",
        pack_capable=True,
        has_movies=True,
        has_episodes=True,
        media_types=["movie", "episode", "season", "show"],
    )

    def __init__(self, config=None, settings=None):
        super().__init__(config=config, settings=settings)
        self.instance_url = self._setting("instance_url", self.config.base_url)
        self.auth_token = self._setting(
            "auth_token", self.config.params.get("auth_token", "")
        )
        self.auth_header = self._setting(
            "auth_header", self.config.params.get("auth_header", "Authorization")
        )

    def search(self, query, options):
        if not self.instance_url:
            return []
        headers = {}
        if self.auth_token:
            headers[self.auth_header or "Authorization"] = self.auth_token
        data = self.http_client(options).get_json(
            self._search_url(),
            params=self._params(query),
            headers=headers,
        )
        return normalize_aiostreams_results(self.id, data)

    def _search_url(self) -> str:
        return urljoin(self.instance_url.rstrip("/") + "/", "streams")

    def _params(self, query) -> dict[str, str]:
        params = {"type": query.media_type, "title": query.title}
        if query.year:
            params["year"] = str(query.year)
        if query.season is not None:
            params["season"] = str(query.season)
        if query.episode is not None:
            params["episode"] = str(query.episode)
        if query.imdb_id:
            params["imdb_id"] = query.imdb_id
        if query.tmdb_id:
            params["tmdb_id"] = query.tmdb_id
        return params

    def _setting(self, name: str, default: str = "") -> str:
        if self.settings is None:
            return default
        return self.settings.get_string(f"provider.{self.id}.{name}", default)


def normalize_aiostreams_results(provider_id: str, data: Any) -> list[SourceResult]:
    items = _items(data)
    results = []
    for item in items:
        if not isinstance(item, dict):
            continue
        torrent = normalize_torrent_item(item)
        if torrent.magnet or torrent.torrent_url or torrent.info_hash:
            results.append(torrent_to_source(provider_id, torrent))
            continue
        title = str(item.get("title") or item.get("name") or "")
        url = str(item.get("url") or item.get("link") or item.get("stream") or "")
        if not title or not url:
            continue
        results.append(
            SourceResult(
                provider=provider_id,
                title=title,
                url=url,
                quality=str(item.get("quality") or item.get("resolution") or "unknown"),
                media_type=str(item.get("type") or item.get("media_type") or "stream"),
                size=parse_size_candidates(
                    item.get("size_bytes"),
                    item.get("filesize"),
                    item.get("file_size"),
                    item.get("size"),
                    title,
                ),
                language=item.get("language") or item.get("lang"),
                headers=_string_dict(item.get("headers")),
                score=float(
                    _optional_int(item.get("seeders") or item.get("score")) or 0
                ),
                direct=bool(item.get("direct", True)),
                metadata=_string_dict(item.get("metadata")),
            )
        )
    return results


def _items(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in ("streams", "results", "items"):
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _string_dict(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items() if item is not None}
