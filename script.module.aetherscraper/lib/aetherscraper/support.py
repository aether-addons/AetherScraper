from __future__ import annotations

import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .kodi.settings import ADDON_ID, KodiSettings, reset_settings
from .kodi.storage import ProfilePaths

_SECRET_QUERY_RE = re.compile(
    r"(?i)([?&](?:api[_-]?key|apikey|token|auth|authorization|password|secret|signature|sig)=)[^&\s]+"
)
_SECRET_HEADER_RE = re.compile(
    r"(?im)^((?:authorization|cookie|set-cookie|x-api-key|x-auth-token)\s*:\s*).+$"
)
_SECRET_VALUE_RE = re.compile(
    r"(?i)\b(api[_-]?key|apikey|token|auth_token|password|secret)\b\s*[:=]\s*[^\s,;]+"
)
_AUTH_SCHEME_RE = re.compile(r"(?i)\b(Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+")


@dataclass(frozen=True)
class DebugConfig:
    enabled: bool = False
    file_logging: bool = False
    log_level: str = "info"
    redact_secrets: bool = True
    max_log_bytes: int = 262_144

    @classmethod
    def from_settings(cls, settings: KodiSettings | None = None) -> DebugConfig:
        settings = settings or KodiSettings()
        level = settings.get_string("support_log_level", "info").strip().lower()
        if level not in {"debug", "info", "warning", "error"}:
            level = "info"
        return cls(
            enabled=settings.get_bool("debug_logging", False),
            file_logging=settings.get_bool("support_file_logging", False),
            log_level=level,
            redact_secrets=settings.get_bool("support_redact_secrets", True),
            max_log_bytes=max(4096, settings.get_int("support_max_log_bytes", 262_144)),
        )


def redact_secrets(message: object) -> str:
    text = str(message)
    text = _SECRET_HEADER_RE.sub(r"\1[redacted]", text)
    text = _SECRET_QUERY_RE.sub(r"\1[redacted]", text)
    text = _SECRET_VALUE_RE.sub(lambda match: f"{match.group(1)}=[redacted]", text)
    text = _AUTH_SCHEME_RE.sub(lambda match: f"{match.group(1)} [redacted]", text)
    return text


class AddonLogBackend:
    def __init__(
        self,
        path: str | None = None,
        paths: ProfilePaths | None = None,
        debug: DebugConfig | None = None,
    ) -> None:
        self.paths = paths or ProfilePaths.create(addon_id=ADDON_ID)
        self.debug = debug or DebugConfig()
        self.path = path or os.path.join(self.paths.profile, "logs", "aetherscraper.log")

    @classmethod
    def from_profile(
        cls, addon_id: str = ADDON_ID, base_path: str | None = None
    ) -> AddonLogBackend:
        paths = ProfilePaths.create(addon_id=addon_id, base_path=base_path)
        return cls(paths=paths)

    def write(self, message: object, level: str = "info") -> None:
        line = redact_secrets(message) if self.debug.redact_secrets else str(message)
        payload = f"[{level.upper()}] {line}\n"
        self._ensure_parent()
        self._rotate_if_needed(len(payload.encode("utf-8")))
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(payload)

    def read(self) -> str:
        if not os.path.exists(self.path):
            return ""
        with open(self.path, encoding="utf-8") as handle:
            return handle.read()

    def tail(self, lines: int = 200) -> str:
        content = self.read().splitlines()
        return "\n".join(content[-max(1, lines) :])

    def clear(self, confirm: bool = False) -> bool:
        if not confirm:
            raise PermissionError("Log clearing requires explicit confirmation.")
        if not os.path.exists(self.path):
            return False
        os.remove(self.path)
        return True

    def _ensure_parent(self) -> None:
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def _rotate_if_needed(self, incoming_bytes: int) -> None:
        if not os.path.exists(self.path):
            return
        if os.path.getsize(self.path) + incoming_bytes <= self.debug.max_log_bytes:
            return
        backup = self.path + ".1"
        if os.path.exists(backup):
            os.remove(backup)
        os.replace(self.path, backup)


def addon_file_text(filename: str, addon_root: str | None = None) -> str:
    root = Path(addon_root or Path(__file__).resolve().parents[3])
    path = (root / filename).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        raise ValueError("Requested file must stay under add-on root.") from None
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def help_text(addon_root: str | None = None) -> str:
    return addon_file_text("HELP.md", addon_root) or addon_file_text(
        "README.md", addon_root
    )


def changelog_text(addon_root: str | None = None) -> str:
    return addon_file_text("CHANGELOG.md", addon_root)


def log_text(backend: AddonLogBackend | None = None, lines: int = 200) -> str:
    return (backend or AddonLogBackend()).tail(lines)


def show_text(title: str, text: str) -> bool:
    try:
        import xbmcgui  # type: ignore
    except Exception:
        return False
    try:
        xbmcgui.Dialog().textviewer(title, text)
        return True
    except Exception:
        return False


def clear_log(backend: AddonLogBackend | None = None, confirm: bool = False) -> bool:
    return (backend or AddonLogBackend()).clear(confirm=confirm)


def cleanup_settings(
    settings: KodiSettings | None = None,
    keys: Iterable[str] | None = None,
    confirm: bool = False,
) -> list[str]:
    return reset_settings(settings or KodiSettings(), keys=keys, confirm=confirm)
