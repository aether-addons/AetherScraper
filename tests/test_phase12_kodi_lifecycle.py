from __future__ import annotations

import json
import os
import tempfile
import unittest

from aetherscraper import (
    KodiSettings,
    SettingsMonitor,
    WindowPropertyStore,
    dispatch_action,
    get_lifecycle_property,
    parse_plugin_query,
    run_service,
    run_startup,
    sync_settings_to_window,
)


class KodiLifecycleTests(unittest.TestCase):
    def test_startup_creates_profile_records_update_and_window_properties(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            settings = KodiSettings(fallback={"debug_logging": "true"})
            status = run_startup(version="1.0.0", settings=settings, base_path=root)

            self.assertTrue(os.path.isdir(status.profile))
            self.assertTrue(status.first_run_complete)
            self.assertEqual(get_lifecycle_property("started"), "true")

            updated = run_startup(version="1.1.0", settings=settings, base_path=root)

            self.assertTrue(updated.version_changed)
            self.assertTrue(updated.cleanup_required)
            self.assertEqual(get_lifecycle_property("cleanup_required"), "true")

    def test_window_settings_sync_skips_secret_keys(self) -> None:
        settings = KodiSettings(
            fallback={"debug_logging": "true", "provider.prowlarr.api_key": "SECRET"}
        )
        store = WindowPropertyStore()

        mirrored = sync_settings_to_window(
            settings,
            store=store,
            keys=("debug_logging", "provider.prowlarr.api_key"),
        )

        self.assertEqual(mirrored, {"debug_logging": "true"})
        self.assertEqual(store.get("settings.debug_logging"), "true")
        self.assertEqual(store.get("settings.provider.prowlarr.api_key"), "")
        with self.assertRaises(ValueError):
            store.set("provider.prowlarr.api_key", "SECRET")

    def test_plugin_query_and_dispatch_actions_work_without_kodi(self) -> None:
        params = parse_plugin_query(["default.py", "1", "?action=health"])

        self.assertEqual(params["action"], "health")
        result = dispatch_action("unknown", settings=KodiSettings())

        self.assertFalse(result.ok)
        self.assertEqual(result.action, "unknown")

    def test_mediaplay_alias_accepts_direct_url_without_kodi_handle(self) -> None:
        result = dispatch_action(
            "MediaPlay",
            settings=KodiSettings(),
            params={"url": "https://example.test/video.mp4", "title": "Example"},
            argv=["default.py"],
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.action, "mediaplay")

    def test_selector_json_is_packaged(self) -> None:
        path = os.path.join(
            "script.module.aetherscraper", "resources", "aetherscraper.select.json"
        )
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)

        self.assertEqual(data["entrypoint"], "aetherscraper.sources")
        self.assertIn("torrents", data["folders"])
        self.assertIn("MediaPlay", data["actions"]["play"])

    def test_settings_monitor_marks_and_polls_changes(self) -> None:
        calls = []
        monitor = SettingsMonitor(
            settings=KodiSettings(), on_changed=lambda current: calls.append(current)
        )

        self.assertFalse(monitor.poll())
        monitor.mark_changed()

        self.assertTrue(monitor.poll())
        self.assertEqual(len(calls), 1)

    def test_service_loop_is_bounded_for_tests(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            status = run_service(
                version="1.0.0", base_path=root, interval=0, max_iterations=0
            )

            self.assertTrue(status.first_run_complete)


if __name__ == "__main__":
    unittest.main()
