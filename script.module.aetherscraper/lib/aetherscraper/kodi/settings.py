from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from ..config import ProviderConfig

ADDON_ID = "script.module.aetherscraper"

_DEFAULTS: dict[str, str] = {
    "debug_logging": "false",
    "scrape_timeout": "30",
    "max_results": "100",
    "provider_timeout": "10",
    "provider_retries": "1",
    "concurrent_scraping": "false",
    "filter_hevc": "false",
    "filter_av1": "false",
    "filter_dolby_vision": "false",
    "filter_hdr": "false",
    "filter_foreign_audio": "false",
    "use_default_undesirables": "true",
    "undesirable_keywords": "",
    "language_filter_enabled": "false",
    "priority_language": "en",
    "support_file_logging": "false",
    "support_log_level": "info",
    "support_redact_secrets": "true",
    "support_max_log_bytes": "262144",
    "ui_color_tags": "true",
    "ui_result_format": "list",
    "ui_highlight_type": "resolution",
    "ui_color_single": "dodgerblue",
    "ui_color_4k": "gold",
    "ui_color_1080p": "deepskyblue",
    "ui_color_720p": "limegreen",
    "ui_color_cam": "red",
    "ui_color_scr": "orange",
    "ui_color_sd": "green",
    "ui_color_direct": "white",
    "ui_autoplay_policy": "score_quality_size",
    "provider.torznab.enabled": "false",
    "provider.torznab.base_url": "",
    "provider.torznab.api_key": "",
    "provider.prowlarr.enabled": "false",
    "provider.prowlarr.base_url": "",
    "provider.prowlarr.api_key": "",
    "provider.tbtorznab.enabled": "false",
    "provider.tbtorznab.base_url": "https://search-api.torbox.app/torznab/api",
    "provider.tbtorznab.api_key": "",
    "provider.torbox_torznab.enabled": "false",
    "provider.torbox_torznab.base_url": "",
    "provider.torbox_torznab.api_key": "",
    "provider.aiostreams.enabled": "false",
    "provider.aiostreams.instance_url": "",
    "provider.aiostreams.auth_token": "",
    "provider.aiostreams.auth_header": "Authorization",
    "provider.ytsmx.enabled": "false",
    "provider.ytsmx.base_url": "https://yts.mx/api/v2/list_movies.json",
}

_SETTING_ALIASES: dict[str, tuple[str, ...]] = {
    "scrape_timeout": ("scraping_timeout",),
    "filter_foreign_audio": ("filter.foreign.single.audio",),
    "language_filter_enabled": ("results.language_filter",),
    "priority_language": ("results.language",),
    "ui_result_format": ("results.list_format",),
    "ui_highlight_type": ("highlight.type",),
    "ui_color_single": ("scraper_single_highlight",),
    "ui_color_4k": ("scraper_4k_highlight",),
    "ui_color_1080p": ("scraper_1080p_highlight",),
    "ui_color_720p": ("scraper_720p_highlight",),
    "ui_color_sd": ("scraper_SD_highlight",),
    "provider.tbtorznab.api_key": ("torbox.token",),
    "provider.tbtorznab.enabled": ("provider.tbtorznab",),
}
_LANGUAGE_CODES = {
    "english": "en",
    "en": "en",
    "french": "fr",
    "fr": "fr",
    "spanish": "es",
    "es": "es",
    "german": "de",
    "de": "de",
    "italian": "it",
    "it": "it",
    "japanese": "ja",
    "ja": "ja",
    "korean": "ko",
    "ko": "ko",
    "chinese": "zh",
    "zh": "zh",
    "portuguese": "pt",
    "pt": "pt",
    "russian": "ru",
    "ru": "ru",
}


