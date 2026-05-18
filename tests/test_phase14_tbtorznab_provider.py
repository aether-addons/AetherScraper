from __future__ import annotations

import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from aetherscraper import SearchOptions, SearchQuery
from aetherscraper.kodi.settings import KodiSettings
from aetherscraper.loader import load_provider_classes
from aetherscraper.providers.torznab import TbTorznabProvider

INFO_HASH = "1234567890abcdef1234567890abcdef12345678"
TBTORZNAB_XML = f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:torznab="http://torznab.com/schemas/2015/feed">
  <channel>
    <item>
      <title>Big Buck Bunny S01E02 1080p</title>
      <guid>tbtorznab-1</guid>
      <link>/download/tbtorznab-1.torrent</link>
      <category>TV</category>
      <torznab:attr name="seeders" value="31" />
      <torznab:attr name="leechers" value="4" />
      <torznab:attr name="size" value="1.4 GB" />
      <torznab:attr name="infohash" value="{INFO_HASH}" />
    </item>
  </channel>
</rss>"""


class TbTorznabHandler(BaseHTTPRequestHandler):
    last_query = {}
    last_path = ""

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/torbox/api":
            self.send_response(404)
            self.end_headers()
            return
        type(self).last_path = parsed.path
        type(self).last_query = parse_qs(parsed.query)
        body = TBTORZNAB_XML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/rss+xml")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        return


class Phase14TbTorznabProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), TbTorznabHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}/torbox/api"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_tbtorznab_uses_user_configured_torznab_endpoint(self):
        settings = KodiSettings(
            fallback={
                "provider.tbtorznab.base_url": self.base_url,
                "torbox.token": "secret-key",
                "provider.tbtorznab": "true",
            }
        )
        provider = TbTorznabProvider(settings=settings)

        results = provider.search(
            SearchQuery("Big Buck Bunny", media_type="episode", season=1, episode=2),
            SearchOptions(max_results=5),
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].provider, "tbtorznab")
        self.assertEqual(results[0].metadata["info_hash"], INFO_HASH)
        self.assertEqual(results[0].score, 31.0)
        self.assertEqual(TbTorznabHandler.last_path, "/torbox/api")
        self.assertEqual(TbTorznabHandler.last_query["t"], ["tvsearch"])
        self.assertEqual(TbTorznabHandler.last_query["q"], ["Big Buck Bunny"])
        self.assertEqual(TbTorznabHandler.last_query["season"], ["1"])
        self.assertEqual(TbTorznabHandler.last_query["ep"], ["2"])
        self.assertEqual(TbTorznabHandler.last_query["apikey"], ["secret-key"])
        self.assertEqual(TbTorznabHandler.last_query["limit"], ["5"])
        self.assertNotIn("secret-key", repr(results))

    def test_tbtorznab_discovery_and_metadata(self):
        classes, errors = load_provider_classes()
        ids = {item.config.id: item.config for item in classes}

        self.assertFalse(errors)
        self.assertIn("tbtorznab", ids)
        self.assertEqual(ids["tbtorznab"].provider_type, "torrent")
        self.assertFalse(ids["tbtorznab"].enabled)
        self.assertTrue(ids["tbtorznab"].pack_capable)
        self.assertTrue(ids["tbtorznab"].has_movies)
        self.assertTrue(ids["tbtorznab"].has_episodes)
        self.assertEqual(
            ids["tbtorznab"].media_types, ["movie", "episode", "season", "show"]
        )


if __name__ == "__main__":
    unittest.main()
