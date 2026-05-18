from __future__ import annotations

import os
import tempfile
import time
import unittest
from typing import cast

from aetherscraper import CacheRecord, SQLiteCache, cache_from_profile
from aetherscraper.cache import CACHE_SCHEMA_VERSION


class CachePersistenceTests(unittest.TestCase):
    def test_sqlite_cache_stores_json_under_profile_cache(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            cache = cache_from_profile(base_path=root)

            cache.set("search", "movie:1", {"title": "Big Buck Bunny"}, ttl=60)

            self.assertTrue(cache.db_path.startswith(os.path.join(root, "cache")))
            self.assertEqual(
                cache.get("search", "movie:1"), {"title": "Big Buck Bunny"}
            )
            record = cache.get_record("search", "movie:1")
            self.assertIsNotNone(record)
            record = cast(CacheRecord, record)
            self.assertEqual(record.namespace, "search")
            self.assertGreater(record.expires_at or 0, time.time())

    def test_ttl_expiry_and_cleanup_drop_stale_values(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            cache = SQLiteCache.from_profile(base_path=root)
            cache.set("search", "expired", {"value": 1}, ttl=0.01)
            cache.set("search", "fresh", {"value": 2}, ttl=60)
            time.sleep(0.02)

            self.assertIsNone(cache.get("search", "expired"))
            self.assertEqual(cache.cleanup(), 0)
            self.assertEqual(cache.get("search", "fresh"), {"value": 2})

    def test_invalidate_namespace_or_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            cache = SQLiteCache.from_profile(base_path=root)
            cache.set("search", "movie:1", 1)
            cache.set("search", "episode:1", 2)
            cache.set("state", "movie:1", 3)

            self.assertEqual(cache.invalidate("search", "movie:"), 1)
            self.assertIsNone(cache.get("search", "movie:1"))
            self.assertEqual(cache.get("search", "episode:1"), 2)
            self.assertEqual(cache.invalidate("search"), 1)
            self.assertEqual(cache.get("state", "movie:1"), 3)

    def test_provider_state_persists_between_instances(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            cache = SQLiteCache.from_profile(base_path=root)
            cache.set_provider_state("prowlarr", {"last_indexer": 7})

            reopened = SQLiteCache(db_path=cache.db_path)

            self.assertEqual(
                reopened.get_provider_state("prowlarr"), {"last_indexer": 7}
            )
            self.assertTrue(reopened.delete_provider_state("prowlarr"))
            self.assertEqual(reopened.get_provider_state("prowlarr", {}), {})

    def test_undesirable_keyword_db_normalizes_and_persists(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            cache = SQLiteCache.from_profile(base_path=root)

            saved = cache.set_undesirable_keywords("cam, sample, CAM, ")
            cache.add_undesirable_keyword("watermark")
            cache.remove_undesirable_keyword("sample")

            self.assertEqual(saved, ["cam", "sample"])
            self.assertEqual(cache.get_undesirable_keywords(), ["cam", "watermark"])

    def test_schema_version_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            cache = SQLiteCache.from_profile(base_path=root)
            with cache._connect() as conn:
                row = conn.execute(
                    "SELECT value FROM schema_info WHERE key = 'version'"
                ).fetchone()
            self.assertEqual(row[0], str(CACHE_SCHEMA_VERSION))


if __name__ == "__main__":
    unittest.main()
