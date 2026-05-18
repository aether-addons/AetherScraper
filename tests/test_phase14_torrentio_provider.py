from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from aetherscraper import SearchOptions, SearchQuery
from aetherscraper.kodi.settings import KodiSettings
from aetherscraper.loader import load_provider_classes
from aetherscraper.providers.torrentio import (
    TorrentioProvider,
    normalize_torrentio_results,
)

INFO_HASH = "1234567890abcdef1234567890abcdef12345678"
TORRENTIO_RESPONSE = {
    "streams": [
        {
            "name": "Torrentio\\n1080p",
            "title": "Big Buck Bunny 2008 1080p BluRay 👤 321 💾 1.4 GB",
            "infoHash": INFO_HASH.upper(),
            "fileIdx": 0,
            "sources": ["tracker:udp://tracker.opentrackr.org:1337/announce"],
            "behaviorHints": {
                "filename": "Big.Buck.Bunny.2008.1080p.BluRay.x264.mkv",
                "bingeGroup": "torrentio|1080p",
            },
        }
    ]
}


class TorrentioHandler(BaseHTTPRequestHandler):
    last_path = ""
    last_accept = ""

    def do_GET(self):
        type(self).last_path = self.path
        type(self).last_accept = self.headers.get("Accept", "")
        if self.path not in {
            "/stream/movie/tt1254207.json",
            "/sort=qualitysize/stream/series/tt0944947:1:2.json",
        }:
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps(TORRENTIO_RESPONSE).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        return


class Phase14TorrentioProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), TorrentioHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_normalize_torrentio_response(self):
        results = normalize_torrentio_results(TORRENTIO_RESPONSE)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].provider, "torrentio")
        self.assertIn("Big.Buck.Bunny", results[0].title)
        self.assertTrue(results[0].url.startswith("magnet:?"))
        self.assertIn(
            "tr=udp%3A//tracker.opentrackr.org%3A1337/announce", results[0].url
        )
        self.assertEqual(results[0].quality.lower(), "1080p")
        self.assertEqual(results[0].score, 321.0)
        self.assertEqual(results[0].size, 1400000000)
        self.assertEqual(results[0].metadata["info_hash"], INFO_HASH)
        self.assertEqual(results[0].metadata["file_idx"], "0")
        self.assertEqual(results[0].metadata["binge_group"], "torrentio|1080p")

    def test_torrentio_provider_movie_requires_imdb_id(self):
        settings = KodiSettings(
            fallback={
                "provider.torrentio.base_url": self.base_url,
                "provider.torrentio.enabled": "true",
            }
        )
        provider = TorrentioProvider(settings=settings)

        missing_id = provider.search(
            SearchQuery("Big Buck Bunny", media_type="movie"), SearchOptions()
        )
        movie_results = provider.search(
            SearchQuery("Big Buck Bunny", media_type="movie", imdb_id="tt1254207"),
            SearchOptions(max_results=3),
        )

        self.assertEqual(missing_id, [])
        self.assertEqual(len(movie_results), 1)
        self.assertEqual(TorrentioHandler.last_path, "/stream/movie/tt1254207.json")
        self.assertEqual(TorrentioHandler.last_accept, "application/json")

    def test_torrentio_provider_episode_config_path(self):
        settings = KodiSettings(
            fallback={
                "provider.torrentio.base_url": self.base_url,
                "provider.torrentio.config_path": "sort=qualitysize",
                "provider.torrentio.enabled": "true",
            }
        )
        provider = TorrentioProvider(settings=settings)

        results = provider.search(
            SearchQuery(
                "Game of Thrones",
                media_type="episode",
                imdb_id="tt0944947",
                season=1,
                episode=2,
            ),
            SearchOptions(),
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            TorrentioHandler.last_path,
            "/sort=qualitysize/stream/series/tt0944947:1:2.json",
        )

    def test_torrentio_discovery_and_metadata(self):
        classes, errors = load_provider_classes()
        ids = {item.config.id: item.config for item in classes}

        self.assertFalse(errors)
        self.assertIn("torrentio", ids)
        self.assertEqual(ids["torrentio"].provider_type, "torrent")
        self.assertFalse(ids["torrentio"].enabled)
        self.assertFalse(ids["torrentio"].pack_capable)
        self.assertTrue(ids["torrentio"].has_movies)
        self.assertTrue(ids["torrentio"].has_episodes)
        self.assertEqual(ids["torrentio"].media_types, ["movie", "episode"])


if __name__ == "__main__":
    unittest.main()
