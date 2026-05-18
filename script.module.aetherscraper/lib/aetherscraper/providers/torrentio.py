from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

from aetherscraper.config import ProviderConfig
from aetherscraper.models import SourceResult
from aetherscraper.provider import BaseProvider
from aetherscraper.torrent import build_magnet, normalize_torrent_item, torrent_to_source

DEFAULT_TORRENTIO_BASE_URL = "https://torrentio.strem.fun"
_SEEDERS_RE = re.compile(
    r"(?:👤\s*|seeders?[:\s]+|seeds?[:\s]+)(?P<count>\d+)", re.IGNORECASE
)
_QUALITY_RE = re.compile(r"\b(2160p|4k|1080p|720p|480p|360p)\b", re.IGNORECASE)


class TorrentioProvider(BaseProvider):
    """Torrentio public Stremio-addon stream provider.

    Required settings: optional base URL/config path; provider is disabled by default.
    Capabilities: movie and episode torrents only; no pack support.
    Timeout: provider timeout setting or per-call override.
    Auth/API key: none.
    Parser assumptions: Stremio `stream/{type}/{id}.json` response with `streams`.
    Safe use: uses public JSON stream endpoint only; no anti-bot/challenge bypass.
    """

    config = ProviderConfig(
        id="torrentio",
        name="Torrentio",
        enabled=False,
        priority=115,
        timeout=10,
        retries=1,
        provider_type="torrent",
        pack_capable=False,
        has_movies=True,
        has_episodes=True,
        media_types=["movie", "episode"],
        base_url=DEFAULT_TORRENTIO_BASE_URL,
    )

    def __init__(self, config=None, settings=None):
        super().__init__(config=config, settings=settings)
        self.base_url = self._setting("base_url", self.config.base_url).rstrip("/")
        self.config_path = self._setting("config_path", "").strip().strip("/")

    def search(self, query, options):
        if query.media_type not in {"movie", "episode"} or not query.imdb_id:
            return []
        stream_id = _stream_id(query)
        if not stream_id:
            return []
        media_type = "movie" if query.media_type == "movie" else "series"
        data = self.http_client(options).get_json(
            self._stream_url(media_type, stream_id),
            headers={"Accept": "application/json"},
        )
        return normalize_torrentio_results(data, provider_id=self.id)

    def _stream_url(self, media_type: str, stream_id: str) -> str:
        parts = [self.base_url]
        if self.config_path:
            parts.append(quote(self.config_path, safe="=|,:;"))
        parts.extend(["stream", media_type, f"{quote(stream_id, safe=':')}.json"])
        return "/".join(parts)

    def _setting(self, name: str, default: str = "") -> str:
        if self.settings is None:
            return default
        return self.settings.get_string(f"provider.{self.id}.{name}", default)


def normalize_torrentio_results(
    data: Any, provider_id: str = "torrentio"
) -> list[SourceResult]:
    results: list[SourceResult] = []
    for stream in _streams(data):
        if not isinstance(stream, dict):
            continue
        info_hash = _optional_str(stream.get("infoHash") or stream.get("info_hash"))
        url = _optional_str(stream.get("url"))
        if not info_hash and not url:
            continue
        title = _stream_title(stream)
        trackers = _trackers(stream.get("sources"))
        magnet = build_magnet(info_hash, title, trackers) if info_hash else ""
        item = normalize_torrent_item(
            {
                "title": title,
                "magnet": magnet,
                "torrent_url": "" if magnet else url,
                "info_hash": info_hash,
                "quality": _quality(stream, title),
                "size": _size_text(stream, title),
                "seeders": _seeders(stream, title),
                "language": stream.get("language") or stream.get("lang"),
                "metadata": {
                    "source": "torrentio",
                    "stream_name": stream.get("name"),
                    "file_idx": stream.get("fileIdx"),
                    "binge_group": _behavior_hint(stream, "bingeGroup"),
                },
            }
        )
        results.append(torrent_to_source(provider_id, item))
    return results


def _stream_id(query) -> str:
    imdb_id = str(query.imdb_id or "").strip()
    if query.media_type == "movie":
        return imdb_id
    if query.season is None or query.episode is None:
        return ""
    return f"{imdb_id}:{int(query.season)}:{int(query.episode)}"


def _streams(data: Any) -> list[Any]:
    if not isinstance(data, dict):
        return []
    streams = data.get("streams")
    return streams if isinstance(streams, list) else []


def _stream_title(stream: dict[str, Any]) -> str:
    behavior = stream.get("behaviorHints")
    filename = behavior.get("filename") if isinstance(behavior, dict) else ""
    for value in (filename, stream.get("title"), stream.get("name"), stream.get("url")):
        text = _optional_str(value)
        if text:
            return text.replace("\n", " ").strip()
    return "Torrentio stream"


def _quality(stream: dict[str, Any], title: str) -> str:
    value = _optional_str(stream.get("quality") or stream.get("resolution"))
    if value:
        return value
    match = _QUALITY_RE.search(_searchable_text(stream, title))
    return match.group(1) if match else "unknown"


def _size_text(stream: dict[str, Any], title: str) -> Any:
    for key in ("size", "size_bytes", "filesize"):
        if stream.get(key) not in (None, ""):
            return stream.get(key)
    return _searchable_text(stream, title)


def _seeders(stream: dict[str, Any], title: str) -> Any:
    for key in ("seeders", "seeds"):
        if stream.get(key) not in (None, ""):
            return stream.get(key)
    match = _SEEDERS_RE.search(_searchable_text(stream, title))
    return match.group("count") if match else None


def _searchable_text(stream: dict[str, Any], title: str) -> str:
    return " ".join(
        text
        for text in (
            title,
            _optional_str(stream.get("title")),
            _optional_str(stream.get("name")),
            _behavior_hint(stream, "filename"),
        )
        if text
    )


def _trackers(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    trackers = []
    for item in value:
        text = _optional_str(item)
        if text.startswith("tracker:"):
            text = text[8:]
        if text.startswith(("udp://", "http://", "https://")):
            trackers.append(text)
    return trackers


def _behavior_hint(stream: dict[str, Any], key: str) -> str:
    behavior = stream.get("behaviorHints")
    if not isinstance(behavior, dict):
        return ""
    return _optional_str(behavior.get(key))


def _optional_str(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value)
