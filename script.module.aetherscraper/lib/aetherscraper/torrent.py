from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse

from .models import SourceResult

_HEX_INFO_HASH_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_BASE32_INFO_HASH_RE = re.compile(r"^[A-Z2-7]{32}$", re.IGNORECASE)
_INFO_HASH_IN_TEXT_RE = re.compile(
    r"(?:urn:btih:)?(?P<hash>[0-9a-fA-F]{40}|[A-Z2-7]{32})", re.IGNORECASE
)
_SIZE_RE = re.compile(
    r"(?P<value>\d+(?:[,.]\d+)*)(?:\s*)(?P<unit>bytes?|kib|kb|k|mib|mb|m|gib|gb|g|tib|tb|t|b)",
    re.IGNORECASE,
)
_RELEASE_TOKEN_RE = re.compile(
    r"\b(2160p|1080p|720p|480p|4k|uhd|hdr|dv|webrip|web-dl|webdl|bluray|brrip|"
    r"xvid|x264|x265|h264|h265|hevc|av1|aac|dts|truehd|atmos|repack|proper)\b",
    re.IGNORECASE,
)
_SPACING_RE = re.compile(r"\s+")

_SIZE_UNITS = {
    "b": 1,
    "byte": 1,
    "bytes": 1,
    "k": 1000,
    "kb": 1000,
    "m": 1000**2,
    "mb": 1000**2,
    "g": 1000**3,
    "gb": 1000**3,
    "t": 1000**4,
    "tb": 1000**4,
    "kib": 1024,
    "mib": 1024**2,
    "gib": 1024**3,
    "tib": 1024**4,
}

_SIZE_LABELS = (
    (1024**4, "TB"),
    (1024**3, "GB"),
    (1024**2, "MB"),
    (1024, "KB"),
)
_MAX_VIDEO_SIZE_BYTES = 50 * 1024**4
_NUMERIC_SIZE_RE = re.compile(r"^\d+(?:[,.]\d+)?$")


@dataclass(frozen=True)
class TorrentConfig:
    require_info_hash: bool = True
    allow_private_trackers: bool = False
    min_seeders: int = 0
    max_size: int | None = None
    trackers: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TorrentItem:
    title: str
    magnet: str = ""
    torrent_url: str = ""
    info_hash: str = ""
    quality: str = "unknown"
    size: int | None = None
    seeders: int | None = None
    leechers: int | None = None
    language: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


def _parse_number(value: str) -> float:
    text = value.strip()
    if "," in text and "." in text:
        text = text.replace(",", "")
    elif "," in text:
        parts = text.split(",")
        text = "".join(parts) if len(parts[-1]) == 3 else text.replace(",", ".")
    return float(text)


