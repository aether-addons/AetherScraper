from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .config import GlobalConfig, SearchOptions
from .kodi.settings import KodiSettings
from .loader import load_providers
from .manager import ScraperManager
from .models import SourceResult
from .torrent import parse_size_candidates

_PROVIDER_FOLDER_ALIASES: dict[str, set[str]] = {
    "torrent": {"torrent", "torrents"},
    "direct": {"direct", "directs", "hoster", "hosters", "hosts"},
    "hoster": {"direct", "directs", "hoster", "hosters", "hosts"},
    "generic": {"generic", "generics"},
}
_MAX_UMBRELLA_SIZE_BYTES = 50 * 1024**4


@dataclass(frozen=True)
class ExternalProviderSummary:
    id: str
    name: str
    provider_type: str
    priority: int
    pack_capable: bool
    has_movies: bool
    has_episodes: bool
    enabled: bool
    folders: tuple[str, ...] = ()


def _provider_summaries(
    providers: Iterable[Any] | None = None,
) -> list[ExternalProviderSummary]:
    if providers is None:
        providers, _ = load_providers(settings=KodiSettings())
    summaries = []
    for provider in providers:
        config = provider.config
        summaries.append(
            ExternalProviderSummary(
                id=config.id,
                name=config.name,
                provider_type=config.provider_type,
                priority=config.priority,
                pack_capable=config.pack_capable,
                has_movies=config.has_movies,
                has_episodes=config.has_episodes,
                enabled=provider.is_enabled(),
                folders=tuple(sorted(_folders_for_provider_type(config.provider_type))),
            )
        )
    return sorted(summaries, key=lambda item: item.priority)


def external_provider_summaries() -> list[ExternalProviderSummary]:
    """Return provider metadata for external consumers."""

    return _provider_summaries()


def torrent_provider_summaries() -> list[ExternalProviderSummary]:
    return [
        item
        for item in external_provider_summaries()
        if item.provider_type == "torrent"
    ]


def hoster_provider_summaries() -> list[ExternalProviderSummary]:
    return [
        item
        for item in external_provider_summaries()
        if item.provider_type in {"direct", "hoster"}
    ]


def pack_capable_provider_summaries() -> list[ExternalProviderSummary]:
    return [item for item in external_provider_summaries() if item.pack_capable]


def sources(specified_folders=None, ret_all: bool = False):
    """Magneto/Umbrella/FenLight-style external-provider entrypoint.

    External consumers import ``aetherscraper`` and expect a list of
    ``(provider_id, source_class)`` tuples. ``specified_folders=['torrents']`` is
    used by FenLight. ``ret_all=True`` is used by Umbrella to show disabled
    providers during provider selection.
    """

    summaries = _filter_summaries_by_folders(
        external_provider_summaries(), specified_folders
    )
    if not ret_all:
        summaries = [item for item in summaries if item.enabled]
    return [(item.id, _adapter_class(item)) for item in summaries]


