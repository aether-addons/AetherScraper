from __future__ import annotations

import threading
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import (  # noqa: UP035 - Kodi Python may lack collections.abc generics
    Any,
    Callable,
    cast,
)

from .config import SearchOptions
from .models import SourceResult

ProgressCallback = Callable[["ScrapeProgress"], None]


@dataclass(frozen=True)
class ScrapeProgress:
    event: str
    completed: int = 0
    total: int = 0
    provider_id: str | None = None
    accepted: int = 0
    raw: int = 0
    quality_counts: dict[str, int] = field(default_factory=dict)
    message: str = ""
    error: str | None = None


@dataclass(frozen=True)
class ProviderRunSummary:
    provider_id: str
    raw_count: int = 0
    accepted_count: int = 0
    elapsed: float = 0.0
    timed_out: bool = False
    cancelled: bool = False
    error: str | None = None


@dataclass(frozen=True)
class ScrapeRunSummary:
    completed: int = 0
    total: int = 0
    accepted: int = 0
    raw: int = 0
    elapsed: float = 0.0
    timed_out: bool = False
    cancelled: bool = False
    quality_counts: dict[str, int] = field(default_factory=dict)
    provider_summaries: list[ProviderRunSummary] = field(default_factory=list)


class CancelToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def is_cancelled(self) -> bool:
        return self.cancelled


def callback_from_options(options: SearchOptions) -> ProgressCallback | None:
    callback = options.extra.get("progress_callback")
    if callable(callback):
        return cast(ProgressCallback, callback)
    return None


def cancel_token_from_options(options: SearchOptions) -> CancelToken | None:
    token = options.extra.get("cancel_token")
    if token is not None and hasattr(token, "cancelled"):
        return token
    return None


def is_cancelled(token: Any | None) -> bool:
    if token is None:
        return False
    cancelled = getattr(token, "cancelled", None)
    if isinstance(cancelled, bool):
        return cancelled
    checker = getattr(token, "is_cancelled", None)
    if callable(checker):
        return bool(checker())
    return False


def quality_counter(results: Iterable[SourceResult]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for result in results:
        quality = result.quality or result.metadata.get("quality") or "unknown"
        counts[str(quality)] += 1
    return dict(counts)


def merge_quality_counts(*items: dict[str, int]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in items:
        counts.update(item)
    return dict(counts)


def emit_progress(callback: ProgressCallback | None, progress: ScrapeProgress) -> None:
    if callback is None:
        return
    callback(progress)