class KodiSettings:
    """Kodi add-on settings wrapper with non-Kodi fallback storage.

    Hidden Kodi settings are plaintext on disk. Do not log secret values read through
    this helper.
    """

    def __init__(
        self,
        addon_id: str = ADDON_ID,
        fallback: dict[str, str] | None = None,
        addon: Any | None = None,
    ) -> None:
        self.addon_id = addon_id
        self._fallback = dict(_DEFAULTS)
        if fallback:
            normalized = {key: str(value) for key, value in fallback.items()}
            self._fallback.update(normalized)
            for canonical, aliases in _SETTING_ALIASES.items():
                if canonical not in normalized:
                    for alias in aliases:
                        if alias in normalized:
                            self._fallback[canonical] = normalized[alias]
                            break
        self._addon = addon if addon is not None else self._load_addon(addon_id)

    @property
    def kodi_available(self) -> bool:
        return self._addon is not None

    def get_string(self, key: str, default: str = "") -> str:
        for candidate in self._setting_candidates(key):
            value = self._get_from_kodi(candidate)
            if value is not None and value != "":
                return value
        for candidate in self._setting_candidates(key):
            value = self._fallback.get(candidate)
            if value is not None and value != "":
                return value
        return self._fallback.get(key, default)

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get_string(key, str(default)).strip().lower()
        return value in {"1", "true", "yes", "on", "enabled"}

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self.get_string(key, str(default)))
        except (TypeError, ValueError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        try:
            return float(self.get_string(key, str(default)))
        except (TypeError, ValueError):
            return default

    def set_string(self, key: str, value: str) -> None:
        text = str(value)
        if self._addon is not None:
            self._set_to_kodi(key, text)
        self._fallback[key] = text

    def set_bool(self, key: str, value: bool) -> None:
        self.set_string(key, "true" if value else "false")

    def set_int(self, key: str, value: int) -> None:
        self.set_string(key, str(int(value)))

    def snapshot(self) -> SettingsSnapshot:
        return SettingsSnapshot.from_settings(self)

    @staticmethod
    def _setting_candidates(key: str) -> tuple[str, ...]:
        candidates = [key]
        aliases = list(_SETTING_ALIASES.get(key, ()))
        aliases.extend(
            canonical
            for canonical, canonical_aliases in _SETTING_ALIASES.items()
            if key in canonical_aliases
        )
        if key.startswith("provider.") and key.endswith(".enabled"):
            aliases.append(key[: -len(".enabled")])
        elif key.startswith("provider.") and not key.endswith(".enabled"):
            aliases.append(key + ".enabled")
        candidates.extend(item for item in aliases if item not in candidates)
        return tuple(candidates)

    def _get_from_kodi(self, key: str) -> str | None:
        if self._addon is None:
            return None
        getter_name = self._typed_getter(key)
        if getter_name and hasattr(self._addon, getter_name):
            try:
                value = getattr(self._addon, getter_name)(key)
                return str(value).lower() if isinstance(value, bool) else str(value)
            except Exception:
                return None
        try:
            return str(self._addon.getSetting(key))
        except Exception:
            return None

    def _set_to_kodi(self, key: str, value: str) -> None:
        addon = self._addon
        if addon is None:
            return
        try:
            if hasattr(addon, "setSetting"):
                addon.setSetting(key, value)
        except Exception:
            return

    @staticmethod
    def _typed_getter(key: str) -> str:
        if key in {
            "debug_logging",
            "filter_hevc",
            "filter_av1",
            "filter_dolby_vision",
            "filter_hdr",
            "filter_foreign_audio",
            "filter.foreign.single.audio",
            "use_default_undesirables",
            "language_filter_enabled",
            "results.language_filter",
            "concurrent_scraping",
            "support_file_logging",
            "support_redact_secrets",
            "ui_color_tags",
        } or (
            key.startswith("provider.")
            and (key.endswith(".enabled") or key.count(".") == 1)
        ):
            return "getSettingBool"
        if key in {
            "scrape_timeout",
            "scraping_timeout",
            "max_results",
            "provider_timeout",
            "provider_retries",
            "support_max_log_bytes",
        }:
            return "getSettingInt"
        return ""

    @staticmethod
    def _load_addon(addon_id: str) -> Any | None:
        try:
            import xbmcaddon  # type: ignore

            return xbmcaddon.Addon(addon_id)
        except Exception:
            return None


@dataclass(frozen=True)
class SettingsSnapshot:
    debug_logging: bool = False
    scrape_timeout: int = 30
    max_results: int = 100
    provider_timeout: int = 10
    provider_retries: int = 1
    concurrent_scraping: bool = False
    filter_hevc: bool = False
    filter_av1: bool = False
    filter_dolby_vision: bool = False
    filter_hdr: bool = False
    filter_foreign_audio: bool = False
    use_default_undesirables: bool = True
    undesirable_keywords: list[str] = field(default_factory=list)
    language_filter_enabled: bool = False
    priority_language: str = "en"
    languages: list[str] = field(default_factory=list)
    extra: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_settings(cls, settings: KodiSettings) -> SettingsSnapshot:
        from ..release import parse_keyword_list

        return cls(
            debug_logging=settings.get_bool("debug_logging", False),
            scrape_timeout=settings.get_int("scrape_timeout", 30),
            max_results=settings.get_int("max_results", 100),
            provider_timeout=settings.get_int("provider_timeout", 10),
            provider_retries=settings.get_int("provider_retries", 1),
            concurrent_scraping=settings.get_bool("concurrent_scraping", False),
            filter_hevc=settings.get_bool("filter_hevc", False),
            filter_av1=settings.get_bool("filter_av1", False),
            filter_dolby_vision=settings.get_bool("filter_dolby_vision", False),
            filter_hdr=settings.get_bool("filter_hdr", False),
            filter_foreign_audio=settings.get_bool("filter_foreign_audio", False),
            use_default_undesirables=settings.get_bool(
                "use_default_undesirables", True
            ),
            undesirable_keywords=parse_keyword_list(
                settings.get_string("undesirable_keywords", "")
            ),
            language_filter_enabled=settings.get_bool("language_filter_enabled", False),
            priority_language=language_code(
                settings.get_string("priority_language", "en")
            ),
            languages=language_filter_list(settings),
        )

    @classmethod
    def from_environment(cls, prefix: str = "AETHERSCRAPERS_") -> SettingsSnapshot:
        fallback = {
            "debug_logging": os.getenv(
                prefix + "DEBUG_LOGGING", _DEFAULTS["debug_logging"]
            ),
            "scrape_timeout": os.getenv(
                prefix + "SCRAPE_TIMEOUT", _DEFAULTS["scrape_timeout"]
            ),
            "max_results": os.getenv(prefix + "MAX_RESULTS", _DEFAULTS["max_results"]),
            "provider_timeout": os.getenv(
                prefix + "PROVIDER_TIMEOUT", _DEFAULTS["provider_timeout"]
            ),
            "provider_retries": os.getenv(
                prefix + "PROVIDER_RETRIES", _DEFAULTS["provider_retries"]
            ),
            "concurrent_scraping": os.getenv(
                prefix + "CONCURRENT_SCRAPING", _DEFAULTS["concurrent_scraping"]
            ),
            "filter_hevc": os.getenv(prefix + "FILTER_HEVC", _DEFAULTS["filter_hevc"]),
            "filter_av1": os.getenv(prefix + "FILTER_AV1", _DEFAULTS["filter_av1"]),
            "filter_dolby_vision": os.getenv(
                prefix + "FILTER_DOLBY_VISION", _DEFAULTS["filter_dolby_vision"]
            ),
            "filter_hdr": os.getenv(prefix + "FILTER_HDR", _DEFAULTS["filter_hdr"]),
            "filter_foreign_audio": os.getenv(
                prefix + "FILTER_FOREIGN_AUDIO", _DEFAULTS["filter_foreign_audio"]
            ),
            "use_default_undesirables": os.getenv(
                prefix + "USE_DEFAULT_UNDESIRABLES",
                _DEFAULTS["use_default_undesirables"],
            ),
            "undesirable_keywords": os.getenv(
                prefix + "UNDESIRABLE_KEYWORDS", _DEFAULTS["undesirable_keywords"]
            ),
            "language_filter_enabled": os.getenv(
                prefix + "LANGUAGE_FILTER_ENABLED",
                _DEFAULTS["language_filter_enabled"],
            ),
            "priority_language": os.getenv(
                prefix + "PRIORITY_LANGUAGE", _DEFAULTS["priority_language"]
            ),
        }
        return KodiSettings(fallback=fallback).snapshot()


def language_code(value: str) -> str:
    text = str(value or "").strip().lower().replace("_", "-")
    if not text:
        return "en"
    if text in _LANGUAGE_CODES:
        return _LANGUAGE_CODES[text]
    return text.split("-", 1)[0]


def language_filter_list(settings: KodiSettings) -> list[str]:
    if not settings.get_bool("language_filter_enabled", False):
        return []
    return [language_code(settings.get_string("priority_language", "en"))]


def provider_enabled_setting(provider_id: str) -> str:
    return f"provider.{provider_id}.enabled"


def set_provider_enabled(
    settings: KodiSettings, provider_id: str, enabled: bool
) -> None:
    settings.set_bool(provider_enabled_setting(provider_id), enabled)


def restore_provider_defaults(
    settings: KodiSettings, configs: list[ProviderConfig]
) -> dict[str, bool]:
    values = {config.id: config.enabled for config in configs}
    _set_provider_group(settings, values)
    return values


def enable_all_providers(
    settings: KodiSettings, configs: list[ProviderConfig]
) -> dict[str, bool]:
    values = {config.id: True for config in configs}
    _set_provider_group(settings, values)
    return values


def disable_all_providers(
    settings: KodiSettings, configs: list[ProviderConfig]
) -> dict[str, bool]:
    values = {config.id: False for config in configs}
    _set_provider_group(settings, values)
    return values


def enable_torrent_providers(
    settings: KodiSettings, configs: list[ProviderConfig]
) -> dict[str, bool]:
    values = {config.id: config.provider_type == "torrent" for config in configs}
    _set_provider_group(settings, values)
    return values


def enable_pack_capable_providers(
    settings: KodiSettings, configs: list[ProviderConfig]
) -> dict[str, bool]:
    values = {config.id: config.pack_capable for config in configs}
    _set_provider_group(settings, values)
    return values


def setting_default(key: str, default: str = "") -> str:
    return _DEFAULTS.get(key, default)


def reset_settings(
    settings: KodiSettings,
    keys: Iterable[str] | None = None,
    confirm: bool = False,
) -> list[str]:
    if not confirm:
        raise PermissionError("Settings cleanup requires explicit confirmation.")
    selected = list(keys) if keys is not None else list(_DEFAULTS)
    reset: list[str] = []
    for key in selected:
        if key not in _DEFAULTS:
            continue
        settings.set_string(key, _DEFAULTS[key])
        reset.append(key)
    return reset


def _set_provider_group(settings: KodiSettings, values: dict[str, bool]) -> None:
    for provider_id, enabled in values.items():
        set_provider_enabled(settings, provider_id, enabled)
