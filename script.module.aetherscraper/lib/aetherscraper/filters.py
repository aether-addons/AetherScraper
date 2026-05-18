from __future__ import annotations

from .config import SearchOptions
from .models import SourceResult
from .release import DEFAULT_UNDESIRABLE_KEYWORDS, enrich_source_result

_QUALITY_RANK = {
    "unknown": 0,
    "sd": 1,
    "480p": 2,
    "720p": 3,
    "1080p": 4,
    "1440p": 5,
    "4k": 6,
    "2160p": 6,
}


def quality_rank(value):
    return _QUALITY_RANK.get(str(value).lower(), 0)


def release_filter_keywords(
    result: SourceResult, options: SearchOptions
) -> SourceResult:
    keywords = []
    if options.use_default_undesirables:
        keywords.extend(DEFAULT_UNDESIRABLE_KEYWORDS)
    keywords.extend(options.undesirable_keywords)
    return enrich_source_result(result, undesirable_keywords=keywords)


def _metadata_bool(result: SourceResult, key: str) -> bool:
    return str(result.metadata.get(key, "")).lower() == "true"


def allowed_by_options(result: SourceResult, options: SearchOptions):
    quality_ok = not options.min_quality or quality_rank(
        result.quality
    ) >= quality_rank(options.min_quality)
    language_ok = not (
        options.languages
        and result.language
        and result.language not in options.languages
    )
    release_ok = not (
        (not options.allow_hevc and _metadata_bool(result, "is_hevc"))
        or (not options.allow_av1 and _metadata_bool(result, "is_av1"))
        or (
            not options.allow_dolby_vision
            and _metadata_bool(result, "has_dolby_vision")
        )
        or (not options.allow_hdr and _metadata_bool(result, "has_hdr"))
        or (
            not options.allow_foreign_audio
            and _metadata_bool(result, "is_foreign_audio")
        )
        or bool(result.metadata.get("undesirable_keywords"))
    )
    return quality_ok and language_ok and release_ok


def sort_results(results):
    return sorted(
        results, key=lambda item: (item.score, quality_rank(item.quality)), reverse=True
    )
