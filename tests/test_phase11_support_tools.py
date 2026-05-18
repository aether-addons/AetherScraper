from __future__ import annotations

import os
import tempfile
import unittest

from aetherscraper import (
    AddonLogBackend,
    DebugConfig,
    KodiSettings,
    ProviderConfig,
    SearchOptions,
    SearchQuery,
    SourceResult,
    cleanup_settings,
    help_text,
    log_text,
    redact_secrets,
    run_provider_health_checks,
)
from aetherscraper.provider import BaseProvider


class HealthyProvider(BaseProvider):
    config = ProviderConfig(id="healthy", name="Healthy", enabled=True)

    def search(self, query: SearchQuery, options: SearchOptions):
        return [SourceResult(provider=self.id, title=query.title, url="memory://ok")]


class FailingProvider(BaseProvider):
    config = ProviderConfig(id="failing", name="Failing", enabled=True)

    def search(self, query: SearchQuery, options: SearchOptions):
        raise RuntimeError("api_key=SECRET token=TOKEN")


class SupportToolTests(unittest.TestCase):
    def test_debug_config_reads_support_settings(self) -> None:
        settings = KodiSettings(
            fallback={
                "debug_logging": "true",
                "support_file_logging": "true",
                "support_log_level": "debug",
                "support_redact_secrets": "true",
                "support_max_log_bytes": "8192",
            }
        )

        config = DebugConfig.from_settings(settings)

        self.assertTrue(config.enabled)
        self.assertTrue(config.file_logging)
        self.assertEqual(config.log_level, "debug")
        self.assertEqual(config.max_log_bytes, 8192)

    def test_redact_secrets_masks_tokens_headers_and_urls(self) -> None:
        text = redact_secrets(
            "Authorization: Bearer SECRET\n"
            "https://example.test/rss?apikey=SECRET&x=1 token=VALUE"
        )

        self.assertNotIn("SECRET", text)
        self.assertNotIn("VALUE", text)
        self.assertIn("apikey=[redacted]", text)
        self.assertIn("Authorization: [redacted]", text)

    def test_addon_log_backend_writes_reads_and_requires_confirm_to_clear(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            backend = AddonLogBackend.from_profile(base_path=root)
            backend.write("token=SECRET ok")

            self.assertIn("token=[redacted]", log_text(backend))
            with self.assertRaises(PermissionError):
                backend.clear()
            self.assertTrue(backend.clear(confirm=True))
            self.assertFalse(os.path.exists(backend.path))

    def test_provider_health_checks_capture_success_and_redacted_failure(self) -> None:
        summary = run_provider_health_checks([HealthyProvider(), FailingProvider()])

        self.assertEqual(summary.total, 2)
        self.assertEqual(summary.ok, 1)
        self.assertEqual(summary.failed, 1)
        failure = next(
            result for result in summary.results if result.provider_id == "failing"
        )
        self.assertIn("api_key=[redacted]", failure.error)
        self.assertNotIn("SECRET", failure.error)

    def test_help_text_reads_addon_docs(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            with open(os.path.join(root, "HELP.md"), "w", encoding="utf-8") as handle:
                handle.write("help body")

            self.assertEqual(help_text(root), "help body")

    def test_settings_cleanup_requires_confirmation(self) -> None:
        settings = KodiSettings(fallback={"debug_logging": "true"})

        with self.assertRaises(PermissionError):
            cleanup_settings(settings, keys=["debug_logging"])
        reset = cleanup_settings(settings, keys=["debug_logging"], confirm=True)

        self.assertEqual(reset, ["debug_logging"])
        self.assertFalse(settings.get_bool("debug_logging", True))


if __name__ == "__main__":
    unittest.main()