class UmbrellaSourceAdapter:
    """Umbrella-compatible source class backed by ``ScraperManager``."""

    provider_id = "aetherscraper"
    provider_name = "AetherScraper"
    priority = 100
    pack_capable = True
    hasMovies = True
    hasEpisodes = True
    language = ["en"]
    provider_ids: tuple[str, ...] = ()
    provider_folders: tuple[str, ...] = ("torrents", "torrent")

    def __init__(
        self,
        manager_factory: Callable[[], Any] | None = None,
        options_factory: Callable[[], SearchOptions] | None = None,
    ) -> None:
        self._manager_factory = manager_factory or _default_manager
        self._options_factory = options_factory or _default_options

    def sources(
        self, data: Mapping[str, Any] | None, hostDict=None
    ) -> list[dict[str, Any]]:
        if not data:
            return []
        manager = self._manager_factory()
        options = _options_for_adapter(
            _options_with_host_dict(self._options_factory(), hostDict),
            self.provider_ids,
            data,
        )
        if _is_episode_payload(data):
            results = manager.search_episode(
                _episode_title(data),
                season=_int_value(data.get("season"), 0),
                episode=_int_value(data.get("episode"), 0),
                year=_int_or_none(data.get("year")),
                imdb_id=_str_or_none(data.get("imdb") or data.get("imdb_id")),
                tmdb_id=_str_or_none(data.get("tmdb") or data.get("tmdb_id")),
                aliases=_payload_aliases(data),
                host_dict=hostDict,
                options=options,
            )
        else:
            results = manager.search_movie(
                str(data.get("title") or data.get("name") or ""),
                year=_int_or_none(data.get("year")),
                imdb_id=_str_or_none(data.get("imdb") or data.get("imdb_id")),
                tmdb_id=_str_or_none(data.get("tmdb") or data.get("tmdb_id")),
                aliases=_payload_aliases(data),
                host_dict=hostDict,
                options=options,
            )
        return [_source_to_umbrella(result) for result in results]

    def sources_packs(
        self,
        data: Mapping[str, Any] | None,
        hostDict=None,
        search_series: bool = False,
        total_seasons: int | None = None,
        bypass_filter: bool = False,
    ) -> list[dict[str, Any]]:
        del bypass_filter
        if not data:
            return []
        manager = self._manager_factory()
        options = _options_for_adapter(
            _options_with_host_dict(self._options_factory(), hostDict),
            self.provider_ids,
            data,
        )
        title = _episode_title(data)
        total_seasons = total_seasons or _int_or_none(data.get("total_seasons"))
        if search_series or _bool_value(data.get("search_series")):
            results = manager.search_show_pack(
                title,
                total_seasons=total_seasons,
                year=_int_or_none(data.get("year")),
                imdb_id=_str_or_none(data.get("imdb") or data.get("imdb_id")),
                tmdb_id=_str_or_none(data.get("tmdb") or data.get("tmdb_id")),
                aliases=_payload_aliases(data),
                host_dict=hostDict,
                options=options,
            )
        else:
            results = manager.search_season_pack(
                title,
                season=_int_value(data.get("season"), 0),
                year=_int_or_none(data.get("year")),
                imdb_id=_str_or_none(data.get("imdb") or data.get("imdb_id")),
                tmdb_id=_str_or_none(data.get("tmdb") or data.get("tmdb_id")),
                aliases=_payload_aliases(data),
                host_dict=hostDict,
                options=options,
            )
        return [_source_to_umbrella(result, pack=True) for result in results]


def _adapter_class(summary: ExternalProviderSummary) -> type[UmbrellaSourceAdapter]:
    attrs = {
        "provider_id": summary.id,
        "provider_name": summary.name,
        "priority": summary.priority,
        "pack_capable": summary.pack_capable,
        "hasMovies": summary.has_movies,
        "hasEpisodes": summary.has_episodes,
        "language": ["en"],
        "provider_ids": (summary.id,),
        "provider_folders": summary.folders,
        "__module__": __name__,
    }
    name = "TjkExternal_" + "".join(
        char if char.isalnum() else "_" for char in summary.id
    )
    return type(name, (UmbrellaSourceAdapter,), attrs)


def _default_manager() -> ScraperManager:
    settings = KodiSettings()
    providers, _ = load_providers(settings=settings)
    return ScraperManager(
        config=GlobalConfig.from_kodi_settings(settings), providers=providers
    )


def _default_options() -> SearchOptions:
    return GlobalConfig.from_kodi_settings(KodiSettings()).to_search_options()


def _options_with_host_dict(options: SearchOptions, host_dict: Any) -> SearchOptions:
    if not host_dict:
        return options
    extra = dict(options.extra)
    extra["host_dict"] = host_dict
    return _replace_options(options, extra=extra)


def _options_for_adapter(
    options: SearchOptions, provider_ids: Iterable[str], data: Mapping[str, Any]
) -> SearchOptions:
    ids = [item for item in provider_ids if item]
    extra = dict(options.extra)
    if data.get("debrid_service"):
        extra["debrid_service"] = str(data.get("debrid_service"))
    if data.get("debrid_token"):
        extra["debrid_token"] = str(data.get("debrid_token"))
    if not ids and extra == options.extra:
        return options
    return _replace_options(
        options, provider_ids=ids or list(options.provider_ids), extra=extra
    )


