from __future__ import annotations

import sys
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode

PLUGIN_ADDON_ID = "plugin.program.aetherscraper"
MODULE_ADDON_ID = "script.module.aetherscraper"


@dataclass(frozen=True)
class MenuEntry:
    label: str
    action: str
    is_folder: bool = True
    info: str = ""
    params: dict[str, str] | None = None


def parse_params(argv: list[str] | None = None) -> dict[str, str]:
    args = list(sys.argv if argv is None else argv)
    query = args[2] if len(args) > 2 else ""
    if query.startswith("?"):
        query = query[1:]
    return dict(parse_qsl(query, keep_blank_values=True))


def plugin_handle(argv: list[str] | None = None) -> int | None:
    args = list(sys.argv if argv is None else argv)
    if len(args) < 2:
        return None
    try:
        return int(args[1])
    except (TypeError, ValueError):
        return None


def build_url(base_url: str, **query: str) -> str:
    return base_url + "?" + urlencode(query)


def root_entries() -> list[MenuEntry]:
    return [
        MenuEntry(_localize(30100, "Settings"), "settings", is_folder=False),
        MenuEntry(_localize(30101, "Providers"), "providers"),
        MenuEntry(
            _localize(30105, "Enable all providers"), "enable_all", is_folder=False
        ),
        MenuEntry(
            _localize(30106, "Disable all providers"), "disable_all", is_folder=False
        ),
        MenuEntry(
            _localize(30107, "Enable torrent providers"),
            "enable_torrents",
            is_folder=False,
        ),
        MenuEntry(
            _localize(30108, "Enable pack-capable providers"),
            "enable_packs",
            is_folder=False,
        ),
        MenuEntry(
            _localize(30109, "Restore provider defaults"),
            "restore_defaults",
            is_folder=False,
        ),
        MenuEntry(
            _localize(30102, "External setup help"), "external_help", is_folder=False
        ),
        MenuEntry(_localize(30103, "Health check"), "health", is_folder=False),
        MenuEntry(_localize(30104, "Module help"), "module_help", is_folder=False),
    ]


def run(argv: list[str] | None = None) -> None:
    args = list(sys.argv if argv is None else argv)
    params = parse_params(args)
    action = (params.get("action") or "root").strip().lower()
    if action in {"mediaplay", "media_play", "play"}:
        _delegate_media_play(params, args)
        return
    if action == "settings":
        _open_module_settings()
        _end_directory(args)
        return
    if action in {
        "enable_all",
        "disable_all",
        "enable_torrents",
        "enable_packs",
        "restore_defaults",
    }:
        _provider_group_action(action)
        _end_directory(args)
        return
    if action == "providers":
        _show_providers(args)
        return
    if action == "external_help":
        _show_text("AetherScraper External Setup", external_help_text())
        _end_directory(args)
        return
    if action == "health":
        _show_health()
        _end_directory(args)
        return
    if action == "module_help":
        _show_module_help()
        _end_directory(args)
        return
    _show_root(args)


def external_help_text() -> str:
    return (
        "AetherScraper core is script.module.aetherscraper and appears under Add-on "
        "libraries. This companion appears under Program add-ons.\n\n"
        "Umbrella: Tools > Providers > Enable External Providers, then select AetherScraper "
        "if your Umbrella build supports external provider modules.\n\n"
        "FenLight: use External Scraper picker and choose AetherScraper where "
        "available.\n\n"
        "Player selector JSON: prefer plugin://plugin.program.aetherscraper/?action=MediaPlay "
        "for visible companion routing. The module route remains import/support only "
        "unless manual Kodi validation proves plugin://script.module.aetherscraper safe."
    )


def _show_root(argv: list[str]) -> None:
    handle = plugin_handle(argv)
    if handle is None:
        return
    _set_content(handle, "files")
    for entry in root_entries():
        query = dict(entry.params or {})
        query.setdefault("action", entry.action)
        _add_directory_item(
            handle,
            build_url(argv[0], **query),
            entry.label,
            is_folder=entry.is_folder,
            info=entry.info,
        )
    _end_directory(argv)


def _show_providers(argv: list[str]) -> None:
    handle = plugin_handle(argv)
    if handle is None:
        return
    _set_content(handle, "files")
    for label in _provider_labels():
        _add_directory_item(
            handle, build_url(argv[0], action="providers"), label, False
        )
    _end_directory(argv)


