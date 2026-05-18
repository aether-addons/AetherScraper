from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .settings import ADDON_ID, KodiSettings

_WINDOW_ID = 10000
_PREFIX = ADDON_ID + "."
_FALLBACK_PROPERTIES: dict[str, str] = {}
_SAFE_SETTING_KEYS = (
    "debug_logging",
    "scrape_timeout",
    "max_results",
    "provider_timeout",
    "provider_retries",
    "concurrent_scraping",
    "filter_hevc",
    "filter_av1",
    "filter_dolby_vision",
    "filter_hdr",
    "filter_foreign_audio",
    "use_default_undesirables",
    "support_file_logging",
    "support_log_level",
)
_SECRET_KEY_PARTS = ("api_key", "token", "auth", "password", "secret", "cookie")


@dataclass(frozen=True)
class WindowPropertyStore:
    """Kodi window-property wrapper with non-Kodi fallback for tests.

    Window properties are process-visible coordination values, not secret storage.
    """

    addon_id: str = ADDON_ID
    window_id: int = _WINDOW_ID
    window: Any | None = None

    def __post_init__(self) -> None:
        if self.window is None:
            object.__setattr__(self, "window", self._load_window())

    def get(self, key: str, default: str = "") -> str:
        name = self._name(key)
        if self.window is not None and hasattr(self.window, "getProperty"):
            value = self.window.getProperty(name)
            return str(value) if value not in (None, "") else default
        return _FALLBACK_PROPERTIES.get(name, default)

    def set(self, key: str, value: object) -> None:
        if _is_secret_key(key):
            raise ValueError("Window properties must not store secrets.")
        name = self._name(key)
        text = str(value)
        if self.window is not None and hasattr(self.window, "setProperty"):
            self.window.setProperty(name, text)
            return
        _FALLBACK_PROPERTIES[name] = text

    def clear(self, key: str) -> None:
        name = self._name(key)
        if self.window is not None and hasattr(self.window, "clearProperty"):
            self.window.clearProperty(name)
            return
        _FALLBACK_PROPERTIES.pop(name, None)

    def _name(self, key: str) -> str:
        clean = str(key).strip().replace(" ", "_")
        if clean.startswith(self.addon_id + "."):
            return clean
        return self.addon_id + "." + clean

    def _load_window(self) -> Any | None:
        try:
            import xbmcgui  # type: ignore
        except Exception:
            return None
        try:
            return xbmcgui.Window(self.window_id)
        except Exception:
            return None


def sync_settings_to_window(
    settings: KodiSettings | None = None,
    store: WindowPropertyStore | None = None,
    keys: tuple[str, ...] = _SAFE_SETTING_KEYS,
) -> dict[str, str]:
    """Mirror non-secret coordination settings to Kodi window properties."""

    settings = settings or KodiSettings()
    store = store or WindowPropertyStore()
    mirrored: dict[str, str] = {}
    for key in keys:
        if _is_secret_key(key):
            continue
        value = settings.get_string(key, "")
        store.set("settings." + key, value)
        mirrored[key] = value
    store.set("settings.synced", "true")
    return mirrored


def set_lifecycle_property(
    key: str, value: object, store: WindowPropertyStore | None = None
) -> None:
    (store or WindowPropertyStore()).set("lifecycle." + key, value)


def get_lifecycle_property(
    key: str, default: str = "", store: WindowPropertyStore | None = None
) -> str:
    return (store or WindowPropertyStore()).get("lifecycle." + key, default)


def clear_aetherscraper_properties(store: WindowPropertyStore | None = None) -> None:
    """Clear fallback properties. Kodi window enumeration is unavailable; clear known keys."""

    store = store or WindowPropertyStore()
    for key in ("settings.synced", "lifecycle.started", "lifecycle.cleanup_required"):
        store.clear(key)
    for key in _SAFE_SETTING_KEYS:
        store.clear("settings." + key)


def _is_secret_key(key: str) -> bool:
    lower = key.lower()
    return any(part in lower for part in _SECRET_KEY_PARTS)