def _replace_options(
    options: SearchOptions,
    *,
    provider_ids: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> SearchOptions:
    return SearchOptions(
        timeout=options.timeout,
        max_results=options.max_results,
        min_quality=options.min_quality,
        languages=list(options.languages),
        include_disabled=options.include_disabled,
        provider_ids=list(
            options.provider_ids if provider_ids is None else provider_ids
        ),
        allow_hevc=options.allow_hevc,
        allow_av1=options.allow_av1,
        allow_dolby_vision=options.allow_dolby_vision,
        allow_hdr=options.allow_hdr,
        allow_foreign_audio=options.allow_foreign_audio,
        undesirable_keywords=list(options.undesirable_keywords),
        use_default_undesirables=options.use_default_undesirables,
        extra=dict(options.extra if extra is None else extra),
    )


def _source_to_umbrella(result: SourceResult, pack: bool = False) -> dict[str, Any]:
    source = _source_kind(result)
    item: dict[str, Any] = {
        "provider": result.provider,
        "source": source,
        "name": result.title,
        "name_info": result.title,
        "quality": _umbrella_quality(result.quality),
        "language": result.language or "en",
        "url": result.url,
        "info": _info_label(result),
        "direct": bool(result.direct),
        "debridonly": source == "torrent",
        "size": _source_size_gb(result),
    }
    info_hash = result.metadata.get("info_hash") or result.metadata.get("hash")
    if info_hash:
        item["hash"] = info_hash
    if pack:
        item["package"] = result.metadata.get("package") or "season"
        for key in ("episode_start", "episode_end", "last_season"):
            value = result.metadata.get(key)
            if value is not None:
                item[key] = _int_value(value, value)
        if "last_season" in item and not result.metadata.get("package"):
            item["package"] = "show"
    return item


def _source_kind(result: SourceResult) -> str:
    url = result.url.lower()
    provider_type = result.metadata.get("provider_type", "")
    if url.startswith("magnet:") or provider_type == "torrent":
        return "torrent"
    if result.direct:
        return "direct"
    return result.provider


def _umbrella_quality(quality: str | None) -> str:
    quality = (quality or "").upper()
    if quality in {"4K", "2160P", "UHD"}:
        return "4K"
    if quality in {"1080P", "1080"}:
        return "1080p"
    if quality in {"720P", "720"}:
        return "720p"
    if quality in {"SCR", "CAM", "SD"}:
        return quality
    return "SD"


def _info_label(result: SourceResult) -> str:
    parts = []
    size = _source_size_bytes(result)
    if size:
        parts.append(f"{_size_gb(size):.2f} GB")
    codec = result.metadata.get("codec")
    hdr = result.metadata.get("hdr")
    if codec:
        parts.append(codec)
    if hdr:
        parts.append(hdr)
    return " | ".join(parts)


def _source_size_bytes(result: SourceResult) -> int | None:
    return parse_size_candidates(
        result.size,
        result.metadata.get("size_bytes"),
        result.metadata.get("filesize"),
        result.metadata.get("file_size"),
        result.metadata.get("size"),
        result.metadata.get("size_label"),
        result.title,
    )


def _source_size_gb(result: SourceResult) -> float:
    return _size_gb(_source_size_bytes(result))


def _size_gb(size: int | None) -> float:
    if not size or size < 0 or size > _MAX_UMBRELLA_SIZE_BYTES:
        return 0.0
    return round(size / 1024 / 1024 / 1024, 3)


def _filter_summaries_by_folders(
    summaries: Iterable[ExternalProviderSummary], specified_folders: Any
) -> list[ExternalProviderSummary]:
    requested = _folder_names(specified_folders)
    if not requested:
        return list(summaries)
    return [
        summary
        for summary in summaries
        if requested.intersection(_folders_for_provider_type(summary.provider_type))
    ]


def _folder_names(value: Any) -> set[str]:
    if value in (None, ""):
        return set()
    values = value if isinstance(value, (list, tuple, set)) else [value]
    return {str(item).strip().lower() for item in values if str(item).strip()}


def _folders_for_provider_type(provider_type: str) -> set[str]:
    key = (provider_type or "generic").strip().lower()
    return set(_PROVIDER_FOLDER_ALIASES.get(key, {key}))


def _is_episode_payload(data: Mapping[str, Any]) -> bool:
    return bool(data.get("tvshowtitle") or data.get("season") or data.get("episode"))


def _episode_title(data: Mapping[str, Any]) -> str:
    return str(
        data.get("tvshowtitle") or data.get("show_title") or data.get("title") or ""
    )


def _payload_aliases(data: Mapping[str, Any]) -> list[str]:
    aliases = []
    aliases.extend(_aliases(data.get("aliases")))
    aliases.extend(_aliases(data.get("alias")))
    aliases.extend(_aliases(data.get("alternate_titles")))
    return list(dict.fromkeys(item for item in aliases if item))


def _aliases(value: Any) -> list[str]:
    aliases = []
    if not value:
        return aliases
    for item in value if isinstance(value, list) else [value]:
        if isinstance(item, Mapping):
            title = item.get("title") or item.get("name")
            if title:
                aliases.append(str(title))
        elif item:
            aliases.append(str(item))
    return aliases


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _int_value(value: Any, default: Any) -> Any:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _int_or_none(value: Any) -> int | None:
    parsed = _int_value(value, None)
    return parsed if isinstance(parsed, int) else None


def _str_or_none(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)
