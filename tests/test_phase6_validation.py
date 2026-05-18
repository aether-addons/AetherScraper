from __future__ import annotations

import unittest

from aetherscraper import (
    ProviderConfig,
    SearchOptions,
    SourceResult,
    ascii_clean,
    episode_matches,
    normalize_title,
    title_matches,
    validate_result,
    year_matches,
)
from aetherscraper.manager import ScraperManager
from aetherscraper.models import SearchQuery
from aetherscraper.provider import BaseProvider


class ValidationProvider(BaseProvider):
    config = ProviderConfig(
        id="validation",
        name="Validation Provider",
        enabled=True,
        pack_capable=True,
        media_types=["movie", "episode", "season", "show"],
    )

    def __init__(self, titles):
        super().__init__()
        self._titles = titles

    def search(self, query, options):
        return [
            SourceResult(
                provider=self.id,
                title=title,
                url=f"https://example.test/{index}",
                media_type=query.media_type,
                score=10 - index,
            )
            for index, title in enumerate(self._titles)
        ]


class Phase6ValidationTests(unittest.TestCase):
    def test_title_normalizer_removes_unprintable_ascii_noise(self) -> None:
        self.assertEqual(ascii_clean("Møvie\x00 Title\n"), "Mvie Title")
        self.assertEqual(
            normalize_title("Movie.Title.2024.S01E02.1080p.x265"), "movie title"
        )

    def test_alias_and_year_matching_with_alternate_years(self) -> None:
        self.assertTrue(
            title_matches(
                "Edge.of.Tomorrow.2014.1080p", "Live Die Repeat", ["Edge of Tomorrow"]
            )
        )
        self.assertFalse(
            title_matches(
                "Wrong.Movie.2014.1080p", "Live Die Repeat", ["Edge of Tomorrow"]
            )
        )
        self.assertTrue(year_matches("Movie.2023.1080p", 2024, [2023]))
        self.assertFalse(year_matches("Movie.2022.1080p", 2024, [2023]))
        self.assertTrue(year_matches("Movie.1080p", 2024, []))

    def test_sxxexx_episode_validator(self) -> None:
        self.assertTrue(episode_matches("Show.S02E07.1080p", 2, 7))
        self.assertFalse(episode_matches("Show.S02E08.1080p", 2, 7))

    def test_validate_result_by_media_type(self) -> None:
        self.assertTrue(
            validate_result(
                SourceResult(
                    "p", "Edge.of.Tomorrow.2014.1080p", "https://example.test"
                ),
                SearchQuery(
                    "Live Die Repeat", "movie", 2014, aliases=["Edge of Tomorrow"]
                ),
            )
        )
        self.assertTrue(
            validate_result(
                SourceResult("p", "Show.S01E02.1080p", "https://example.test"),
                SearchQuery("Show", "episode", season=1, episode=2),
            )
        )
        self.assertTrue(
            validate_result(
                SourceResult("p", "Show.S01E01-E08.1080p", "https://example.test"),
                SearchQuery("Show", "season", season=1),
            )
        )
        self.assertTrue(
            validate_result(
                SourceResult("p", "Show.S01-S03.1080p", "https://example.test"),
                SearchQuery("Show", "show", extra={"total_seasons": 3}),
            )
        )

    def test_manager_filters_mismatched_titles_years_and_episodes(self) -> None:
        provider = ValidationProvider(
            [
                "Big.Buck.Bunny.2008.1080p",
                "Big.Buck.Bunny.2009.1080p",
                "Wrong.Movie.2008.1080p",
            ]
        )
        manager = ScraperManager(providers=[provider])

        results = manager.search_movie(
            "Big Buck Bunny", year=2008, options=SearchOptions(include_disabled=True)
        )

        self.assertEqual(
            [result.title for result in results], ["Big.Buck.Bunny.2008.1080p"]
        )

        episode_provider = ValidationProvider(
            ["Show.S01E01.1080p", "Show.S01E02.1080p"]
        )
        episode_manager = ScraperManager(providers=[episode_provider])
        episode_results = episode_manager.search_episode(
            "Show", 1, 2, options=SearchOptions(include_disabled=True)
        )

        self.assertEqual(
            [result.title for result in episode_results], ["Show.S01E02.1080p"]
        )


if __name__ == "__main__":
    unittest.main()
