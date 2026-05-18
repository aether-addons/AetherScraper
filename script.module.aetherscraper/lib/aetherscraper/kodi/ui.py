from __future__ import annotations

from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass, replace
from typing import (  # noqa: UP035 - Kodi Python may lack collections.abc generics
    Any,
    Callable,
    Mapping,
    Optional,
)
from urllib.parse import urlencode

from ..models import SourceResult
from ..torrent import bytes_to_size
from .settings import KodiSettings

_SECRET_HEADER_NAMES = {"authorization", "cookie", "x-api-key", "x-auth-token"}
_SAFE_PIPE_HEADER_NAMES = {
    "user-agent",
    "referer",
    "origin",
    "accept",
    "accept-language",
}

QUALITY_WEIGHTS: dict[str, int] = {
    "4k": 500,
    "2160p": 500,
    "1080p": 400,
    "720p": 300,
    "sd": 100,
    "scr": 25,
    "cam": 10,
    "unknown": 0,
}


@dataclass(frozen=True)
class KodiUiSettings:
    color_tags: bool = True
    color_4k: str = "gold"
    color_1080p: str = "deepskyblue"
    color_720p: str = "limegreen"
    color_cam: str = "red"
    color_scr: str = "orange"
    color_direct: str = "white"
    autoplay_policy: str = "score_quality_size"

    @classmethod
    def from_settings(cls, settings: KodiSettings | None = None) -> KodiUiSettings:
        settings = settings or KodiSettings()
        return cls(
            color_tags=settings.get_bool("ui_color_tags", True),
            color_4k=settings.get_string("ui_color_4k", "gold"),
            color_1080p=settings.get_string("ui_color_1080p", "deepskyblue"),
            color_720p=settings.get_string("ui_color_720p", "limegreen"),
            color_cam=settings.get_string("ui_color_cam", "red"),
            color_scr=settings.get_string("ui_color_scr", "orange"),
            color_direct=settings.get_string("ui_color_direct", "white"),
            autoplay_policy=settings.get_string(
                "ui_autoplay_policy", "score_quality_size"
            ),
        )


MetadataLookup = Callable[[SourceResult], Optional[Mapping[str, Any]]]  # noqa: UP007
PlaybackResolver = Callable[[SourceResult], Optional[SourceResult]]  # noqa: UP007


def quality_weight(quality: str | None) -> int:
    key = (quality or "unknown").strip().lower()
    return QUALITY_WEIGHTS.get(key, 0)


def source_rank_key(source: SourceResult) -> tuple[float, int, int, int]:
    return (
        float(source.score or 0),
        quality_weight(source.quality),
        int(source.size or 0),
        1 if source.direct else 0,
    )


def rank_autoplay_sources(
    sources: Iterable[SourceResult], policy: str = "score_quality_size"
) -> list[SourceResult]:
    items = list(sources)
    if policy == "quality_score_size":
        return sorted(
            items,
            key=lambda item: (
                quality_weight(item.quality),
                float(item.score or 0),
                int(item.size or 0),
                1 if item.direct else 0,
            ),
            reverse=True,
        )
    if policy == "size_quality_score":
        return sorted(
            items,
            key=lambda item: (
                int(item.size or 0),
                quality_weight(item.quality),
                float(item.score or 0),
                1 if item.direct else 0,
            ),
            reverse=True,
        )
    return sorted(items, key=source_rank_key, reverse=True)


def choose_autoplay_source(
    sources: Iterable[SourceResult], settings: KodiUiSettings | None = None
) -> SourceResult | None:
    settings = settings or KodiUiSettings()
    ranked = rank_autoplay_sources(sources, settings.autoplay_policy)
    return ranked[0] if ranked else None


def with_metadata_lookup(
    source: SourceResult, lookup: MetadataLookup | None = None
) -> SourceResult:
    """Return source with optional metadata overlay from consumer add-on.

    AetherScraper does not call TMDb/IMDb itself in Phase 13. Consumers may provide
    a lookup callable and own any API keys/cache policy.
    """

    if lookup is None:
        return source
    extra = lookup(source)
    if not extra:
        return source
    metadata = dict(source.metadata)
    metadata.update({str(key): str(value) for key, value in extra.items() if value})
    return replace(source, metadata=metadata)