def _provider_labels() -> list[str]:
    try:
        from aetherscraper import KodiSettings, load_providers
    except Exception as exc:
        return [f"Provider load unavailable: {exc}"]
    settings = KodiSettings()
    providers, errors = load_providers(settings=settings)
    labels = []
    for provider in providers:
        config = provider.config
        state = "enabled" if provider.is_enabled() else "disabled"
        packs = "packs" if config.pack_capable else "no packs"
        labels.append(
            f"{config.name} [{state}] type={config.provider_type} priority={config.priority} {packs}"
        )
    labels.extend(f"Load error: {error.module}: {error.message}" for error in errors)
    return labels or ["No providers discovered."]


def _provider_group_action(action: str) -> None:
    prompt = _localize(30201, "Run provider action: {action}?").format(action=action)
    if not _confirm(prompt):
        _notify("AetherScraper", _localize(30200, "Provider action cancelled"))
        return
    try:
        from aetherscraper import (
            KodiSettings,
            disable_all_providers,
            enable_all_providers,
            enable_pack_capable_providers,
            enable_torrent_providers,
            load_provider_classes,
            restore_provider_defaults,
        )
    except Exception as exc:
        _notify("AetherScraper", f"Provider action unavailable: {exc}")
        return
    settings = KodiSettings()
    classes, errors = load_provider_classes()
    configs = [provider_class.config for provider_class in classes]
    actions = {
        "enable_all": enable_all_providers,
        "disable_all": disable_all_providers,
        "enable_torrents": enable_torrent_providers,
        "enable_packs": enable_pack_capable_providers,
        "restore_defaults": restore_provider_defaults,
    }
    values = actions[action](settings, configs)
    message = f"Updated {len(values)} providers"
    if errors:
        message += f"; {len(errors)} load errors"
    _notify("AetherScraper", message)


def _localize(string_id: int, fallback: str) -> str:
    try:
        import xbmcaddon  # type: ignore
    except Exception:
        return fallback
    try:
        value = xbmcaddon.Addon(PLUGIN_ADDON_ID).getLocalizedString(string_id)
    except Exception:
        return fallback
    return value or fallback


def _delegate_media_play(params: dict[str, str], argv: list[str]) -> None:
    try:
        from aetherscraper import dispatch_action
    except Exception:
        _end_directory(argv)
        return
    dispatch_action("mediaplay", params=params, argv=argv)


def _show_health() -> None:
    try:
        from aetherscraper import KodiSettings, load_providers, run_provider_health_checks
    except Exception as exc:
        _show_text("AetherScraper Health", f"Health check unavailable: {exc}")
        return
    providers, errors = load_providers(settings=KodiSettings())
    summary = run_provider_health_checks(providers)
    text = (
        f"Providers: {summary.ok}/{summary.total} healthy\nLoad errors: {len(errors)}"
    )
    _show_text("AetherScraper Health", text)


def _show_module_help() -> None:
    try:
        from aetherscraper import help_text
    except Exception as exc:
        _show_text("AetherScraper Help", f"Help unavailable: {exc}")
        return
    _show_text("AetherScraper Help", help_text())


def _open_module_settings() -> bool:
    try:
        import xbmcaddon  # type: ignore
    except Exception:
        return False
    try:
        xbmcaddon.Addon(MODULE_ADDON_ID).openSettings()
        return True
    except Exception:
        return False


def _add_directory_item(
    handle: int, url: str, label: str, is_folder: bool, info: str = ""
) -> None:
    try:
        import xbmcgui  # type: ignore
        import xbmcplugin  # type: ignore
    except Exception:
        return
    item = xbmcgui.ListItem(label=label)
    if info:
        item.setInfo("video", {"plot": info})
    xbmcplugin.addDirectoryItem(handle, url, item, isFolder=is_folder)


def _set_content(handle: int, content: str) -> None:
    try:
        import xbmcplugin  # type: ignore
    except Exception:
        return
    xbmcplugin.setContent(handle, content)


def _end_directory(argv: list[str]) -> None:
    handle = plugin_handle(argv)
    if handle is None:
        return
    try:
        import xbmcplugin  # type: ignore
    except Exception:
        return
    xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=False)


def _confirm(message: str) -> bool:
    try:
        import xbmcgui  # type: ignore
    except Exception:
        return False
    return bool(xbmcgui.Dialog().yesno("AetherScraper", message))


def _notify(title: str, message: str) -> None:
    try:
        import xbmcgui  # type: ignore
    except Exception:
        return
    xbmcgui.Dialog().notification(title, message)


def _show_text(title: str, text: str) -> bool:
    try:
        import xbmcgui  # type: ignore
    except Exception:
        return False
    xbmcgui.Dialog().textviewer(title, text)
    return True
