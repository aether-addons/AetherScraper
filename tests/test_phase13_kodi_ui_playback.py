from __future__ import annotations

import unittest
from typing import Any, cast

from aetherscraper import (
    KodiSettings,
    KodiUiSettings,
    SourceResult,
    add_source_directory,
    build_resolved_listitem,
    build_source_listitem,
    choose_autoplay_source,
    dispatch_action,
    kodi_stream_url,
    pick_highlight_color,
    resolve_playback_source,
    resolve_to_kodi,
    select_source,
    with_metadata_lookup,
)


class FakePlugin:
    def __init__(self) -> None:
        self.content: tuple[int, str] | None = None
        self.items: list[tuple[str, object, bool]] = []
        self.ended: tuple[int, bool, bool] | None = None
        self.resolved: tuple[int, bool, object] | None = None

    def setContent(self, handle: int, content: str) -> None:  # noqa: N802
        self.content = (handle, content)

    def addDirectoryItems(  # noqa: N802
        self,
        handle: int,
        items: list[tuple[str, object, bool]],
        totalItems: int = 0,
    ) -> None:
        self.items.extend(items)
        self.total_items = totalItems

    def endOfDirectory(  # noqa: N802
        self,
        handle: int,
        succeeded: bool = True,
        updateListing: bool = False,
        cacheToDisc: bool = True,
    ) -> None:
        self.ended = (handle, succeeded, cacheToDisc)

    def setResolvedUrl(self, handle: int, succeeded: bool, item: object) -> None:  # noqa: N802
        self.resolved = (handle, succeeded, item)


class FakeDialog:
    def __init__(self, index: int | None = 0, color: str | None = "red") -> None:
        self.index = index
        self.color = color

    def select(self, heading: str, labels: list[str]) -> int | None:
        self.heading = heading
        self.labels = labels
        return self.index

    def colorpicker(self, heading: str, current: str) -> str | None:
        self.color_heading = heading
        self.current = current
        return self.color


class KodiUiPlaybackTests(unittest.TestCase):
    def source(self, **overrides: object) -> SourceResult:
        values = {
            "provider": "demo",
            "title": "Big Buck Bunny 1080p",
            "url": "https://example.invalid/video.mp4",
            "quality": "1080p",
            "media_type": "movie",
            "size": 1_500_000_000,
            "language": "en",
            "score": 90.0,
            "direct": True,
            "metadata": {"year": "2008", "plot": "Open movie"},
        }
        values.update(overrides)
        return SourceResult(**values)  # type: ignore[arg-type]

    def test_listitem_builder_formats_label_and_sets_playable_flag(self) -> None:
        source = self.source()
        url, item, is_folder = build_source_listitem(
            source,
            base_url="plugin://script.module.aetherscraper/",
            source_id="7",
            settings=KodiUiSettings(color_1080p="cyan"),
        )

        self.assertIn("route=play", url)
        self.assertIn("source_id=7", url)
        self.assertFalse(is_folder)
        self.assertEqual(item.properties["IsPlayable"], "true")
        self.assertIn("[COLOR cyan]", item.label)
        self.assertEqual(item.info["video"]["year"], 2008)

    def test_source_selection_and_autoplay_ranking(self) -> None:
        low = self.source(title="Low", quality="720p", score=100.0)
        high = self.source(title="High", quality="1080p", score=80.0)

        selected = select_source([low, high], dialog=FakeDialog(index=1))
        autoplay = choose_autoplay_source(
            [low, high], KodiUiSettings(autoplay_policy="quality_score_size")
        )

        self.assertEqual(selected, high)
        self.assertEqual(autoplay, high)

    def test_add_source_directory_ends_uncached_video_listing(self) -> None:
        plugin = FakePlugin()

        ok = add_source_directory(
            42,
            [self.source()],
            "plugin://script.module.aetherscraper/",
            xbmcplugin_module=plugin,
        )

        self.assertTrue(ok)
        self.assertEqual(plugin.content, (42, "videos"))
        self.assertEqual(len(plugin.items), 1)
        self.assertEqual(plugin.ended, (42, True, False))

    def test_stream_url_filters_secret_headers(self) -> None:
        url = kodi_stream_url(
            "https://example.invalid/video.mp4",
            {
                "User-Agent": "Kodi",
                "Authorization": "Bearer SECRET",
                "Cookie": "session=SECRET",
            },
        )

        self.assertIn("User-Agent=Kodi", url)
        self.assertNotIn("SECRET", url)
        self.assertNotIn("Authorization", url)
        self.assertNotIn("Cookie", url)

    def test_resolver_hook_and_kodi_resolution(self) -> None:
        plugin = FakePlugin()
        unresolved = self.source(direct=False, url="plugin-source")
        resolved = self.source(url="https://example.invalid/final.mp4")

        self.assertEqual(resolve_playback_source(unresolved), None)
        ok = resolve_to_kodi(
            1,
            unresolved,
            resolver=lambda source: resolved,
            xbmcplugin_module=plugin,
        )

        self.assertTrue(ok)
        if plugin.resolved is None:
            self.fail("resolver did not call setResolvedUrl")
        handle, succeeded, item = plugin.resolved
        self.assertEqual(handle, 1)
        self.assertTrue(succeeded)
        self.assertEqual(cast(Any, item).path, "https://example.invalid/final.mp4")

    def test_resolved_listitem_uses_metadata_lookup_overlay(self) -> None:
        item = build_resolved_listitem(
            self.source(metadata={}),
            metadata_lookup=lambda source: {"plot": "Looked up", "year": 2008},
        )
        enriched = with_metadata_lookup(
            self.source(metadata={}), lambda source: {"thumb": "thumb.jpg"}
        )

        self.assertEqual(item.info["video"]["plot"], "Looked up")
        self.assertEqual(enriched.metadata["thumb"], "thumb.jpg")

    def test_color_picker_updates_setting_and_plugin_action_exists(self) -> None:
        settings = KodiSettings(fallback={"ui_color_1080p": "blue"})
        color = pick_highlight_color(settings, dialog=FakeDialog(color="green"))
        result = dispatch_action("pick_color", settings=settings)

        self.assertEqual(color, "green")
        self.assertEqual(settings.get_string("ui_color_1080p"), "green")
        self.assertTrue(result.ok)

    def test_magneto_style_ui_settings_aliases(self) -> None:
        settings = KodiUiSettings.from_settings(
            KodiSettings(
                fallback={
                    "results.list_format": "wide",
                    "highlight.type": "single_color",
                    "scraper_single_highlight": "magenta",
                },
                addon=None,
            )
        )
        url, item, is_folder = build_source_listitem(
            self.source(title="Movie", quality="720p"), settings=settings
        )

        self.assertEqual(url, "https://example.invalid/video.mp4")
        self.assertFalse(is_folder)
        self.assertIn("  •  ", cast(Any, item).label)
        self.assertTrue(cast(Any, item).label.startswith("[COLOR magenta]"))


if __name__ == "__main__":
    unittest.main()
