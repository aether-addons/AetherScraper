from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugin.program.aetherscraper"
PLUGIN_LIB = PLUGIN_ROOT / "resources" / "lib"
MODULE_ROOT = ROOT / "script.module.aetherscraper"
MODULE_LIB = MODULE_ROOT / "lib"

for path in (str(PLUGIN_LIB), str(MODULE_LIB)):
    if path not in sys.path:
        sys.path.insert(0, path)

from aetherscraper_program.routes import (  # noqa: E402
    build_url,
    external_help_text,
    parse_params,
    plugin_handle,
    root_entries,
)


class ProgramCompanionTests(unittest.TestCase):
    def test_manifest_is_program_plugin_and_depends_on_module(self) -> None:
        tree = ET.parse(PLUGIN_ROOT / "addon.xml")
        root = tree.getroot()
        self.assertEqual(root.attrib["id"], "plugin.program.aetherscraper")
        extension = root.find("extension[@point='xbmc.python.pluginsource']")
        if extension is None:
            self.fail("missing xbmc.python.pluginsource extension")
        self.assertEqual(extension.attrib["library"], "default.py")
        self.assertEqual(extension.findtext("provides"), "executable")
        imports = {item.attrib["addon"] for item in root.findall("requires/import")}
        self.assertIn("script.module.aetherscraper", imports)

    def test_module_manifest_stays_module_only(self) -> None:
        tree = ET.parse(MODULE_ROOT / "addon.xml")
        points = [item.attrib["point"] for item in tree.getroot().findall("extension")]
        self.assertIn("xbmc.python.module", points)
        self.assertNotIn("xbmc.python.pluginsource", points)
        self.assertNotIn("xbmc.service", points)

    def test_default_entrypoint_imports(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "plugin_program_aetherscraper_default", PLUGIN_ROOT / "default.py"
        )
        if spec is None or spec.loader is None:
            self.fail("default.py import spec unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(callable(module.main))

    def test_route_parse_and_url_helpers(self) -> None:
        argv = ["plugin://plugin.program.aetherscraper/", "7", "?action=providers&x=1"]
        self.assertEqual(plugin_handle(argv), 7)
        self.assertEqual(parse_params(argv), {"action": "providers", "x": "1"})
        self.assertEqual(
            build_url(argv[0], action="external_help"),
            "plugin://plugin.program.aetherscraper/?action=external_help",
        )

    def test_root_entries_cover_required_routes(self) -> None:
        actions = {entry.action for entry in root_entries()}
        self.assertTrue(
            {
                "settings",
                "providers",
                "enable_all",
                "disable_all",
                "enable_torrents",
                "enable_packs",
                "restore_defaults",
                "external_help",
                "health",
                "module_help",
            }.issubset(actions)
        )

    def test_external_help_documents_companion_mediaplay(self) -> None:
        text = external_help_text()
        self.assertIn("plugin://plugin.program.aetherscraper/?action=MediaPlay", text)
        self.assertIn("script.module.aetherscraper", text)

    def test_selector_json_points_to_companion_route(self) -> None:
        import json

        data = json.loads(
            (MODULE_ROOT / "resources" / "aetherscraper.select.json").read_text()
        )
        self.assertEqual(
            data["actions"]["play"],
            "plugin://plugin.program.aetherscraper/?action=MediaPlay",
        )
        companion = json.loads(
            (PLUGIN_ROOT / "resources" / "aetherscraper.select.json").read_text()
        )
        self.assertEqual(companion["module_id"], "script.module.aetherscraper")


if __name__ == "__main__":
    unittest.main()
