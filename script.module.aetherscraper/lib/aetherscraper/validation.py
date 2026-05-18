from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

from .models import SearchQuery, SourceResult
from .packs import is_season_pack, is_show_pack

_YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
_EPISODE_RE = re.compile(r"\b[Ss](\d{1,2})[ ._-]*[Ee](\d{1,3})\b")
_DROP_TOKENS_RE = re.compile(
    r"\b(?:"
    r"2160p|1080p|720p|480p|4k|uhd|hdrip|webrip|web-dl|webdl|bluray|brrip|dvdrip|hdtv|"
    r"x264|h264|x265|h265|hevc|av1|aac|dts|truehd|atmos|dolby|vision|hdr|dv|"
    r"proper|repack|extended|remastered|limited|complete|series|season"
    r")\b",
    re.IGNORECASE,
)
_SEASON_EPISODE_RE = re.compile(r"\b[Ss]\d{1,2}(?:[ ._-]*[Ee]\d{1,3})+\b")
_SEASON_ONLY_RE = re.compile(r"\b(?:[Ss]\d{1,2}|season[ ._-]*\d{1,2})\b", re.IGNORECASE)
_NON_WORD_RE = re.compile(r"[^a-z0-9]+")
_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class ValidationContext:
    """Normalized search data used to validate provider titles."""

    title: str
    aliases: tuple[str, ...] = ()
    year: int | None = None
    alternate_years: tuple[int, ...] = ()
    season: int | None = None
    episode: int | None = None
    media_type: str = "movie"
    total_seasons: int | None = None

    @property
    def accepted_years(self) -> set[int]:
        years = set(self.alternate_years)
        if self.year is not None:
            years.add(self.year)
        return years


def ascii_clean(value: str) -> str:
    """Return printable ASCII-ish text with unprintable chars removed."""
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    printable = "".join(ch if ch.isprintable() else " " for ch in ascii_text)
    return _SPACE_RE.sub(" ", printable).strip()


def normalize_title(value: str) -> str:
    """Normalize title for alias/source matching."""
    cleaned = ascii_clean(value).lower()
    cleaned = _SEASON_EPISODE_RE.sub(" ", cleaned)
    cleaned = _SEASON_ONLY_RE.sub(" ", cleaned)
    cleaned = _YEAR_RE.sub(" ", cleaned)
    cleaned = _DROP_TOKENS_RE.sub(" ", cleaned)
    cleaned = _NON_WORD_RE.sub(" ", cleaned)
    return _SPACE_RE.sub(" ", cleaned).strip()


def title_tokens(value: str) -> list[str]:
    return [token for token in normalize_title(value).split() if token]


def title_matches(source_title: str, title: str, aliases: Iterable[str] = ()) -> bool:
    """Return True when source title contains requested title or alias tokens."""
    source_tokens = title_tokens(source_title)
    if not source_tokens:
        return False
    source = " ".join(source_tokens)
    candidates = [title, *list(aliases or [])]
    for candidate in candidates:
        candidate_tokens = title_tokens(candidate)
        if not candidate_tokens:
            continue
        candidate_text = " ".join(candidate_tokens)
        if candidate_text in source:
            return True
    return False


def extract_years(value: str) -> set[int]:
    return {int(year) for year in _YEAR_RE.findall(value or "")}


def year_matches(
    source_title: str, year: int | None, alternate_years: Iterable[int] = ()
) -> bool:
    accepted = {int(item) for item in alternate_years or []}
    if year is not None:
        accepted.add(int(year))
    if not accepted:
        return True
    found = extract_years(source_title)
    return not found or bool(found & accepted)


def episode_matches(source_title: str, season: int, episode: int) -> bool:
    for found_season, found_episode in _EPISODE_RE.findall(source_title or ""):
        if int(found_season) == int(season) and int(found_episode) == int(episode):
            return True
    return False


def context_from_query(query: SearchQuery) -> ValidationContext:
    alternate_years = tuple(
        int(value)
        for value in query.extra.get("alternate_years", ())
        if value is not None
    )
    return ValidationContext(
        title=query.title,
        aliases=tuple(query.aliases or ()),
        year=query.year,
        alternate_years=alternate_years,
        season=query.season,
        episode=query.episode,
        media_type=query.media_type,
        total_seasons=query.extra.get("total_seasons"),
    )


def validate_movie_result(result: SourceResult, context: ValidationContext) -> bool:
    return title_matches(result.title, context.title, context.aliases) and year_matches(
        result.title, context.year, context.alternate_years
    )


def validate_episode_result(result: SourceResult, context: ValidationContext) -> bool:
    if context.season is None or context.episode is None:
        return False
    return (
        title_matches(result.title, context.title, context.aliases)
        and year_matches(result.title, context.year, context.alternate_years)
        and episode_matches(result.title, context.season, context.episode)
    )


def validate_season_pack_result(
    result: SourceResult, context: ValidationContext
) -> bool:
    if context.season is None:
        return False
    return (
        title_matches(result.title, context.title, context.aliases)
        and year_matches(result.title, context.year, context.alternate_years)
        and is_season_pack(result, context.season)
    )


def validate_show_pack_result(result: SourceResult, context: ValidationContext) -> bool:
    return (
        title_matches(result.title, context.title, context.aliases)
        and year_matches(result.title, context.year, context.alternate_years)
        and is_show_pack(result, context.total_seasons)
    )


def validate_result(result: SourceResult, query: SearchQuery) -> bool:
    """Validate provider result against query title/year/episode/pack context."""
    context = context_from_query(query)
    if context.media_type == "movie":
        return validate_movie_result(result, context)
    if context.media_type == "episode":
        return validate_episode_result(result, context)
    if context.media_type == "season":
        return validate_season_pack_result(result, context)
    if context.media_type == "show":
        return validate_show_pack_result(result, context)
    return title_matches(result.title, context.title, context.aliases)
