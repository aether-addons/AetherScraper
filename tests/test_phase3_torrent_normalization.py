from __future__ import annotations

import json
import os
import tempfile
import unittest

from aetherscraper import (
    SearchOptions,
    SearchQuery,
    base32_to_hex_infohash,
    build_magnet,
    bytes_to_size,
    clean_release_title,
    extract_info_hash,
    normalize_info_hash,
    normalize_torrent_item,
    parse_magnet,
    parse_size,
    parse_size_candidates,
)
from aetherscraper.providers.torrent_json import TorrentJsonProvider


class Phase3TorrentNormalizationTests(unittest.TestCase):
    def test_parse_size_accepts_common_units_and_formats(self) -> None:
        self.assertEqual(parse_size("1.5 GB"), 1_500_000_000)
        self.assertEqual(parse_size("1,024 MB"), 1_024_000_000)
        self.assertEqual(parse_size("700 MiB"), 734_003_200)
        self.assertEqual(parse_size("2.5 G"), 2_500_000_000)
        self.assertEqual(parse_size("850 M"), 850_000_000)
        self.assertEqual(parse_size(2.5), 2_500_000_000)
        self.assertEqual(parse_size(1234), 1234)
        self.assertIsNone(parse_size(True))
        self.assertIsNone(parse_size("Movie 2024 1080p WEB-DL"))
        self.assertIsNone(parse_size("246800.48 GB"))
        self.assertIsNone(parse_size("1864647.59 GB"))
        self.assertEqual(bytes_to_size(1_073_741_824), "1.00 GB")

    def test_parse_size_candidates_skips_bad_primary_fields(self) -> None:
        self.assertEqual(
            parse_size_candidates("N/A", "2147483648", "Example 2024 1080p"),
            2_147_483_648,
        )
        self.assertEqual(
            parse_size_candidates("N/A", None, "Example 2024 1080p 2.5 GB"),
            2_500_000_000,
        )

    def test_info_hash_helpers_normalize_hex_and_base32(self) -> None:
        self.assertEqual(base32_to_hex_infohash("A" * 32), "0" * 40)
        self.assertEqual(normalize_info_hash("URN:BTIH:" + "A" * 32), "0" * 40)
        self.assertEqual(normalize_info_hash("ABCDEF" + "1" * 34), "abcdef" + "1" * 34)
        self.assertEqual(normalize_info_hash("not-a-hash"), "")

    def test_magnet_hash_extraction_uses_lowercase_hex(self) -> None:
        magnet = build_magnet(
            "A" * 32, name="Big Buck Bunny", trackers=["udp://tracker.example"]
        )
        parsed = parse_magnet(magnet)

        self.assertEqual(parsed["name"], "Big Buck Bunny")
        self.assertEqual(parsed["info_hash"], "0" * 40)
        self.assertEqual(extract_info_hash(magnet), "0" * 40)
        self.assertEqual(extract_info_hash("urn:btih:" + "A" * 32), "0" * 40)

    def test_clean_release_title_removes_common_noise(self) -> None:
        self.assertEqual(
            clean_release_title("Big.Buck.Bunny.2008.1080p.WEB-DL.x265-GROUP.mkv"),
            "Big Buck Bunny 2008 GROUP",
        )

    def test_normalize_torrent_item_maps_provider_field_aliases(self) -> None:
        item = normalize_torrent_item(
            {
                "name": "Big Buck Bunny 1080p",
                "magnet_uri": build_magnet("A" * 32),
                "size": "N/A",
                "size_bytes": "1500000000",
                "seeds": "12",
                "leeches": "3",
                "lang": "en",
                "resolution": "1080p",
                "metadata": {"source": "fixture", "ignore": None},
            }
        )

        self.assertEqual(item.title, "Big Buck Bunny 1080p")
        self.assertEqual(item.info_hash, "0" * 40)
        self.assertEqual(item.size, 1_500_000_000)
        self.assertEqual(item.seeders, 12)
        self.assertEqual(item.leechers, 3)
        self.assertEqual(item.language, "en")
        self.assertEqual(item.quality, "1080p")
        self.assertEqual(item.metadata["source"], "fixture")
        self.assertEqual(item.metadata["clean_title"], "Big Buck Bunny")

    def test_torrent_json_provider_uses_normalization_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "torrents.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "items": [
                            {
                                "name": "Big Buck Bunny 720p",
                                "magnet_uri": build_magnet("A" * 32),
                                "size": "700 MiB",
                                "seeds": "7",
                                "resolution": "720p",
                            }
                        ]
                    },
                    handle,
                )

            provider = TorrentJsonProvider(path=path)
            results = list(
                provider.search(SearchQuery("Big Buck Bunny"), SearchOptions())
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].metadata["info_hash"], "0" * 40)
        self.assertEqual(results[0].size, 734_003_200)
        self.assertEqual(results[0].score, 7.0)


if __name__ == "__main__":
    unittest.main()
