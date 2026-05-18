from __future__ import annotations

import unittest

import aetherscraper
from aetherscraper import SearchOptions, SourceResult
from aetherscraper.config import ProviderConfig
from aetherscraper.external import (
    UmbrellaSourceAdapter,
    _adapter_class,
    _filter_summaries_by_folders,
    _provider_summaries,
    _source_to_umbrella,
    sources,
)
from aetherscraper.provider import BaseProvider


class FakeManager:
    def __init__(self):
        self.calls = []

    def search_movie(self, *args, **kwargs):
        self.calls.append(("movie", args, kwargs))
        return [
            SourceResult(
                provider="fake_torrent",
                title="Big Buck Bunny 2008 1080p x265 HDR",
                url="magnet:?xt=urn:btih:abcdef",
                quality="1080p",
                size=2 * 1024 * 1024 * 1024,
                language="en",
                metadata={"info_hash": "abcdef", "codec": "HEVC", "hdr": "HDR"},
            )
        ]

    def search_episode(self, *args, **kwargs):
        self.calls.append(("episode", args, kwargs))
        return [
            SourceResult(
                provider="fake_direct",
                title="Example Show S01E02 720p",
                url="https://example.test/video.mkv",
                quality="720p",
                direct=True,
                language="en",
            )
        ]

    def search_season_pack(self, *args, **kwargs):
        self.calls.append(("season", args, kwargs))
        return [
            SourceResult(
                provider="fake_torrent",
                title="Example Show S01E01-E08 1080p",
                url="magnet:?xt=urn:btih:1234",
                quality="1080p",
                metadata={"episode_start": "1", "episode_end": "8"},
            )
        ]

    def search_show_pack(self, *args, **kwargs):
        self.calls.append(("show", args, kwargs))
        return [
            SourceResult(
                provider="fake_torrent",
                title="Example Show Complete Series 1080p",
                url="magnet:?xt=urn:btih:5678",
                quality="1080p",
                metadata={"last_season": "3"},
            )
        ]


class SummaryProvider(BaseProvider):
    config = ProviderConfig(
        id="summary",
        name="Summary",
        enabled=True,
        priority=5,
        provider_type="torrent",
        pack_capable=True,
    )

    def search(self, query, options):
        return []


