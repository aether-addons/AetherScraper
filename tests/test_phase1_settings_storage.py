from __future__ import annotations

import os
import tempfile
import unittest

from aetherscraper import (
    GlobalConfig,
    KodiSettings,
    first_run_setup,
    record_version_update,
)


class Phase1SettingsStorageTests(unittest.TestCase):
    def test_settings_fallback_snapshot(self) -> None:
        settings = KodiSettings(
            fallback={
                "debug_logging": "true",
                "scrape_timeout": "45",
                "max_results": "25",
                "provider_timeout": "8",
                "provider_retries": "2",
            },
            addon=None,
        )
        snapshot = settings.snapshot()
        self.assertTrue(snapshot.debug_logging)
        self.assertEqual(snapshot.scrape_timeout, 45)
        self.assertEqual(snapshot.max_results, 25)
        self.assertEqual(snapshot.provider_timeout, 8)
        self.assertEqual(snapshot.provider_retries, 2)

    def test_global_config_from_settings(self) -> None:
        settings = KodiSettings(
            fallback={"max_results": "12", "debug_logging": "true"}, addon=None
        )
        config = GlobalConfig.from_kodi_settings(settings)
        self.assertEqual(config.max_results, 12)
        self.assertTrue(config.debug_logging)

    def test_profile_setup_and_version_update_are_non_destructive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = first_run_setup(version="0.1.0", base_path=temp_dir)
            self.assertTrue(os.path.isdir(paths.cache))
            state = paths.read_state()
            self.assertTrue(state["first_run_complete"])
            self.assertFalse(state["cleanup_required"])

            changed = record_version_update(version="0.2.0", base_path=temp_dir)
            self.assertTrue(changed)
            state = paths.read_state()
            self.assertEqual(state["previous_version"], "0.1.0")
            self.assertTrue(state["cleanup_required"])


if __name__ == "__main__":
    unittest.main()
