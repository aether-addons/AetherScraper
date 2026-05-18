from __future__ import annotations

import os
import unittest

from aetherscraper import (
    KodiSettings,
    SearchQuery,
    disable_all_providers,
    enable_all_providers,
    enable_pack_capable_providers,
    enable_torrent_providers,
    load_providers,
    restore_provider_defaults,
)
from aetherscraper.loader import load_provider_configs


class Phase2ProviderDiscoveryTests(unittest.TestCase):
    def test_provider_configs_include_phase2_metadata(self) -> None:
        configs = load_provider_configs(
            os.path.join("script.module.aetherscraper", "resources", "providers.d")
        )
        torrent = configs["torrent_json"]
        example = configs["example"]

        self.assertEqual(torrent.provider_type, "torrent")
        self.assertTrue(torrent.pack_capable)
        self.assertIn("season", torrent.media_types)
        self.assertEqual(example.provider_type, "direct")
        self.assertFalse(example.has_episodes)

    def test_load_providers_discovers_builtin_modules(self) -> None:
        providers, errors = load_providers()
        self.assertEqual(errors, [])
        ids = [provider.id for provider in providers]
        self.assertIn("torrent_json", ids)
        self.assertIn("example", ids)

    def test_settings_control_provider_enabled_state(self) -> None:
        settings = KodiSettings(
            fallback={
                "provider.torrent_json.enabled": "false",
                "provider.example.enabled": "true",
            },
            addon=None,
        )
        providers, errors = load_providers(settings=settings)
        self.assertEqual(errors, [])
        by_id = {provider.id: provider for provider in providers}

        self.assertFalse(by_id["torrent_json"].is_enabled())
        self.assertTrue(by_id["example"].is_enabled())

    def test_provider_supports_media_capabilities(self) -> None:
        providers, _ = load_providers()
        by_id = {provider.id: provider for provider in providers}

        self.assertTrue(by_id["example"].supports(SearchQuery("Title", "movie")))
        self.assertFalse(by_id["example"].supports(SearchQuery("Title", "episode")))
        self.assertTrue(by_id["torrent_json"].supports(SearchQuery("Title", "season")))

    def test_provider_group_actions_update_settings(self) -> None:
        providers, errors = load_providers()
        self.assertEqual(errors, [])
        configs = [provider.config for provider in providers]
        settings = KodiSettings(addon=None)

        disable_all_providers(settings, configs)
        self.assertFalse(settings.get_bool("provider.torrent_json.enabled", True))
        self.assertFalse(settings.get_bool("provider.example.enabled", True))

        enable_all_providers(settings, configs)
        self.assertTrue(settings.get_bool("provider.torrent_json.enabled", False))
        self.assertTrue(settings.get_bool("provider.example.enabled", False))

        enable_torrent_providers(settings, configs)
        self.assertTrue(settings.get_bool("provider.torrent_json.enabled", False))
        self.assertFalse(settings.get_bool("provider.example.enabled", True))

        enable_pack_capable_providers(settings, configs)
        self.assertTrue(settings.get_bool("provider.torrent_json.enabled", False))
        self.assertFalse(settings.get_bool("provider.example.enabled", True))

        restore_provider_defaults(settings, configs)
        self.assertTrue(settings.get_bool("provider.torrent_json.enabled", False))
        self.assertFalse(settings.get_bool("provider.example.enabled", True))


if __name__ == "__main__":
    unittest.main()
