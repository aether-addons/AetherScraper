from __future__ import annotations

import unittest

from aetherscraper import (
    ProviderConfig,
    SearchOptions,
    SourceResult,
    detect_episode_range,
    detect_season_range,
    is_season_pack,
    is_show_pack,
)
from aetherscraper.manager import ScraperManager
from aetherscraper.provider import BaseProvider


class ContractProvider(BaseProvider):
    config = ProviderConfig(
        id="contract",
        name="Contract Provider",
        enabled=True,
        pack_capable=True,
        media_types=["movie", "episode", "season", "show"],
    )

    def __init__(self, results):
        super().__init__()
        self.calls = []
        self._results = results

    def search(self, query, options):
        self.calls.append((query, options))
        return [
            SourceResult(
                provider=self.id,
                title=title,
                url=f"https://example.test/{index}",
                media_type=query.media_type,
                score=10 - index,
            )
            for index, title in enumerate(self._results)
        ]


class Phase5SearchContractTests(unittest.TestCase):
    def test_movie_and_episode_adapters_build_query_and_preserve_host_dict(
        self,
    ) -> None:
        provider = ContractProvider(["Big Buck Bunny 2008 1080p", "Show.S01E02.1080p"])
        manager = ScraperManager(providers=[provider])

        movie_results = manager.search_movie(
            "Big Buck Bunny",
            year=2008,
            aliases=["BBB"],
            host_dict={"torrent": ["magnet"]},
            options=SearchOptions(include_disabled=True),
        )
        episode_results = manager.search_episode(
            "Show",
            season=1,
            episode=2,
            host_dict={"direct": ["https"]},
            options=SearchOptions(include_disabled=True),
        )

        self.assertEqual(len(movie_results), 1)
        self.assertEqual(provider.calls[0][0].media_type, "movie")
        self.assertEqual(provider.calls[0][0].year, 2008)
        self.assertEqual(provider.calls[0][0].aliases, ["BBB"])
        self.assertEqual(
            provider.calls[0][1].extra["host_dict"], {"torrent": ["magnet"]}
        )
        self.assertEqual(len(episode_results), 1)
        self.assertEqual(provider.calls[1][0].media_type, "episode")
        self.assertEqual(provider.calls[1][0].season, 1)
        self.assertEqual(provider.calls[1][0].episode, 2)
        self.assertEqual(provider.calls[1][1].extra["host_dict"], {"direct": ["https"]})

    def test_episode_range_detection_for_season_packs(self) -> None:
        self.assertEqual(detect_episode_range("Show.S01E01-E08.1080p", 1), (1, 8))
        self.assertEqual(detect_episode_range("Show.S01E01E02E03", 1), (1, 3))
        self.assertIsNone(detect_episode_range("Show.S02E01-E08", 1))
        self.assertTrue(
            is_season_pack(
                SourceResult("p", "Show Season 1 1080p", "https://example.test"), 1
            )
        )

    def test_season_pack_search_filters_non_pack_results(self) -> None:
        provider = ContractProvider(
            [
                "Show.S01E01.1080p",
                "Show.S01E01-E08.1080p",
                "Show.S02.Complete.1080p",
                "Show.Season.1.1080p",
            ]
        )
        manager = ScraperManager(providers=[provider])

        results = manager.search_season_pack(
            "Show", season=1, options=SearchOptions(include_disabled=True)
        )

        self.assertEqual(
            [result.title for result in results],
            ["Show.S01E01-E08.1080p", "Show.Season.1.1080p"],
        )

    def test_total_season_aware_show_pack_filtering(self) -> None:
        self.assertEqual(detect_season_range("Show S01-S03 1080p"), (1, 3))
        self.assertTrue(
            is_show_pack(
                SourceResult("p", "Show Complete Series 1080p", "https://example.test"),
                total_seasons=5,
            )
        )
        provider = ContractProvider(
            [
                "Show S01 1080p",
                "Show S01-S02 1080p",
                "Show S01-S03 1080p",
                "Show Complete Series 1080p",
            ]
        )
        manager = ScraperManager(providers=[provider])

        results = manager.search_show_pack(
            "Show", total_seasons=3, options=SearchOptions(include_disabled=True)
        )

        self.assertEqual(
            [result.title for result in results],
            ["Show S01-S03 1080p", "Show Complete Series 1080p"],
        )


if __name__ == "__main__":
    unittest.main()
