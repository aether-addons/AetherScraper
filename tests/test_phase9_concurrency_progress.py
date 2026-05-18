from __future__ import annotations

import time
import unittest

from aetherscraper import (
    BaseProvider,
    CancelToken,
    GlobalConfig,
    ProviderConfig,
    ScraperManager,
    SearchOptions,
    SearchQuery,
    SourceResult,
)
from aetherscraper.kodi.settings import KodiSettings


class SlowProvider(BaseProvider):
    def __init__(self, provider_id: str, delay: float, quality: str = "1080p") -> None:
        super().__init__(
            ProviderConfig(
                id=provider_id,
                name=provider_id,
                enabled=True,
                priority=10,
                timeout=1,
            )
        )
        self.delay = delay
        self.quality = quality
        self.seen_timeout: float | None = None

    def search(self, query, options):
        self.seen_timeout = options.timeout
        time.sleep(self.delay)
        return [
            SourceResult(
                provider=self.id,
                title=f"{query.title} 2008 {self.quality}",
                url=f"https://example.invalid/{self.id}",
                quality=self.quality,
                media_type=query.media_type,
            )
        ]


class Phase9ConcurrencyProgressTests(unittest.TestCase):
    def test_concurrent_runner_uses_parallel_providers_and_reports_progress(self):
        events = []
        manager = ScraperManager(
            config=GlobalConfig(concurrent=True),
            providers=[
                SlowProvider("one", 0.12, "720p"),
                SlowProvider("two", 0.12, "1080p"),
            ],
        )
        started = time.monotonic()

        results = manager.search(
            SearchQuery("Big Buck Bunny", year=2008),
            SearchOptions(
                extra={"progress_callback": events.append, "scrape_timeout": 2}
            ),
        )

        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 0.22)
        self.assertEqual({result.provider for result in results}, {"one", "two"})
        self.assertIn("started", [event.event for event in events])
        self.assertIn("finished", [event.event for event in events])
        self.assertEqual(events[-1].quality_counts["720p"], 1)
        self.assertEqual(events[-1].quality_counts["1080p"], 1)

    def test_per_provider_timeout_marks_slow_provider(self):
        events = []
        fast = SlowProvider("fast", 0.01)
        slow = SlowProvider("slow", 0.2)
        manager = ScraperManager(
            config=GlobalConfig(concurrent=True), providers=[fast, slow]
        )

        results = manager.search(
            SearchQuery("Big Buck Bunny", year=2008),
            SearchOptions(
                extra={
                    "progress_callback": events.append,
                    "provider_timeout": 0.05,
                    "scrape_timeout": 1,
                }
            ),
        )

        self.assertEqual([result.provider for result in results], ["fast"])
        self.assertEqual(fast.seen_timeout, 0.05)
        self.assertIn("provider_timed_out", [event.event for event in events])

    def test_cancel_token_stops_before_scrape(self):
        events = []
        token = CancelToken()
        token.cancel()
        manager = ScraperManager(providers=[SlowProvider("one", 0.01)])

        results = manager.search(
            SearchQuery("Big Buck Bunny", year=2008),
            SearchOptions(
                extra={"cancel_token": token, "progress_callback": events.append}
            ),
        )

        self.assertEqual(results, [])
        self.assertIn("cancelled", [event.event for event in events])

    def test_kodi_settings_enable_concurrent_global_config(self):
        settings = KodiSettings(fallback={"concurrent_scraping": "true"})
        config = GlobalConfig.from_kodi_settings(settings)

        self.assertTrue(config.concurrent)


if __name__ == "__main__":
    unittest.main()