class Phase135UmbrellaBridgeTests(unittest.TestCase):
    def test_importable_sources_surface_matches_umbrella_validation(self) -> None:
        self.assertTrue(callable(aetherscraper.sources))
        provider_entries = aetherscraper.sources(ret_all=True)
        self.assertTrue(provider_entries)
        provider_id, provider_class = provider_entries[0]
        self.assertIsInstance(provider_id, str)
        self.assertTrue(hasattr(provider_class, "hasMovies"))
        self.assertTrue(hasattr(provider_class, "hasEpisodes"))
        self.assertTrue(hasattr(provider_class, "pack_capable"))

    def test_sources_supports_magneto_signature_and_fenlight_folders(self) -> None:
        self.assertIsInstance(
            sources(specified_folders=["torrents"], ret_all=True), list
        )
        self.assertIsInstance(sources(specified_folders=None, ret_all=True), list)

    def test_folder_filter_and_per_provider_adapter_class(self) -> None:
        summary = _provider_summaries([SummaryProvider()])[0]
        self.assertIn("torrents", summary.folders)
        self.assertEqual(
            _filter_summaries_by_folders([summary], ["torrents"]), [summary]
        )
        adapter_class = _adapter_class(summary)
        self.assertEqual(adapter_class.provider_id, "summary")
        self.assertEqual(adapter_class.priority, 5)
        self.assertEqual(adapter_class.provider_ids, ("summary",))
        self.assertTrue(adapter_class.pack_capable)

    def test_movie_payload_maps_to_manager_and_umbrella_dict(self) -> None:
        fake = FakeManager()
        adapter = UmbrellaSourceAdapter(
            manager_factory=lambda: fake,
            options_factory=lambda: SearchOptions(include_disabled=True),
        )

        result = adapter.sources(
            {
                "title": "Big Buck Bunny",
                "year": "2008",
                "imdb": "tt1254207",
                "aliases": [{"title": "BBB"}],
            },
            {"torrent": ["magnet"]},
        )

        self.assertEqual(fake.calls[0][0], "movie")
        self.assertEqual(fake.calls[0][1][0], "Big Buck Bunny")
        self.assertEqual(fake.calls[0][2]["year"], 2008)
        self.assertEqual(fake.calls[0][2]["aliases"], ["BBB"])
        self.assertEqual(result[0]["source"], "torrent")
        self.assertEqual(result[0]["hash"], "abcdef")
        self.assertEqual(result[0]["size"], 2.0)
        self.assertTrue(result[0]["true_size"])
        self.assertEqual(result[0]["seeders"], 0)
        self.assertIn("HEVC", result[0]["info"])

    def test_episode_and_pack_payloads_map_to_manager(self) -> None:
        fake = FakeManager()
        adapter = UmbrellaSourceAdapter(
            manager_factory=lambda: fake,
            options_factory=lambda: SearchOptions(include_disabled=True),
        )

        episode = adapter.sources(
            {
                "title": "Episode Title",
                "tvshowtitle": "Example Show",
                "season": "1",
                "episode": "2",
            },
            {},
        )
        season_pack = adapter.sources_packs(
            {"tvshowtitle": "Example Show", "season": "1"}, {}
        )
        show_pack = adapter.sources_packs(
            {"tvshowtitle": "Example Show"}, {}, search_series=True, total_seasons=3
        )

        self.assertEqual(fake.calls[0][0], "episode")
        self.assertEqual(fake.calls[0][1][0], "Example Show")
        self.assertEqual(fake.calls[0][2]["season"], 1)
        self.assertEqual(fake.calls[0][2]["episode"], 2)
        self.assertEqual(episode[0]["source"], "direct")
        self.assertEqual(fake.calls[1][0], "season")
        self.assertEqual(season_pack[0]["episode_start"], 1)
        self.assertEqual(season_pack[0]["episode_end"], 8)
        self.assertEqual(fake.calls[2][0], "show")
        self.assertEqual(show_pack[0]["last_season"], 3)

    def test_provider_metadata_summary(self) -> None:
        provider = SummaryProvider()
        summary = _provider_summaries([provider])[0]

        self.assertEqual(summary.id, "summary")
        self.assertEqual(summary.provider_type, "torrent")
        self.assertTrue(summary.pack_capable)
        self.assertTrue(summary.enabled)

    def test_source_result_conversion_defaults(self) -> None:
        item = _source_to_umbrella(
            SourceResult("hoster", "Name", "https://example.test", quality="weird")
        )

        self.assertEqual(item["provider"], "hoster")
        self.assertEqual(item["source"], "hoster")
        self.assertEqual(item["quality"], "SD")
        self.assertEqual(item["size"], 0.0)
        self.assertFalse(item["direct"])

    def test_source_result_conversion_uses_title_size_fallback(self) -> None:
        item = _source_to_umbrella(
            SourceResult(
                "torrent",
                "Name 1080p 2.5 GB",
                "magnet:?xt=urn:btih:" + "a" * 40,
            )
        )

        self.assertEqual(item["size"], 2.328)
        self.assertFalse(item["true_size"])
        self.assertEqual(item["seeders"], 0)
        self.assertIn("2.33 GB", item["info"])

    def test_source_result_conversion_clamps_implausible_size(self) -> None:
        item = _source_to_umbrella(
            SourceResult(
                "torrent",
                "Name",
                "magnet:?xt=urn:btih:" + "a" * 40,
                size=246_800 * 1024**3,
            )
        )

        self.assertEqual(item["size"], 0.0)
        self.assertFalse(item["true_size"])
        self.assertNotIn("246800", item["info"])

    def test_source_result_conversion_exposes_external_consumer_fields(self) -> None:
        torrent = _source_to_umbrella(
            SourceResult(
                "torrentio",
                "Name",
                "magnet:?xt=urn:btih:" + "b" * 40,
                metadata={"seeders": "42", "size_bytes": str(3 * 1024**3)},
            )
        )
        usenet = _source_to_umbrella(
            SourceResult(
                "newznab",
                "Name",
                "https://example.test/nzb",
                metadata={"provider_type": "usenet", "usenet": "true"},
            )
        )

        self.assertEqual(torrent["seeders"], 42)
        self.assertTrue(torrent["true_size"])
        self.assertNotIn("usenet", torrent)
        self.assertEqual(usenet["source"], "usenet")
        self.assertTrue(usenet["usenet"])


if __name__ == "__main__":
    unittest.main()
