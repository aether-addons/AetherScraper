from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from aetherscraper import SearchOptions, SearchQuery
from aetherscraper.kodi.settings import KodiSettings
from aetherscraper.loader import load_provider_classes
from aetherscraper.providers.aiostreams import (
    AIOStreamsProvider,
    normalize_aiostreams_results,
)
from aetherscraper.providers.torznab import ProwlarrProvider, TorznabProvider
from aetherscraper.torznab import build_torznab_params, parse_torznab

INFO_HASH = "0123456789abcdef0123456789abcdef01234567"
TORZNAB_XML = f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:torznab="http://torznab.com/schemas/2015/feed">
  <channel>
    <item>
      <title>Big Buck Bunny 2008 1080p</title>
      <guid>abc</guid>
      <link>/download/1.torrent</link>
      <category>Movies</category>
      <torznab:attr name="seeders" value="12" />
      <torznab:attr name="leechers" value="3" />
      <torznab:attr name="size" value="1.5 GB" />
      <torznab:attr name="infohash" value="{INFO_HASH}" />
    </item>
  </channel>
</rss>"""


class ProviderHandler(BaseHTTPRequestHandler):
    last_torznab_query = {}
    last_aiostreams_headers = {}

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/torznab":
            type(self).last_torznab_query = parse_qs(parsed.query)
            body = TORZNAB_XML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/rss+xml")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/streams":
            type(self).last_aiostreams_headers = dict(self.headers.items())
            body = json.dumps(
                {
                    "streams": [
                        {
                            "title": "Big Buck Bunny 2008 720p",
                            "url": "https://example.invalid/video.mp4",
                            "quality": "720p",
                            "direct": True,
                        },
                        {
                            "title": "Big Buck Bunny 2008 1080p",
                            "magnet": f"magnet:?xt=urn:btih:{INFO_HASH}&dn=Big+Buck+Bunny",
                            "seeders": 5,
                        },
                    ]
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):  # noqa: A002
        return


class Phase8AuthorizedProvidersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), ProviderHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_parse_torznab_xml(self):
        items = parse_torznab(TORZNAB_XML, self.base_url)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Big Buck Bunny 2008 1080p")
        self.assertEqual(items[0].info_hash, INFO_HASH)
        self.assertEqual(items[0].seeders, 12)
        self.assertEqual(items[0].size, 1500000000)
        self.assertEqual(items[0].torrent_url, f"{self.base_url}/download/1.torrent")

    def test_torznab_query_params(self):
        query = SearchQuery(
            "Show Name", media_type="episode", season=2, episode=3, imdb_id="tt123"
        )
        params = build_torznab_params(query, "secret", [5000, 5030])

        self.assertEqual(params["t"], "tvsearch")
        self.assertEqual(params["season"], "2")
        self.assertEqual(params["ep"], "3")
        self.assertEqual(params["imdbid"], "123")
        self.assertEqual(params["apikey"], "secret")
        self.assertEqual(params["cat"], "5000,5030")

    def test_torznab_provider_uses_settings_without_logging_secret(self):
        settings = KodiSettings(
            fallback={
                "provider.torznab.base_url": f"{self.base_url}/torznab",
                "provider.torznab.api_key": "secret-key",
            }
        )
        provider = TorznabProvider(settings=settings)

        results = provider.search(
            SearchQuery("Big Buck Bunny", year=2008), SearchOptions()
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].provider, "torznab")
        self.assertEqual(ProviderHandler.last_torznab_query["apikey"], ["secret-key"])
        self.assertNotIn("secret-key", repr(results[0]))

    def test_prowlarr_is_torznab_wrapper(self):
        self.assertEqual(ProwlarrProvider.config.id, "prowlarr")
        self.assertTrue(ProwlarrProvider.config.pack_capable)

    def test_aiostreams_normalization_and_provider(self):
        normalized = normalize_aiostreams_results(
            "aiostreams",
            {
                "streams": [
                    {
                        "title": "Big Buck Bunny 2008",
                        "url": "https://example.invalid/v.mp4",
                        "size": "1.5 GB",
                    }
                ]
            },
        )
        settings = KodiSettings(
            fallback={
                "provider.aiostreams.instance_url": self.base_url,
                "provider.aiostreams.auth_token": "Bearer secret",
                "provider.aiostreams.auth_header": "Authorization",
            }
        )
        provider = AIOStreamsProvider(settings=settings)

        results = provider.search(
            SearchQuery("Big Buck Bunny", year=2008), SearchOptions()
        )

        self.assertEqual(normalized[0].url, "https://example.invalid/v.mp4")
        self.assertEqual(normalized[0].size, 1_500_000_000)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].provider, "aiostreams")
        self.assertEqual(
            ProviderHandler.last_aiostreams_headers["Authorization"], "Bearer secret"
        )
        self.assertNotIn("Bearer secret", repr(results))

    def test_discovery_finds_phase8_providers(self):
        classes, errors = load_provider_classes()
        ids = {item.config.id for item in classes}

        self.assertFalse(errors)
        self.assertIn("torznab", ids)
        self.assertIn("prowlarr", ids)
        self.assertNotIn("torbox_torznab", ids)
        self.assertIn("aiostreams", ids)


if __name__ == "__main__":
    unittest.main()
