from __future__ import annotations

import gzip
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from aetherscraper.config import ProviderConfig, SearchOptions
from aetherscraper.http import (
    DEFAULT_USER_AGENT,
    HttpClient,
    HttpResponse,
    NetworkOptions,
    browser_headers,
    build_url,
    choose_user_agent,
    get_json,
    get_text,
    options_from_provider,
)

PAYLOAD = b"0123456789"


class NetworkHandler(BaseHTTPRequestHandler):
    attempts = 0

    def do_HEAD(self):
        if self.path == "/file":
            self.send_response(200)
            self.send_header("Content-Length", str(len(PAYLOAD)))
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/json"):
            self._send_json({"ok": True, "query": self.path})
            return
        if self.path == "/gzip":
            body = gzip.compress(b"compressed")
            self.send_response(200)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/set-cookie":
            self.send_response(200)
            self.send_header("Set-Cookie", "session=abc; Path=/")
            self.end_headers()
            self.wfile.write(b"set")
            return
        if self.path == "/echo-cookie":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(self.headers.get("Cookie", "").encode("utf-8"))
            return
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/target")
            self.end_headers()
            return
        if self.path == "/target":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"target")
            return
        if self.path == "/file":
            self._send_file()
            return
        if self.path == "/flaky":
            type(self).attempts += 1
            if type(self).attempts == 1:
                self.send_response(503)
                self.end_headers()
                return
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        self.send_response(404)
        self.end_headers()

    def _send_json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self):
        range_header = self.headers.get("Range", "")
        if range_header == "bytes=2-5":
            body = PAYLOAD[2:6]
            self.send_response(206)
            self.send_header("Content-Range", f"bytes 2-5/{len(PAYLOAD)}")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if range_header == "bytes=0-0":
            body = PAYLOAD[:1]
            self.send_response(206)
            self.send_header("Content-Range", f"bytes 0-0/{len(PAYLOAD)}")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)

    def log_message(self, format, *args):  # noqa: A002
        return


class Phase7NetworkStackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), NetworkHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_response_text_json_and_build_url(self):
        url = build_url(f"{self.base_url}/json", {"q": "big bunny"})
        response = HttpClient().request(url)

        self.assertIsInstance(response, HttpResponse)
        self.assertTrue(response.ok)
        self.assertEqual(response.json()["ok"], True)
        self.assertIn("q=big+bunny", response.json()["query"])

    def test_legacy_get_text_and_json_helpers(self):
        text = get_text(f"{self.base_url}/json")
        data = get_json(f"{self.base_url}/json")

        self.assertIn('"ok": true', text)
        self.assertTrue(data["ok"])

    def test_session_cookies_persist(self):
        client = HttpClient()

        client.request(f"{self.base_url}/set-cookie")
        response = client.request(f"{self.base_url}/echo-cookie")

        self.assertIn("session=abc", response.text)

    def test_redirects_can_be_allowed_or_blocked(self):
        client = HttpClient()

        followed = client.request(f"{self.base_url}/redirect")
        blocked = client.request(f"{self.base_url}/redirect", allow_redirects=False)

        self.assertEqual(followed.text, "target")
        self.assertEqual(blocked.status_code, 302)

    def test_headers_presets_and_gzip_decode(self):
        headers = browser_headers(user_agent="Agent", referer="http://ref", xhr=True)
        response = HttpClient(NetworkOptions(headers={"X-Test": "1"})).request(
            f"{self.base_url}/gzip"
        )

        self.assertEqual(headers["User-Agent"], "Agent")
        self.assertEqual(headers["Referer"], "http://ref")
        self.assertEqual(headers["X-Requested-With"], "XMLHttpRequest")
        self.assertEqual(response.text, "compressed")

    def test_partial_content_and_file_size(self):
        client = HttpClient()

        partial = client.partial_content(f"{self.base_url}/file", 2, 5)
        size = client.file_size(f"{self.base_url}/file")

        self.assertEqual(partial.status_code, 206)
        self.assertEqual(partial.body, b"2345")
        self.assertEqual(size, len(PAYLOAD))

    def test_retry_backoff_and_provider_options(self):
        NetworkHandler.attempts = 0
        provider_config = ProviderConfig(
            id="net",
            name="Net",
            timeout=9,
            retries=2,
            headers={"X-Provider": "1"},
            user_agent="ProviderAgent",
        )
        options = SearchOptions(
            timeout=3,
            extra={
                "network": {
                    "retries": 1,
                    "backoff_factor": 0,
                    "proxy": "http://proxy.local:8080",
                    "headers": {"X-Search": "1"},
                    "referer": "http://ref",
                    "xhr": True,
                }
            },
        )

        network_options = options_from_provider(provider_config, options)
        response = HttpClient(NetworkOptions(retries=1, backoff_factor=0)).request(
            f"{self.base_url}/flaky"
        )

        self.assertEqual(network_options.timeout, 3)
        self.assertEqual(network_options.retries, 1)
        self.assertEqual(network_options.proxy, "http://proxy.local:8080")
        self.assertEqual(network_options.headers["X-Provider"], "1")
        self.assertEqual(network_options.headers["X-Search"], "1")
        self.assertEqual(network_options.user_agent, "ProviderAgent")
        self.assertEqual(response.text, "ok")

    def test_user_agent_choice(self):
        self.assertEqual(choose_user_agent(False), DEFAULT_USER_AGENT)
        self.assertEqual(choose_user_agent(True, "Fixed"), "Fixed")
        self.assertTrue(choose_user_agent(True))


if __name__ == "__main__":
    unittest.main()
