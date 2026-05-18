from __future__ import annotations

import sys
from dataclasses import dataclass
from urllib.parse import parse_qs

from ..health import run_provider_health_checks
from ..loader import load_providers
from ..models import SourceResult
from ..support import changelog_text, help_text, log_text, show_text
from .lifecycle import run_startup
from .settings import ADDON_ID, KodiSettings
from .ui import pick_highlight_color, resolve_to_kodi


@dataclass(frozen=True)
class PluginActionResult:
    action: str
    ok: bool
    message: str = ""


def parse_plugin_query(argv: list[str] | None = None) -> dict[str, str]:
    argv = list(sys.argv if argv is None else argv)
    query = argv[2] if len(argv) > 2 else ""
    if query.startswith("?"):
        query = query[1:]
    values = parse_qs(query, keep_blank_values=True)
    return {key: items[-1] if items else "" for key, items in values.items()}


def run_plugin(
    argv: list[str] | None = None, settings: KodiSettings | None = None
) -> PluginActionResult:
    """Minimal Kodi plugin router for support/lifecycle actions.

    Media listings/playback are intentionally deferred to Phase 13.
    """

    params = parse_plugin_query(argv)
    action = params.get("action", "startup") or "startup"
    settings = settings or KodiSettings()
    result = dispatch_action(action, settings=settings, params=params, argv=argv)
    if result.action != "mediaplay":
        _end_directory(argv)
    return result


def dispatch_action(
    action: str,
    settings: KodiSettings | None = None,
    params: dict[str, str] | None = None,
    argv: list[str] | None = None,
) -> PluginActionResult:
    settings = settings or KodiSettings()
    params = params or {}
    normalized = action.strip().lower()
    if normalized in {"", "startup", "root"}:
        status = run_startup(settings=settings)
        return PluginActionResult(
            action="startup", ok=True, message=f"Profile ready: {status.profile}"
        )
    if normalized == "open_settings":
        return PluginActionResult(
            action=normalized, ok=_open_settings(), message="Settings opened"
        )
    if normalized == "help":
        text = help_text()
        return PluginActionResult(
            action=normalized, ok=show_text("AetherScraper Help", text), message=text
        )
    if normalized == "changelog":
        text = changelog_text()
        return PluginActionResult(
            action=normalized,
            ok=show_text("AetherScraper Changelog", text),
            message=text,
        )
    if normalized == "log":
        text = log_text()
        return PluginActionResult(
            action=normalized, ok=show_text("AetherScraper Log", text), message=text
        )
    if normalized == "health":
        providers, errors = load_providers(settings=settings)
        summary = run_provider_health_checks(providers)
        failed = summary.failed + len(errors)
        message = f"Providers: {summary.ok}/{summary.total} healthy, {failed} failed"
        return PluginActionResult(action=normalized, ok=failed == 0, message=message)
    if normalized == "pick_color":
        color = pick_highlight_color(settings)
        return PluginActionResult(
            action=normalized,
            ok=True,
            message=f"Selected highlight color: {color}",
        )
    if normalized in {"mediaplay", "media_play", "play"}:
        return _dispatch_media_play(params, argv)
    return PluginActionResult(action=normalized, ok=False, message="Unknown action.")


def _dispatch_media_play(
    params: dict[str, str], argv: list[str] | None = None
) -> PluginActionResult:
    url = params.get("url") or params.get("path")
    if not url:
        return PluginActionResult(
            action="mediaplay", ok=False, message="MediaPlay requires url or path."
        )
    source = SourceResult(
        provider=params.get("provider", "external"),
        title=params.get("title") or params.get("name") or "External source",
        url=url,
        quality=params.get("quality", "unknown"),
        language=params.get("language") or None,
        direct=True,
    )
    handle = _plugin_handle(argv)
    if handle is None:
        return PluginActionResult(
            action="mediaplay", ok=True, message="MediaPlay URL accepted."
        )
    ok = resolve_to_kodi(handle, source)
    return PluginActionResult(
        action="mediaplay",
        ok=ok,
        message="MediaPlay resolved" if ok else "MediaPlay resolve failed",
    )


def _open_settings(addon_id: str = ADDON_ID) -> bool:
    try:
        import xbmcaddon  # type: ignore
    except Exception:
        return False
    try:
        xbmcaddon.Addon(addon_id).openSettings()
        return True
    except Exception:
        return False


def _plugin_handle(argv: list[str] | None = None) -> int | None:
    argv = list(sys.argv if argv is None else argv)
    if len(argv) < 2:
        return None
    try:
        return int(argv[1])
    except (TypeError, ValueError):
        return None


def _end_directory(argv: list[str] | None = None) -> None:
    handle = _plugin_handle(argv)
    if handle is None:
        return
    try:
        import xbmcplugin  # type: ignore
    except Exception:
        return
    try:
        xbmcplugin.endOfDirectory(handle, succeeded=True)
    except Exception:
        return
