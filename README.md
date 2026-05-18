# AetherScraper

Source/development workspace for Aether Kodi add-ons.

Install repository output lives in separate repo:

```text
https://github.com/aether-addons/AetherRepo
```

## Active add-ons

- `script.module.aetherscraper` — shared scraper/provider module
- `plugin.program.aetherscraper` — Kodi Program add-on companion UI

Reference folders such as `plugin.video.umbrella`, `plugin.video.fenlight`, and `script.module.magneto` are for compatibility research only unless explicitly promoted.

## Validate

```bash
python3 scripts/validate_addons.py .
PYTHONPATH=script.module.aetherscraper/lib:plugin.program.aetherscraper/resources/lib python3 -m pytest -q
```

## Build install repository

With sibling `../AetherRepo` checkout:

```bash
cd ../AetherRepo
python3 build_repo.py
python3 scripts/validate_repo.py .
```

Default output uses GitHub raw URLs for:

```text
https://raw.githubusercontent.com/aether-addons/AetherRepo/main/
```
