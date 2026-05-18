from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass

from .config import SearchOptions
from .models import SearchQuery
from .provider import BaseProvider
from .support import redact_secrets


@dataclass(frozen=True)
class ProviderHealthResult:
    provider_id: str
    provider_name: str
    enabled: bool
    supported: bool
    ok: bool
    elapsed: float
    result_count: int = 0
    error: str = ""


@dataclass(frozen=True)
class HealthCheckSummary:
    total: int
    ok: int
    failed: int
    skipped: int
    results: list[ProviderHealthResult]


def run_provider_health_checks(
    providers: Iterable[BaseProvider],
    query: SearchQuery | None = None,
    options: SearchOptions | None = None,
    include_disabled: bool = True,
) -> HealthCheckSummary:
    health_query = query or SearchQuery(title="Health Check", media_type="movie")
    health_options = options or SearchOptions(timeout=5, include_disabled=True)
    results: list[ProviderHealthResult] = []
    for provider in providers:
        started = time.monotonic()
        enabled = provider.is_enabled()
        supported = provider.supports(health_query)
        if (not enabled and not include_disabled) or not supported:
            results.append(
                ProviderHealthResult(
                    provider_id=provider.id,
                    provider_name=provider.name,
                    enabled=enabled,
                    supported=supported,
                    ok=False,
                    elapsed=time.monotonic() - started,
                    error="disabled" if not enabled else "unsupported query",
                )
            )
            continue
        try:
            provider_results = list(provider.search(health_query, health_options) or [])
        except Exception as exc:  # provider sandbox for diagnostics
            results.append(
                ProviderHealthResult(
                    provider_id=provider.id,
                    provider_name=provider.name,
                    enabled=enabled,
                    supported=supported,
                    ok=False,
                    elapsed=time.monotonic() - started,
                    error=redact_secrets(exc),
                )
            )
            continue
        results.append(
            ProviderHealthResult(
                provider_id=provider.id,
                provider_name=provider.name,
                enabled=enabled,
                supported=supported,
                ok=True,
                elapsed=time.monotonic() - started,
                result_count=len(provider_results),
            )
        )
    ok_count = sum(1 for result in results if result.ok)
    skipped = sum(
        1 for result in results if result.error in {"disabled", "unsupported query"}
    )
    failed = len(results) - ok_count - skipped
    return HealthCheckSummary(
        total=len(results), ok=ok_count, failed=failed, skipped=skipped, results=results
    )
