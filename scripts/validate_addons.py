#!/usr/bin/env python3
"""Validate active AetherScraper Kodi add-on source folders."""

from __future__ import annotations

import compileall
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ACTIVE_ADDONS = [
    "script.module.aetherscraper",
    "plugin.program.aetherscraper",
]


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def validate_addon(root: Path, addon_id: str) -> None:
    addon_dir = root / addon_id
    addon_xml = addon_dir / "addon.xml"
    if not addon_xml.is_file():
        fail(f"missing {addon_xml}")

    addon = ET.parse(addon_xml).getroot()
    if addon.attrib.get("id") != addon_id:
        fail(f"{addon_xml} id does not match folder name")
    if not addon.attrib.get("version"):
        fail(f"{addon_xml} missing version")

    for extension in addon.findall("extension"):
        library = extension.attrib.get("library")
        if library and not (addon_dir / library).exists():
            fail(f"{addon_xml} references missing library {library}")

    for asset_name in ("icon", "fanart"):
        for asset in addon.findall(f".//{asset_name}"):
            if not asset.text:
                fail(f"{addon_xml} has empty {asset_name} asset")
            if not asset.text.startswith(("http://", "https://")) and not (addon_dir / asset.text).is_file():
                fail(f"{addon_xml} references missing asset {asset.text}")

    if not compileall.compile_dir(str(addon_dir), quiet=1):
        fail(f"Python compile failed in {addon_dir}")


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    for addon_id in ACTIVE_ADDONS:
        validate_addon(root, addon_id)
    print("AetherScraper addon source validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
