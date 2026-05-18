from __future__ import annotations

import time
from dataclasses import dataclass
from typing import (  # noqa: UP035 - Kodi Python may lack collections.abc generics
    Any,
    Callable,
)

from .settings import ADDON_ID, KodiSettings
from .storage import first_run_setup, record_version_update
from .window import WindowPropertyStore, set_lifecycle_property, sync_settings_to_window

SettingsChangedCallback = Callable[[KodiSettings], None]


@dataclass(frozen=True)
class LifecycleStatus:
    addon_id: str
    version: str
    profile: str
    first_run_complete: bool
    version_changed: bool
    cleanup_required: bool


def addon_version(addon_id: str = ADDON_ID, default: str = "") -> str:
    try:
        import xbmcaddon  # type: ignore

        return str(xbmcaddon.Addon(addon_id).getAddonInfo("version") or default)
    except Exception:
        return default


def run_startup(
    addon_id: str = ADDON_ID,
    version: str | None = None,
    settings: KodiSettings | None = None,
    base_path: str | None = None,
    store: WindowPropertyStore | None = None,
) -> LifecycleStatus:
    """Run safe startup hooks. Never deletes settings/cache automatically."""

    resolved_version = version if version is not None else addon_version(addon_id)
    paths = first_run_setup(
        addon_id=addon_id, version=resolved_version, base_path=base_path
    )
    version_changed = record_version_update(
        addon_id=addon_id, version=resolved_version, base_path=base_path
    )
    state = paths.read_state()
    store = store or WindowPropertyStore(addon_id=addon_id)
    sync_settings_to_window(settings or KodiSettings(addon_id=addon_id), store=store)
    set_lifecycle_property("started", "true", store=store)
    set_lifecycle_property(
        "cleanup_required",
        "true" if state.get("cleanup_required") else "false",
        store=store,
    )
    return LifecycleStatus(
        addon_id=addon_id,
        version=resolved_version,
        profile=paths.profile,
        first_run_complete=bool(state.get("first_run_complete")),
        version_changed=version_changed,
        cleanup_required=bool(state.get("cleanup_required")),
    )


class SettingsMonitor:
    """Kodi Monitor wrapper with fallback polling for non-Kodi tests."""

    def __init__(
        self,
        settings: KodiSettings | None = None,
        on_changed: SettingsChangedCallback | None = None,
    ) -> None:
        self.settings = settings or KodiSettings()
        self.on_changed = on_changed or (
            lambda current: sync_settings_to_window(current)
        )
        self._changed = False
        self._monitor = self._create_monitor()

    def abort_requested(self) -> bool:
        if self._monitor is not None and hasattr(self._monitor, "abortRequested"):
            return bool(self._monitor.abortRequested())
        return False

    def wait_for_abort(self, timeout: float) -> bool:
        if self._monitor is not None and hasattr(self._monitor, "waitForAbort"):
            return bool(self._monitor.waitForAbort(timeout))
        time.sleep(max(0.0, min(float(timeout), 0.01)))
        return False

    def poll(self) -> bool:
        if not self._changed:
            return False
        self._changed = False
        self.on_changed(self.settings)
        return True

    def mark_changed(self) -> None:
        self._changed = True

    def _create_monitor(self) -> Any | None:
        try:
            import xbmc  # type: ignore
        except Exception:
            return None

        outer = self

        class _KodiMonitor(xbmc.Monitor):  # type: ignore[name-defined]
            def onSettingsChanged(self) -> None:  # noqa: N802 - Kodi API name
                outer.mark_changed()

        try:
            return _KodiMonitor()
        except Exception:
            return None


def run_service(
    addon_id: str = ADDON_ID,
    version: str | None = None,
    settings: KodiSettings | None = None,
    base_path: str | None = None,
    interval: float = 2.0,
    max_iterations: int | None = None,
) -> LifecycleStatus:
    """Service loop for Kodi. Bounded by Monitor.waitForAbort()."""

    settings = settings or KodiSettings(addon_id=addon_id)
    status = run_startup(
        addon_id=addon_id, version=version, settings=settings, base_path=base_path
    )
    monitor = SettingsMonitor(settings=settings)
    iterations = 0
    while not monitor.abort_requested():
        monitor.poll()
        if max_iterations is not None and iterations >= max_iterations:
            break
        iterations += 1
        if monitor.wait_for_abort(interval):
            break
    return status
