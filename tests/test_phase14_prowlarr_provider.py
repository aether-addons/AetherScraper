from __future__ import annotations

import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from aetherscraper import SearchOptions, SearchQuery
from aetherscraper.kodi.settings import KodiSettings
from aetherscraper.loader import load_provider_classes
from aetherscraper.providers.torznab import ProwlarrProvider

INFO_HASH = "abcdefabcdefabcdefabcdefabcdefabcdefabcd"
PROWLARR_XML = f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:torznab="http://torznab.com/schemas/2015/feed">
  <channel>
    <item>
      <title>Big Buck Bunny 2008 1080p</title>
      <guid>prowlarr-1</guid>
      <link>/download/prowlarr-1.torrent</link>
      <category>Movies</category>
      <torznab:attr name="seeders" value="42" />
      <torznab:attr name="leechers" value="2" />
      <torznab:attr name="size" value="900 MB" />
      <torznab:attr name="infohash" value="{INFO_HASH}" />
    </item>
  </channel>
</rss>"""


class ProwlarrHandler(BaseHTTPRequestHandler):
    last_query = {}
    last_path = ""

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/7/api":
            self.send_response(404)
            self.end_headers()
            return
        type(self).last_path = parsed.path
        type(self).last_query = parse_qs(parsed.query)
        body = PROWLARR_XML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/rss+xml")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        return


class Phase14ProwlarrProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), ProwlarrHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.root_url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_prowlarr_builds_indexer_endpoint_and_torznab_params(self):
        settings = KodiSettings(
            fallback={
                "provider.prowlarr.base_url": self.root_url,
                "provider.prowlarr.indexer_id": "7",
                "provider.prowlarr.api_key": "secret-key",
                "provider.prowlarr.categories": "2000, 2010, bad",
                "provider.prowlarr.enabled": "true",
            }
        )
        provider = ProwlarrProvider(settings=settings)

        results = provider.search(
            SearchQuery("Big Buck Bunny", year=2008, imdb_id="tt1254207"),
            SearchOptions(max_results=5),
        )

        self.assertEqual(provider.base_url, f"{self.root_url}/7/api")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].provider, "prowlarr")
        self.assertEqual(results[0].metadata["info_hash"], INFO_HASH)
        self.assertEqual(results[0].score, 42.0)
        self.assertEqual(ProwlarrHandler.last_path, "/7/api")
        self.assertEqual(ProwlarrHandler.last_query["t"], ["movie"])
        self.assertEqual(ProwlarrHandler.last_query["q"], ["Big Buck Bunny"])
        self.assertEqual(ProwlarrHandler.last_query["year"], ["2008"])
        self.assertEqual(ProwlarrHandler.last_query["imdbid"], ["1254207"])
        self.assertEqual(ProwlarrHandler.last_query["cat"], ["2000,2010"])
        self.assertEqual(ProwlarrHandler.last_query["apikey"], ["secret-key"])
        self.assertNotIn("secret-key", repr(results))

    def test_prowlarr_discovery_and_metadata(self):
        classes, errors = load_provider_classes()
        ids = {item.config.id: item.config for item in classes}

        self.assertFalse(errors)
        self.assertIn("prowlarr", ids)
        self.assertEqual(ids["prowlarr"].provider_type, "torrent")
        self.assertFalse(ids["prowlarr"].enabled)
        self.assertTrue(ids["prowlarr"].pack_capable)
        self.assertTrue(ids["prowlarr"].has_movies)
        self.assertTrue(ids["prowlarr"].has_episodes)
        self.assertEqual(
            ids["prowlarr"].media_types, ["movie", "episode", "season", "show"]
        )


if __name__ == "__main__":
    unittest.main()