def format_source_label(
    source: SourceResult, settings: KodiUiSettings | None = None
) -> str:
    settings = settings or KodiUiSettings()
    parts = [source.title]
    if source.quality and source.quality != "unknown":
        parts.append(source.quality)
    if source.size:
        parts.append(bytes_to_size(source.size))
    if source.provider:
        parts.append(source.provider)
    if source.language:
        parts.append(source.language)
    label = " | ".join(str(part) for part in parts if part)
    color = _source_color(source, settings)
    if settings.color_tags and color:
        return f"[COLOR {color}]{label}[/COLOR]"
    return label


def build_plugin_url(base_url: str, **query: str) -> str:
    if not query:
        return base_url
    return base_url + "?" + urlencode(query)


def build_source_plugin_url(
    base_url: str,
    source_id: str,
    route: str = "play",
    extra: Mapping[str, str] | None = None,
) -> str:
    params = {"route": route, "source_id": source_id}
    if extra:
        params.update(dict(extra))
    return build_plugin_url(base_url, **params)


def build_source_listitem(
    source: SourceResult,
    *,
    base_url: str = "",
    source_id: str = "0",
    settings: KodiUiSettings | None = None,
    xbmcgui_module: Any | None = None,
    metadata_lookup: MetadataLookup | None = None,
) -> tuple[str, Any, bool]:
    source = with_metadata_lookup(source, metadata_lookup)
    xbmcgui_module = xbmcgui_module or _xbmcgui()
    label = format_source_label(source, settings)
    path = build_source_plugin_url(base_url, source_id) if base_url else source.url
    item = xbmcgui_module.ListItem(label=label)
    if hasattr(item, "setProperty"):
        item.setProperty("IsPlayable", "true")
    _apply_video_info(item, source, label)
    return path, item, False


def build_source_directory_items(
    sources: Iterable[SourceResult],
    base_url: str,
    settings: KodiUiSettings | None = None,
    metadata_lookup: MetadataLookup | None = None,
) -> list[tuple[str, Any, bool]]:
    return [
        build_source_listitem(
            source,
            base_url=base_url,
            source_id=str(index),
            settings=settings,
            metadata_lookup=metadata_lookup,
        )
        for index, source in enumerate(sources)
    ]


def add_source_directory(
    handle: int,
    sources: Iterable[SourceResult],
    base_url: str,
    *,
    settings: KodiUiSettings | None = None,
    xbmcplugin_module: Any | None = None,
    metadata_lookup: MetadataLookup | None = None,
) -> bool:
    xbmcplugin_module = xbmcplugin_module or _xbmcplugin()
    if xbmcplugin_module is None:
        return False
    items = build_source_directory_items(
        sources,
        base_url,
        settings=settings,
        metadata_lookup=metadata_lookup,
    )
    if hasattr(xbmcplugin_module, "setContent"):
        xbmcplugin_module.setContent(handle, "videos")
    if hasattr(xbmcplugin_module, "addDirectoryItems"):
        xbmcplugin_module.addDirectoryItems(handle, items, totalItems=len(items))
    elif hasattr(xbmcplugin_module, "addDirectoryItem"):
        for url, item, is_folder in items:
            xbmcplugin_module.addDirectoryItem(handle, url, item, isFolder=is_folder)
    else:
        return False
    if hasattr(xbmcplugin_module, "endOfDirectory"):
        xbmcplugin_module.endOfDirectory(handle, succeeded=True, cacheToDisc=False)
    return True


def select_source(
    sources: Iterable[SourceResult],
    *,
    dialog: Any | None = None,
    settings: KodiUiSettings | None = None,
) -> SourceResult | None:
    items = list(sources)
    if not items:
        return None
    labels = [format_source_label(item, settings) for item in items]
    dialog = dialog or _dialog()
    if dialog is None or not hasattr(dialog, "select"):
        return items[0]
    index = dialog.select("Select source", labels)
    if index is None or index < 0 or index >= len(items):
        return None
    return items[index]


def kodi_stream_url(url: str, headers: Mapping[str, str] | None = None) -> str:
    safe_headers = {
        name: value
        for name, value in (headers or {}).items()
        if name.strip().lower() in _SAFE_PIPE_HEADER_NAMES
        and name.strip().lower() not in _SECRET_HEADER_NAMES
        and value
    }
    if not safe_headers:
        return url
    return url + "|" + urlencode(safe_headers)


def resolve_playback_source(
    source: SourceResult,
    resolver: PlaybackResolver | None = None,
) -> SourceResult | None:
    if source.direct and source.url:
        return source
    if resolver is None:
        return None
    resolved = resolver(source)
    if resolved is None or not resolved.url:
        return None
    return resolved


