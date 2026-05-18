from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import replace
from typing import Any

from .config import GlobalConfig, SearchOptions
from .errors import ProviderError
from .filters import allowed_by_options, release_filter_keywords, sort_results
from .models import SearchQuery, SourceResult
from .packs import is_season_pack, is_show_pack, with_host_dict
from .progress import (
    ProviderRunSummary,
    ScrapeProgress,
    callback_from_options,
    cancel_token_from_options,
    emit_progress,
    is_cancelled,
    merge_quality_counts,
    quality_counter,
)
from .provider import BaseProvider
from .validation import validate_result


class ScraperManager:
    def __init__(
        self,
        config: GlobalConfig | None = None,
        providers: Iterable[BaseProvider] | None = None,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        self.config = config or GlobalConfig()
        self.providers: list[BaseProvider] = []
        self.logger = logger
        for provider in providers or []:
            self.register(provider)

    @classmethod
    def from_defaults(cls, logger=None):
        return cls(logger=logger)

    def register(self, provider: BaseProvider):
        self.providers.append(provider)
        self.providers.sort(key=lambda item: item.config.priority)
        return provider

    def enabled_providers(self, options: SearchOptions):
        provider_ids = set(options.provider_ids)
        for provider in self.providers:
            if provider_ids and provider.id not in provider_ids:
                continue
            if not options.include_disabled and not provider.is_enabled():
                continue
            yield provider

    def search(self, query: SearchQuery, options=None):
        options = options or self.config.to_search_options()
        providers = [
            provider
            for provider in self.enabled_providers(options)
            if provider.supports(query)
        ]
        callback = callback_from_options(options)
        cancel_token = cancel_token_from_options(options)
        total = len(providers)
        emit_progress(callback, ScrapeProgress(event="started", total=total))
        if is_cancelled(cancel_token):
            emit_progress(
                callback,
                ScrapeProgress(event="cancelled", total=total, message="cancelled"),
            )
            return []

        if self._concurrent_enabled(options):
            results = self._search_concurrent(
                query, options, providers, callback, cancel_token
            )
        else:
            results = self._search_sequential(
                query, options, providers, callback, cancel_token
            )

        sorted_results = sort_results(results)[: options.max_results]
        emit_progress(
            callback,
            ScrapeProgress(
                event="finished",
                completed=total,
                total=total,
                accepted=len(sorted_results),
                raw=len(results),
                quality_counts=quality_counter(sorted_results),
            ),
        )
        return sorted_results

    def search_movie(
        self,
        title: str,
        year: int | None = None,
        imdb_id: str | None = None,
        tmdb_id: str | None = None,
        aliases: Iterable[str] | None = None,
        host_dict: dict[str, Any] | None = None,
        options: SearchOptions | None = None,
    ) -> list[SourceResult]:
        query = SearchQuery(
            title=title,
            media_type="movie",
            year=year,
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
            aliases=list(aliases or []),
        )
        return self.search(query, with_host_dict(options, host_dict))

    def search_episode(
        self,
        title: str,
        season: int,
        episode: int,
        year: int | None = None,
        imdb_id: str | None = None,
        tmdb_id: str | None = None,
        aliases: Iterable[str] | None = None,
        host_dict: dict[str, Any] | None = None,
        options: SearchOptions | None = None,
    ) -> list[SourceResult]:
        query = SearchQuery(
            title=title,
            media_type="episode",
            year=year,
            season=season,
            episode=episode,
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
            aliases=list(aliases or []),
        )
        return self.search(query, with_host_dict(options, host_dict))

    def search_season_pack(
        self,
        title: str,
        season: int,
        year: int | None = None,
        imdb_id: str | None = None,
        tmdb_id: str | None = None,
        aliases: Iterable[str] | None = None,
        host_dict: dict[str, Any] | None = None,
        options: SearchOptions | None = None,
    ) -> list[SourceResult]:
        query = SearchQuery(
            title=title,
            media_type="season",
            year=year,
            season=season,
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
            aliases=list(aliases or []),
        )
        results = self.search(query, with_host_dict(options, host_dict))
        return [result for result in results if is_season_pack(result, season)]

    def search_show_pack(
        self,
        title: str,
        total_seasons: int | None = None,
        year: int | None = None,
        imdb_id: str | None = None,
        tmdb_id: str | None = None,
        aliases: Iterable[str] | None = None,
        host_dict: dict[str, Any] | None = None,
        options: SearchOptions | None = None,
    ) -> list[SourceResult]:
        query = SearchQuery(
            title=title,
            media_type="show",
            year=year,
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
            aliases=list(aliases or []),
            extra={"total_seasons": total_seasons} if total_seasons is not None else {},
        )
        results = self.search(query, with_host_dict(options, host_dict))
        return [result for result in results if is_show_pack(result, total_seasons)]

    def _search_sequential(
        self, query, options, providers, callback, cancel_token
    ) -> list[SourceResult]:
        started = time.monotonic()
        results = []
        quality_counts: dict[str, int] = {}
        for index, provider in enumerate(providers, start=1):
            if self._deadline_expired(started, options) or is_cancelled(cancel_token):
                emit_progress(
                    callback,
                    ScrapeProgress(
                        event="cancelled", completed=index - 1, total=len(providers)
                    ),
                )
                break
            emit_progress(
                callback,
                ScrapeProgress(
                    event="provider_started",
                    completed=index - 1,
                    total=len(providers),
                    provider_id=provider.id,
                ),
            )
            provider_results, summary = self._run_provider(provider, query, options)
            results.extend(provider_results)
            quality_counts = merge_quality_counts(
                quality_counts, quality_counter(provider_results)
            )
            self._emit_provider_done(
                callback, summary, index, len(providers), quality_counts
            )
        return results

    def _search_concurrent(
        self, query, options, providers, callback, cancel_token
    ) -> list[SourceResult]:
        if not providers:
            return []
        started = time.monotonic()
        results: list[SourceResult] = []
        quality_counts: dict[str, int] = {}
        completed = 0
        max_workers = int(options.extra.get("max_workers") or len(providers))
        executor = ThreadPoolExecutor(max_workers=max(1, max_workers))
        futures: dict[Future, tuple[BaseProvider, float]] = {}
        timed_out: set[Future] = set()
        try:
            for provider in providers:
                if is_cancelled(cancel_token):
                    break
                emit_progress(
                    callback,
                    ScrapeProgress(
                        event="provider_started",
                        completed=completed,
                        total=len(providers),
                        provider_id=provider.id,
                    ),
                )
                futures[
                    executor.submit(self._run_provider, provider, query, options)
                ] = (
                    provider,
                    time.monotonic(),
                )

            pending = set(futures)
            while pending:
                if is_cancelled(cancel_token) or self._deadline_expired(
                    started, options
                ):
                    for future in pending:
                        future.cancel()
                    emit_progress(
                        callback,
                        ScrapeProgress(
                            event="cancelled",
                            completed=completed,
                            total=len(providers),
                            message="cancelled or timed out",
                        ),
                    )
                    break

                now = time.monotonic()
                provider_timeouts = [
                    future
                    for future in pending
                    if now - futures[future][1]
                    >= self._provider_timeout(futures[future][0], options)
                ]
                for future in provider_timeouts:
                    provider, provider_started = futures[future]
                    future.cancel()
                    pending.remove(future)
                    timed_out.add(future)
                    completed += 1
                    summary = ProviderRunSummary(
                        provider.id,
                        elapsed=now - provider_started,
                        timed_out=True,
                    )
                    self._emit_provider_done(
                        callback, summary, completed, len(providers), quality_counts
                    )

                if not pending:
                    break
                done, _ = wait(pending, timeout=0.05, return_when=FIRST_COMPLETED)
                for future in done:
                    pending.remove(future)
                    if future in timed_out:
                        continue
                    completed += 1
                    provider_results, summary = future.result()
                    results.extend(provider_results)
                    quality_counts = merge_quality_counts(
                        quality_counts, quality_counter(provider_results)
                    )
                    self._emit_provider_done(
                        callback, summary, completed, len(providers), quality_counts
                    )
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        return results

    def _run_provider(self, provider, query, options):
        started = time.monotonic()
        provider_options = replace(
            options, timeout=self._provider_timeout(provider, options)
        )
        try:
            provider_results = list(provider.search(query, provider_options) or [])
            normalized = self._normalize(provider_results, provider_options, query)
            return normalized, ProviderRunSummary(
                provider_id=provider.id,
                raw_count=len(provider_results),
                accepted_count=len(normalized),
                elapsed=time.monotonic() - started,
            )
        except Exception as exc:  # provider sandbox
            if self.config.fail_fast:
                raise ProviderError(provider.id, str(exc)) from exc
            self._log(f"Provider failed: {provider.id}: {exc}")
            return [], ProviderRunSummary(
                provider_id=provider.id,
                elapsed=time.monotonic() - started,
                error=str(exc),
            )

    def _normalize(self, provider_results, options, query):
        normalized = []
        for result in provider_results or []:
            if not isinstance(result, SourceResult):
                continue
            enriched = release_filter_keywords(result, options)
            if allowed_by_options(enriched, options) and validate_result(
                enriched, query
            ):
                normalized.append(enriched)
        return normalized

    def _concurrent_enabled(self, options: SearchOptions) -> bool:
        value = options.extra.get("concurrent")
        if value is None:
            return self.config.concurrent
        return bool(value)

    def _provider_timeout(
        self, provider: BaseProvider, options: SearchOptions
    ) -> float:
        value = options.extra.get("provider_timeout", options.timeout)
        if value is None:
            value = provider.config.timeout or self.config.provider_timeout
        return float(value)

    def _deadline_expired(self, started: float, options: SearchOptions) -> bool:
        budget = options.extra.get("scrape_timeout") or self.config.scrape_timeout
        return bool(budget and time.monotonic() - started >= float(budget))

    def _emit_provider_done(self, callback, summary, completed, total, quality_counts):
        event = "provider_finished"
        if summary.timed_out:
            event = "provider_timed_out"
        elif summary.cancelled:
            event = "provider_cancelled"
        elif summary.error:
            event = "provider_failed"
        emit_progress(
            callback,
            ScrapeProgress(
                event=event,
                completed=completed,
                total=total,
                provider_id=summary.provider_id,
                accepted=summary.accepted_count,
                raw=summary.raw_count,
                quality_counts=quality_counts,
                error=summary.error,
            ),
        )

    def _log(self, message):
        if self.logger:
            self.logger(message)
