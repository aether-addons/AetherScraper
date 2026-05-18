from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

from .models import SourceResult

_QUALITY_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b(?:2160p|4k|uhd)\b", "4k"),
    (r"\b1080p\b", "1080p"),
    (r"\b720p\b", "720p"),
    (r"\b(?:576p|480p|360p|xvid|dvdrip|sd)\b", "sd"),
)
_CAM_RE = re.compile(r"\b(?:cam|camrip|hdcam|ts|telesync|tc|telecine)\b", re.I)
_SCR_RE = re.compile(r"\b(?:scr|screener|dvdscr|webscr|workprint)\b", re.I)
_HEVC_RE = re.compile(r"\b(?:h\.?265|x265|hevc)\b", re.I)
_AV1_RE = re.compile(r"\bav1\b", re.I)
_DV_RE = re.compile(r"\b(?:dv|dovi|dolby[ ._-]?vision)\b", re.I)
_HDR_RE = re.compile(r"\b(?:hdr10\+?|hdr|hlg)\b", re.I)
_TOKEN_SPLIT_RE = re.compile(r"[^a-z0-9+]+", re.I)

DEFAULT_UNDESIRABLE_KEYWORDS: tuple[str, ...] = (
    "3d",
    "camrip",
    "hardcoded",
    "hdcam",
    "korsub",
    "password",
    "r5",
    "sample",
    "telesync",
    "telecine",
    "upscaled",
    "watermark",
    "workprint",
)

_LANGUAGE_TOKENS: dict[str, set[str]] = {
    "en": {"en", "eng", "english"},
    "fr": {"fr", "fre", "french", "truefrench", "vff", "vfq"},
    "es": {"es", "spa", "spanish", "castellano", "latino"},
    "de": {"de", "ger", "german"},
    "it": {"it", "ita", "italian"},
    "pt": {"pt", "por", "portuguese", "brazilian"},
    "ru": {"ru", "rus", "russian"},
    "ja": {"ja", "jpn", "japanese"},
    "ko": {"ko", "kor", "korean"},
    "zh": {"zh", "chi", "chinese", "mandarin"},
}
_MULTI_LANGUAGE_TOKENS = {"multi", "multilang", "dual", "dualaudio", "multiaduio"}


@dataclass(frozen=True)
class ReleaseMetadata:
    quality: str = "unknown"
    is_cam: bool = False
    is_scr: bool = False
    codec: str = ""
    is_hevc: bool = False
    is_av1: bool = False
    hdr: str = ""
    has_dolby_vision: bool = False
    has_hdr: bool = False
    language: str = ""
    is_foreign_audio: bool = False
    undesirable_keywords: list[str] = field(default_factory=list)

    def as_metadata(self) -> dict[str, str]:
        values = {
            "detected_quality": self.quality,
            "is_cam": str(self.is_cam).lower(),
            "is_scr": str(self.is_scr).lower(),
            "codec": self.codec,
            "is_hevc": str(self.is_hevc).lower(),
            "is_av1": str(self.is_av1).lower(),
            "hdr": self.hdr,
            "has_dolby_vision": str(self.has_dolby_vision).lower(),
            "has_hdr": str(self.has_hdr).lower(),
            "detected_language": self.language,
            "is_foreign_audio": str(self.is_foreign_audio).lower(),
            "undesirable_keywords": ",".join(self.undesirable_keywords),
        }
        return {key: value for key, value in values.items() if value != ""}


def detect_quality(text: str) -> str:
    for pattern, quality in _QUALITY_PATTERNS:
        if re.search(pattern, text, re.I):
            return quality
    return "unknown"


def parse_keyword_list(value: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        raw = value
    else:
        raw = re.split(r"[,\n]", str(value))
    keywords = []
    seen = set()
    for item in raw:
        keyword = str(item).strip().lower()
        if keyword and keyword not in seen:
            seen.add(keyword)
            keywords.append(keyword)
    return keywords


def detect_language(text: str) -> str:
    tokens = {token.lower() for token in _TOKEN_SPLIT_RE.split(text) if token}
    if tokens & _MULTI_LANGUAGE_TOKENS:
        return "multi"
    for code, aliases in _LANGUAGE_TOKENS.items():
        if tokens & aliases:
            return code
    return ""


def inspect_release(
    title: str,
    *,
    language: str | None = None,
    undesirable_keywords: list[str] | tuple[str, ...] | None = None,
) -> ReleaseMetadata:
    text = title or ""
    keyword_list = parse_keyword_list(undesirable_keywords)
    matched_undesirable = [
        keyword for keyword in keyword_list if keyword in text.lower()
    ]
    detected_language = (language or "").strip().lower() or detect_language(text)
    is_foreign = detected_language not in {"", "en", "eng", "english", "multi"}
    is_hevc = bool(_HEVC_RE.search(text))
    is_av1 = bool(_AV1_RE.search(text))
    has_dv = bool(_DV_RE.search(text))
    has_hdr = bool(_HDR_RE.search(text))
    codec = "hevc" if is_hevc else "av1" if is_av1 else ""
    hdr = (
        "dv+hdr" if has_dv and has_hdr else "dv" if has_dv else "hdr" if has_hdr else ""
    )
    return ReleaseMetadata(
        quality=detect_quality(text),
        is_cam=bool(_CAM_RE.search(text)),
        is_scr=bool(_SCR_RE.search(text)),
        codec=codec,
        is_hevc=is_hevc,
        is_av1=is_av1,
        hdr=hdr,
        has_dolby_vision=has_dv,
        has_hdr=has_hdr,
        language=detected_language,
        is_foreign_audio=is_foreign,
        undesirable_keywords=matched_undesirable,
    )


def enrich_source_result(
    result: SourceResult,
    *,
    undesirable_keywords: list[str] | tuple[str, ...] | None = None,
) -> SourceResult:
    release = inspect_release(
        result.title,
        language=result.language,
        undesirable_keywords=undesirable_keywords,
    )
    quality = result.quality if result.quality != "unknown" else release.quality
    language = result.language or release.language or None
    metadata = dict(result.metadata)
    metadata.update(release.as_metadata())
    return replace(result, quality=quality, language=language, metadata=metadata)
