from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from aetherscraper import SearchOptions, SearchQuery
from aetherscraper.kodi.settings import KodiSettings
from aetherscraper.loader import load_provider_classes
from aetherscraper.providers.ytsmx import YtsMxProvider, normalize_ytsmx_results

INFO_HASH = "0123456789abcdef0123456789abcdef01234567"
YTS_RESPONSE = {
    "status": "ok",
    "data": {
        "movie_count": 1,
        "movies": [
            {
                "id": 1,
                "title": "Big Buck Bunny",
                "title_long": "Big Buck Bunny (2008)",
                "year": 2008,
                "language": "en",
                "imdb_code": "tt1254207",
                "torrents": [
                    {
                        "url": "https://yts.mx/torrent/download/0123",
                        "hash": INFO_HASH.upper(),
                        "quality": "1080p",
                        "type": "bluray",
                        "seeds": 123,
                        "peers": 4,
                        "size": "1.2 GB",
                    }
                ],
            }
        ],
    },
}


class YtsMxHandler(BaseHTTPRequestHandler):
    last_query = {}
    last_accept = ""

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/v2/list_movies.json":
            self.send_response(404)
            self.end_headers()
            return
        type(self).last_query = parse_qs(parsed.query)
        type(self).last_accept = self.headers.get("Accept", "")
        body = json.dumps(YTS_RESPONSE).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        return


class Phase14YtsMxProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), YtsMxHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.api_url = (
            f"http://127.0.0.1:{cls.server.server_address[1]}/api/v2/list_movies.json"
        )

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_normalize_ytsmx_response(self):
        results = normalize_ytsmx_results(YTS_RESPONSE)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].provider, "ytsmx")
        self.assertIn("Big Buck Bunny", results[0].title)
        self.assertIn("1080p", results[0].title)
        self.assertTrue(results[0].url.startswith("magnet:?"))
        self.assertEqual(results[0].quality, "1080p")
        self.assertEqual(results[0].score, 123.0)
        self.assertEqual(results[0].size, 1200000000)
        self.assertEqual(results[0].language, "en")
        self.assertEqual(results[0].metadata["info_hash"], INFO_HASH)
        self.assertEqual(results[0].metadata["imdb_code"], "tt1254207")

    def test_ytsmx_provider_uses_settings_and_movie_only(self):
        settings = KodiSettings(
            fallback={
                "provider.ytsmx.base_url": self.api_url,
                "provider.ytsmx.enabled": "true",
            }
        )
        provider = YtsMxProvider(settings=settings)

        episode_results = provider.search(
            SearchQuery("Big Buck Bunny", media_type="episode", season=1, episode=1),
            SearchOptions(),
        )
        movie_results = provider.search(
            SearchQuery("Big Buck Bunny", year=2008, imdb_id="tt1254207"),
            SearchOptions(max_results=3),
        )

        self.assertEqual(episode_results, [])
        self.assertEqual(len(movie_results), 1)
        self.assertEqual(YtsMxHandler.last_query["query_term"], ["tt1254207"])
        self.assertEqual(YtsMxHandler.last_query["limit"], ["3"])
        self.assertEqual(YtsMxHandler.last_query["sort_by"], ["seeds"])
        self.assertEqual(YtsMxHandler.last_accept, "application/json")
        self.assertNotIn("api_key", repr(movie_results))

    def test_ytsmx_discovery_and_metadata(self):
        classes, errors = load_provider_classes()
        ids = {item.config.id: item.config for item in classes}

        self.assertFalse(errors)
        self.assertIn("ytsmx", ids)
        self.assertEqual(ids["ytsmx"].provider_type, "torrent")
        self.assertFalse(ids["ytsmx"].enabled)
        self.assertFalse(ids["ytsmx"].pack_capable)
        self.assertTrue(ids["ytsmx"].has_movies)
        self.assertFalse(ids["ytsmx"].has_episodes)


if __name__ == "__main__":
    unittest.main()
