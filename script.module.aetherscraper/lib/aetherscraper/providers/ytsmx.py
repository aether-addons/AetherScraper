from __future__ import annotations

from typing import Any

from aetherscraper.config import ProviderConfig
from aetherscraper.models import SourceResult
from aetherscraper.provider import BaseProvider
from aetherscraper.torrent import build_magnet, normalize_torrent_item, torrent_to_source

DEFAULT_YTSMX_API_URL = "https://yts.mx/api/v2/list_movies.json"
YTSMX_TRACKERS = [
    "udp://open.demonii.com:1337/announce",
    "udp://tracker.openbittorrent.com:80",
    "udp://tracker.coppersurfer.tk:6969",
    "udp://glotorrents.pw:6969/announce",
    "udp://tracker.opentrackr.org:1337/announce",
]


class YtsMxProvider(BaseProvider):
    """YTS.mx public movie API provider.

    Required settings: optional API URL override; provider is disabled by default.
    Capabilities: movie torrents only; no episode or pack support.
    Timeout: provider timeout setting or per-call override.
    Auth/API key: none.
    Parser assumptions: YTS `list_movies.json` response with `data.movies[].torrents`.
    Safe use: uses documented JSON API only; no anti-bot/challenge bypass.
    """

    config = ProviderConfig(
        id="ytsmx",
        name="YTS.mx",
        enabled=False,
        priority=120,
        timeout=10,
        retries=1,
        provider_type="torrent",
        pack_capable=False,
        has_movies=True,
        has_episodes=False,
        media_types=["movie"],
        base_url=DEFAULT_YTSMX_API_URL,
    )

    def __init__(self, config=None, settings=None):
        super().__init__(config=config, settings=settings)
        self.api_url = self._setting("base_url", self.config.base_url)

    def search(self, query, options):
        if query.media_type != "movie" or not self.api_url:
            return []
        data = self.http_client(options).get_json(
            self.api_url,
            params=self._params(query, options),
            headers={"Accept": "application/json"},
        )
        return normalize_ytsmx_results(data, provider_id=self.id)

    def _params(self, query, options) -> dict[str, str]:
        limit = max(1, min(int(getattr(options, "max_results", 50) or 50), 50))
        return {
            "query_term": query.imdb_id or query.title,
            "limit": str(limit),
            "sort_by": "seeds",
            "order_by": "desc",
        }

    def _setting(self, name: str, default: str = "") -> str:
        if self.settings is None:
            return default
        return self.settings.get_string(f"provider.{self.id}.{name}", default)


def normalize_ytsmx_results(
    data: Any, provider_id: str = "ytsmx"
) -> list[SourceResult]:
    results: list[SourceResult] = []
    for movie in _movies(data):
        if not isinstance(movie, dict):
            continue
        movie_title = str(movie.get("title_long") or movie.get("title") or "").strip()
        if not movie_title:
            continue
        year = movie.get("year")
        language = _optional_str(movie.get("language"))
        imdb_code = _optional_str(movie.get("imdb_code"))
        for torrent in movie.get("torrents") or []:
            if not isinstance(torrent, dict):
                continue
            info_hash = _optional_str(torrent.get("hash"))
            if not info_hash:
                continue
            quality = _optional_str(torrent.get("quality")) or "unknown"
            release_type = _optional_str(torrent.get("type"))
            title = " ".join(
                part for part in (movie_title, quality, release_type) if part
            )
            magnet = build_magnet(info_hash, title or movie_title, YTSMX_TRACKERS)
            item = normalize_torrent_item(
                {
                    "title": title or movie_title,
                    "magnet": magnet,
                    "torrent_url": torrent.get("url"),
                    "info_hash": info_hash,
                    "quality": quality,
                    "size": torrent.get("size_bytes") or torrent.get("size"),
                    "seeders": torrent.get("seeds"),
                    "leechers": torrent.get("peers"),
                    "language": language,
                    "metadata": {
                        "provider_movie_id": movie.get("id"),
                        "imdb_code": imdb_code,
                        "year": year,
                        "type": release_type,
                        "source": "ytsmx",
                    },
                }
            )
            results.append(torrent_to_source(provider_id, item))
    return results


def _movies(data: Any) -> list[Any]:
    if not isinstance(data, dict):
        return []
    payload = data.get("data") if isinstance(data.get("data"), dict) else data
    movies = payload.get("movies") if isinstance(payload, dict) else None
    return movies if isinstance(movies, list) else []


def _optional_str(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value)
