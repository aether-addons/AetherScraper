from __future__ import annotations

import re
from dataclasses import replace
from typing import Any

from .config import SearchOptions
from .models import SourceResult

_EPISODE_RE = re.compile(r"\b[Ss](\d{1,2})[ ._-]*[Ee](\d{1,3})\b")
_EPISODE_CHAIN_RE = re.compile(r"\b[Ss](\d{1,2})(?:[ ._-]*[Ee](\d{1,3})){2,}")
_EPISODE_AFTER_S_RE = re.compile(r"[Ee](\d{1,3})")
_EPISODE_RANGE_RE = re.compile(
    r"\b[Ss](\d{1,2})[ ._-]*[Ee](\d{1,3})\s*(?:-|to|through|thru|~)\s*(?:[Ss]\d{1,2}[ ._-]*)?[Ee]?(\d{1,3})\b",
    re.IGNORECASE,
)
_SEASON_TOKEN_RE = re.compile(r"\b[Ss](\d{1,2})\b")
_SEASON_RANGE_RE = re.compile(
    r"\b(?:[Ss]easons?|[Ss])\s*(\d{1,2})\s*(?:-|to|through|thru|~)\s*(\d{1,2})\b"
)
_COMPLETE_SERIES_RE = re.compile(
    r"\b(complete\s+(?:series|show|collection)|all\s+seasons|full\s+series)\b",
    re.IGNORECASE,
)


def with_host_dict(
    options: SearchOptions | None, host_dict: dict[str, Any] | None
) -> SearchOptions | None:
    """Return options carrying legacy Magneto-style hostDict data."""
    if not host_dict:
        return options
    base = options or SearchOptions()
    extra = dict(base.extra)
    extra["host_dict"] = host_dict
    return replace(base, extra=extra)


def detect_episode_range(
    title: str, season: int | None = None
) -> tuple[int, int] | None:
    """Detect min/max episode numbers for one season release title."""
    if not title:
        return None

    range_match = _EPISODE_RANGE_RE.search(title)
    if range_match:
        found_season = int(range_match.group(1))
        if season is not None and found_season != season:
            return None
        start = int(range_match.group(2))
        end = int(range_match.group(3))
        return (min(start, end), max(start, end))

    chain_match = _EPISODE_CHAIN_RE.search(title)
    if chain_match:
        found_season = int(chain_match.group(1))
        if season is not None and found_season != season:
            return None
        episodes = [
            int(value) for value in _EPISODE_AFTER_S_RE.findall(chain_match.group(0))
        ]
        if episodes:
            return (min(episodes), max(episodes))

    episodes = []
    for found_season, episode in _EPISODE_RE.findall(title):
        if season is None or int(found_season) == season:
            episodes.append(int(episode))
    if episodes:
        return (min(episodes), max(episodes))
    return None


def is_season_pack(result: SourceResult, season: int) -> bool:
    """Return True when result looks like full/partial season pack for season."""
    title = result.title or ""
    if re.search(rf"\b[Ss]{season:02d}\b", title) or re.search(
        rf"\b[Ss]eason[ ._-]*0?{season}\b", title, re.IGNORECASE
    ):
        return True
    episode_range = detect_episode_range(title, season)
    return bool(episode_range and episode_range[0] != episode_range[1])


def detect_season_range(title: str) -> tuple[int, int] | None:
    """Detect min/max seasons included in show-pack title."""
    if not title:
        return None
    if _COMPLETE_SERIES_RE.search(title):
        return (1, 999)
    range_match = _SEASON_RANGE_RE.search(title)
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        return (min(start, end), max(start, end))
    seasons = [int(value) for value in _SEASON_TOKEN_RE.findall(title)]
    if seasons:
        return (min(seasons), max(seasons))
    return None


def is_show_pack(result: SourceResult, total_seasons: int | None = None) -> bool:
    """Return True when result looks like multi-season or complete-show pack."""
    title = result.title or ""
    if _COMPLETE_SERIES_RE.search(title):
        return True
    season_range = detect_season_range(title)
    if season_range is None:
        return False
    start, end = season_range
    if total_seasons is not None:
        return start <= 1 and end >= total_seasons
    return end > start