def build_resolved_listitem(
    source: SourceResult,
    *,
    xbmcgui_module: Any | None = None,
    metadata_lookup: MetadataLookup | None = None,
) -> Any:
    source = with_metadata_lookup(source, metadata_lookup)
    xbmcgui_module = xbmcgui_module or _xbmcgui()
    item = xbmcgui_module.ListItem(
        label=source.title,
        path=kodi_stream_url(source.url, source.headers),
    )
    _apply_video_info(item, source, source.title)
    return item


def resolve_to_kodi(
    handle: int,
    source: SourceResult,
    *,
    resolver: PlaybackResolver | None = None,
    xbmcplugin_module: Any | None = None,
    xbmcgui_module: Any | None = None,
    metadata_lookup: MetadataLookup | None = None,
) -> bool:
    xbmcplugin_module = xbmcplugin_module or _xbmcplugin()
    xbmcgui_module = xbmcgui_module or _xbmcgui()
    if xbmcplugin_module is None or not hasattr(xbmcplugin_module, "setResolvedUrl"):
        return False
    resolved = resolve_playback_source(source, resolver=resolver)
    if resolved is None:
        xbmcplugin_module.setResolvedUrl(handle, False, xbmcgui_module.ListItem())
        return False
    xbmcplugin_module.setResolvedUrl(
        handle,
        True,
        build_resolved_listitem(
            resolved,
            xbmcgui_module=xbmcgui_module,
            metadata_lookup=metadata_lookup,
        ),
    )
    return True


def pick_highlight_color(
    settings: KodiSettings,
    key: str = "ui_color_1080p",
    *,
    dialog: Any | None = None,
) -> str:
    current = settings.get_string(key, "deepskyblue")
    dialog = dialog or _dialog()
    if dialog is None or not hasattr(dialog, "colorpicker"):
        return current
    try:
        selected = dialog.colorpicker("Select highlight color", current)
    except TypeError:
        selected = dialog.colorpicker(current)
    if selected:
        settings.set_string(key, str(selected))
        return str(selected)
    return current


def _source_color(source: SourceResult, settings: KodiUiSettings) -> str:
    quality = (source.quality or "").strip().lower()
    if quality in {"4k", "2160p"}:
        return settings.color_4k
    if quality == "1080p":
        return settings.color_1080p
    if quality == "720p":
        return settings.color_720p
    if quality == "cam":
        return settings.color_cam
    if quality == "scr":
        return settings.color_scr
    if source.direct:
        return settings.color_direct
    return ""


def _apply_video_info(item: Any, source: SourceResult, title: str) -> None:
    info: dict[str, Any] = {"title": title}
    if source.metadata.get("plot"):
        info["plot"] = source.metadata["plot"]
    if source.metadata.get("year"):
        with suppress(TypeError, ValueError):
            info["year"] = int(source.metadata["year"])
    if hasattr(item, "setInfo"):
        item.setInfo("video", info)
    art = {
        key: value
        for key, value in {
            "thumb": source.metadata.get("thumb"),
            "poster": source.metadata.get("poster"),
            "fanart": source.metadata.get("fanart"),
            "icon": source.metadata.get("icon"),
        }.items()
        if value
    }
    if art and hasattr(item, "setArt"):
        item.setArt(art)


def _xbmcgui() -> Any:
    try:
        import xbmcgui  # type: ignore

        return xbmcgui
    except Exception:
        return _FallbackXbmcGui


def _xbmcplugin() -> Any | None:
    try:
        import xbmcplugin  # type: ignore

        return xbmcplugin
    except Exception:
        return None


def _dialog() -> Any | None:
    gui = _xbmcgui()
    if hasattr(gui, "Dialog"):
        return gui.Dialog()
    return None


class _FallbackListItem:
    def __init__(self, label: str = "", path: str = "") -> None:
        self.label = label
        self.path = path
        self.properties: dict[str, str] = {}
        self.info: dict[str, dict[str, Any]] = {}
        self.art: dict[str, str] = {}

    def setProperty(self, key: str, value: str) -> None:  # noqa: N802 - Kodi API name
        self.properties[key] = value

    def setInfo(self, info_type: str, info: dict[str, Any]) -> None:  # noqa: N802
        self.info[info_type] = dict(info)

    def setArt(self, art: dict[str, str]) -> None:  # noqa: N802
        self.art.update(art)


class _FallbackXbmcGui:
    ListItem = _FallbackListItem