def parse_size(value: Any) -> int | None:
    """Parse common torrent size strings to bytes."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return _valid_size(value)
    if isinstance(value, float):
        if value < 0:
            return None
        size = int(value * _SIZE_UNITS["gb"]) if not value.is_integer() else int(value)
        return _valid_size(size)

    text = str(value).strip()
    if not text:
        return None
    match = _SIZE_RE.search(text)
    if not match:
        if not _NUMERIC_SIZE_RE.fullmatch(text):
            return None
        return _valid_size(int(_parse_number(text)))

    number = _parse_number(match.group("value"))
    unit = match.group("unit").lower()
    return _valid_size(int(number * _SIZE_UNITS[unit]))


def parse_size_candidates(*values: Any) -> int | None:
    """Return first parseable size from ordered provider fields/text."""
    for value in values:
        parsed = parse_size(value)
        if parsed is not None:
            return parsed
    return None


def _valid_size(value: int) -> int | None:
    if value < 0 or value > _MAX_VIDEO_SIZE_BYTES:
        return None
    return value


def bytes_to_size(value: int | None) -> str:
    """Format bytes with binary units for display/docs/tests."""
    if value is None:
        return ""
    if value < 0:
        return ""
    for factor, label in _SIZE_LABELS:
        if value >= factor:
            return f"{value / factor:.2f} {label}"
    return f"{value} B"


def base32_to_hex_infohash(value: str) -> str:
    """Convert BTIH base32 infohash to lowercase hex."""
    text = value.strip().upper()
    if not _BASE32_INFO_HASH_RE.fullmatch(text):
        raise ValueError("info hash must be 32 chars of base32")
    try:
        return base64.b32decode(text).hex()
    except binascii.Error as exc:
        raise ValueError("invalid base32 info hash") from exc


def normalize_info_hash(value: str) -> str:
    """Return lowercase 40-char hex infohash from hex/base32 input."""
    text = value.strip()
    if text.lower().startswith("urn:btih:"):
        text = text[9:]
    if _HEX_INFO_HASH_RE.fullmatch(text):
        return text.lower()
    if _BASE32_INFO_HASH_RE.fullmatch(text):
        return base32_to_hex_infohash(text)
    return ""


def extract_info_hash(value: str) -> str:
    """Extract first hex/base32 BTIH hash from magnet URI or free text."""
    if not value:
        return ""
    if value.startswith("magnet:"):
        parsed = parse_magnet(value)
        return str(parsed.get("info_hash", ""))
    match = _INFO_HASH_IN_TEXT_RE.search(value)
    return normalize_info_hash(match.group("hash")) if match else ""


def parse_magnet(uri: str) -> dict[str, Any]:
    parsed = urlparse(uri)
    if parsed.scheme != "magnet":
        return {}
    values = parse_qs(parsed.query)
    flat = {key: [unquote(item) for item in value] for key, value in values.items()}
    xt_values = flat.get("xt", [])
    info_hash = ""
    for value in xt_values:
        if value.lower().startswith("urn:btih:"):
            info_hash = normalize_info_hash(value)
            break
    return {
        "name": flat.get("dn", [""])[0],
        "info_hash": info_hash,
        "trackers": flat.get("tr", []),
        "raw": flat,
    }


def build_magnet(
    info_hash: str, name: str = "", trackers: list[str] | None = None
) -> str:
    normalized_hash = normalize_info_hash(info_hash) or info_hash.strip()
    parts = [f"xt=urn:btih:{quote(normalized_hash)}"]
    if name:
        parts.append(f"dn={quote(name)}")
    for tracker in trackers or []:
        parts.append(f"tr={quote(tracker)}")
    return "magnet:?" + "&".join(parts)


def clean_release_title(value: str) -> str:
    """Remove common release noise while preserving readable title text."""
    text = re.sub(r"https?://\S+", " ", value or "")
    text = re.sub(r"\.(mkv|mp4|avi|mov|wmv|torrent)$", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[._]+", " ", text)
    text = re.sub(r"[\[\](){}]", " ", text)
    text = _RELEASE_TOKEN_RE.sub(" ", text)
    text = re.sub(r"\bS\d{1,2}E\d{1,2}\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d{3,4}MB\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+-\s*", " ", text)
    return _SPACING_RE.sub(" ", text).strip(" -_")


def _first_present(
    data: dict[str, Any], keys: tuple[str, ...], default: Any = ""
) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return default


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _string_metadata(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items() if item is not None}


def normalize_torrent_item(data: dict[str, Any]) -> TorrentItem:
    """Normalize inconsistent provider torrent fields into TorrentItem."""
    title = str(_first_present(data, ("title", "name", "release_title"), ""))
    magnet = str(_first_present(data, ("magnet", "magnet_uri", "uri"), ""))
    torrent_url = str(
        _first_present(data, ("torrent_url", "torrent", "url", "link"), "")
    )
    raw_hash = str(_first_present(data, ("info_hash", "hash", "btih"), ""))
    info_hash = normalize_info_hash(raw_hash) or extract_info_hash(magnet)
    size = parse_size_candidates(
        data.get("size_bytes"),
        data.get("filesize"),
        data.get("file_size"),
        data.get("size"),
        title,
    )
    metadata = _string_metadata(data.get("metadata"))
    if info_hash:
        metadata.setdefault("info_hash", info_hash)
    if title:
        metadata.setdefault("clean_title", clean_release_title(title))

    return TorrentItem(
        title=title,
        magnet=magnet,
        torrent_url=torrent_url,
        info_hash=info_hash,
        quality=str(_first_present(data, ("quality", "resolution"), "unknown")),
        size=size,
        seeders=_optional_int(_first_present(data, ("seeders", "seeds", "seed"), None)),
        leechers=_optional_int(
            _first_present(data, ("leechers", "leeches", "peers"), None)
        ),
        language=_first_present(data, ("language", "lang"), None),
        metadata=metadata,
    )


def normalize_torrent_items(items: list[dict[str, Any]]) -> list[TorrentItem]:
    return [normalize_torrent_item(item) for item in items if isinstance(item, dict)]


def torrent_to_source(provider_id: str, item: TorrentItem) -> SourceResult:
    parsed = parse_magnet(item.magnet) if item.magnet else {}
    info_hash = item.info_hash or str(parsed.get("info_hash", ""))
    url = (
        item.magnet
        or (build_magnet(info_hash, item.title) if info_hash else "")
        or item.torrent_url
    )
    metadata = dict(item.metadata)
    metadata.update(
        {
            "info_hash": info_hash,
            "seeders": "" if item.seeders is None else str(item.seeders),
            "leechers": "" if item.leechers is None else str(item.leechers),
            "torrent_url": item.torrent_url,
        }
    )
    if item.size is not None:
        metadata.setdefault("size_label", bytes_to_size(item.size))
    return SourceResult(
        provider=provider_id,
        title=item.title,
        url=url,
        quality=item.quality,
        media_type="torrent",
        size=item.size,
        language=item.language,
        score=float(item.seeders or 0),
        direct=False,
        metadata=metadata,
    )
