from __future__ import annotations

import unittest

from aetherscraper import (
    GlobalConfig,
    SearchOptions,
    SearchQuery,
    SourceResult,
    detect_language,
    detect_quality,
    inspect_release,
)
from aetherscraper.manager import ScraperManager
from aetherscraper.provider import BaseProvider


class StaticProvider(BaseProvider):
    def __init__(self, results):
        super().__init__()
        self._results = results

    def search(self, query, options):
        return list(self._results)


class Phase4ReleaseFilterTests(unittest.TestCase):
    def test_quality_cam_scr_codec_hdr_and_language_detection(self) -> None:
        release = inspect_release("Movie.2024.2160p.WEB-DL.x265.DoVi.HDR.TrueFrench")

        self.assertEqual(detect_quality("Movie 4K UHD"), "4k")
        self.assertEqual(release.quality, "4k")
        self.assertTrue(release.is_hevc)
        self.assertEqual(release.codec, "hevc")
        self.assertTrue(release.has_dolby_vision)
        self.assertTrue(release.has_hdr)
        self.assertEqual(release.hdr, "dv+hdr")
        self.assertEqual(release.language, "fr")
        self.assertTrue(release.is_foreign_audio)
        self.assertTrue(inspect_release("Movie CAMRip").is_cam)
        self.assertTrue(inspect_release("Movie DVDSCR").is_scr)
        self.assertEqual(detect_language("Movie dual audio"), "multi")

    def test_undesirable_keywords_include_default_and_custom(self) -> None:
        release = inspect_release(
            "Movie.1080p.WEB-DL.Sample.Watermark",
            undesirable_keywords=["sample", "watermark", "custom"],
        )

        self.assertEqual(release.undesirable_keywords, ["sample", "watermark"])

    def test_manager_enriches_results_and_applies_release_filters(self) -> None:
        provider = StaticProvider(
            [
                SourceResult(
                    provider="static",
                    title="Movie.2024.1080p.WEB-DL.x265.DoVi.HDR",
                    url="https://example.test/hevc",
                ),
                SourceResult(
                    provider="static",
                    title="Movie.2024.720p.WEB-DL.x264.English",
                    url="https://example.test/ok",
                ),
                SourceResult(
                    provider="static",
                    title="Movie.2024.1080p.WEB-DL.x264.French",
                    url="https://example.test/fr",
                ),
                SourceResult(
                    provider="static",
                    title="Movie.2024.1080p.WEB-DL.x264.Sample",
                    url="https://example.test/sample",
                ),
            ]
        )
        manager = ScraperManager(config=GlobalConfig(), providers=[provider])

        results = manager.search(
            SearchQuery("Movie"),
            SearchOptions(
                include_disabled=True,
                allow_hevc=False,
                allow_dolby_vision=False,
                allow_hdr=False,
                allow_foreign_audio=False,
            ),
        )

        self.assertEqual(
            [result.url for result in results], ["https://example.test/ok"]
        )
        self.assertEqual(results[0].quality, "720p")
        self.assertEqual(results[0].metadata["detected_language"], "en")

    def test_global_config_from_settings_maps_filter_toggles(self) -> None:
        from aetherscraper.kodi.settings import KodiSettings

        settings = KodiSettings(
            fallback={
                "filter_hevc": "true",
                "filter_av1": "true",
                "filter_dolby_vision": "true",
                "filter_hdr": "true",
                "filter_foreign_audio": "true",
                "undesirable_keywords": "sample, watermark",
            }
        )
        config = GlobalConfig.from_kodi_settings(settings)
        options = config.to_search_options()

        self.assertFalse(options.allow_hevc)
        self.assertFalse(options.allow_av1)
        self.assertFalse(options.allow_dolby_vision)
        self.assertFalse(options.allow_hdr)
        self.assertFalse(options.allow_foreign_audio)
        self.assertEqual(options.undesirable_keywords, ["sample", "watermark"])


if __name__ == "__main__":
    unittest.main()
