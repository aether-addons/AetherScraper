from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .settings import ADDON_ID


@dataclass(frozen=True)
class ProfilePaths:
    addon_id: str = ADDON_ID
    profile: str = ""
    cache: str = ""
    state: str = ""
    kodi_vfs: Any | None = None

    @classmethod
    def create(
        cls, addon_id: str = ADDON_ID, base_path: str | None = None
    ) -> ProfilePaths:
        vfs = _load_xbmcvfs()
        profile = base_path or f"special://profile/addon_data/{addon_id}"
        if vfs is not None:
            profile = _translate(vfs, profile)
        else:
            profile = _fallback_profile_path(addon_id, profile)
        cache = os.path.join(profile, "cache")
        state = os.path.join(profile, "state.json")
        return cls(
            addon_id=addon_id, profile=profile, cache=cache, state=state, kodi_vfs=vfs
        )

    def ensure(self) -> None:
        _mkdirs(self.profile, self.kodi_vfs)
        _mkdirs(self.cache, self.kodi_vfs)

    def read_state(self) -> dict[str, Any]:
        data = _read_text(self.state, self.kodi_vfs)
        if not data:
            return {}
        try:
            value = json.loads(data)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def write_state(self, state: dict[str, Any]) -> None:
        self.ensure()
        payload = json.dumps(state, indent=2, sort_keys=True)
        _write_text(self.state, payload, self.kodi_vfs)


def ensure_profile(
    addon_id: str = ADDON_ID, base_path: str | None = None
) -> ProfilePaths:
    paths = ProfilePaths.create(addon_id=addon_id, base_path=base_path)
    paths.ensure()
    return paths


def first_run_setup(
    addon_id: str = ADDON_ID, version: str = "", base_path: str | None = None
) -> ProfilePaths:
    paths = ensure_profile(addon_id=addon_id, base_path=base_path)
    state = paths.read_state()
    if not state.get("first_run_complete"):
        state.update(
            {
                "addon_id": addon_id,
                "first_run_complete": True,
                "installed_version": version,
                "cleanup_required": False,
            }
        )
        paths.write_state(state)
    return paths


def record_version_update(
    addon_id: str = ADDON_ID, version: str = "", base_path: str | None = None
) -> bool:
    """Record version change and flag cleanup review; never deletes data."""

    paths = ensure_profile(addon_id=addon_id, base_path=base_path)
    state = paths.read_state()
    previous = str(state.get("installed_version", ""))
    changed = bool(version and previous and previous != version)
    state["addon_id"] = addon_id
    state["installed_version"] = version or previous
    if changed:
        state["previous_version"] = previous
        state["cleanup_required"] = True
    paths.write_state(state)
    return changed


def _load_xbmcvfs() -> Any | None:
    try:
        import xbmcvfs  # type: ignore

        return xbmcvfs
    except Exception:
        return None


def _translate(vfs: Any, path: str) -> str:
    if hasattr(vfs, "translatePath"):
        return str(vfs.translatePath(path))
    return path


def _fallback_profile_path(addon_id: str, profile: str) -> str:
    if not profile.startswith("special://"):
        return profile
    root = os.environ.get("AETHERSCRAPERS_PROFILE")
    if root:
        return os.path.join(root, addon_id)
    return str(Path.home() / ".kodi" / "userdata" / "addon_data" / addon_id)


def _mkdirs(path: str, vfs: Any | None) -> None:
    if vfs is not None and hasattr(vfs, "mkdirs"):
        vfs.mkdirs(path)
        return
    os.makedirs(path, exist_ok=True)


def _read_text(path: str, vfs: Any | None) -> str:
    if vfs is not None and hasattr(vfs, "File") and hasattr(vfs, "exists"):
        if not vfs.exists(path):
            return ""
        handle = vfs.File(path)
        try:
            data = handle.read()
        finally:
            handle.close()
        return data.decode("utf-8") if isinstance(data, bytes) else str(data)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _write_text(path: str, data: str, vfs: Any | None) -> None:
    if vfs is not None and hasattr(vfs, "File"):
        handle = vfs.File(path, "w")
        try:
            handle.write(data)
        finally:
            handle.close()
        return
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(data)
