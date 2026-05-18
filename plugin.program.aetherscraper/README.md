# AetherScraper Tools

`plugin.program.aetherscraper` is the visible Program add-on companion for `script.module.aetherscraper`.

The scraper core stays in the module add-on so Kodi installs it as an Add-on library. This companion exposes safe UI routes only and depends on the module instead of duplicating provider or scraping code.

## Repository builds

Develop this launcher in `../AetherScraper/plugin.program.aetherscraper/`. Kodi repository output is generated in sibling folder `../AetherScraperRepo/`.

After changes, bump this add-on's `addon.xml` version and rebuild:

```bash
cd ../AetherScraperRepo
python3 build_repo.py
```

Install/update through `repository.aetherscraper`; Kodi installs `script.module.aetherscraper` as dependency.

## Routes

- Root menu: settings, provider summary, provider group actions, help, health check.
- Settings: opens `script.module.aetherscraper` settings.
- Providers: shows provider enabled state, type, priority, and pack support.
- Provider actions: enable all, disable all, enable torrent providers, enable pack-capable providers, restore defaults. Kodi confirmation is required.
- External help: Umbrella/FenLight setup notes.
- `MediaPlay`: delegates to the module playback resolver.

## External selector URL

Prefer:

```text
plugin://plugin.program.aetherscraper/?action=MediaPlay
```

The old module-shaped URL is not guaranteed because `script.module.aetherscraper` intentionally has no `xbmc.python.pluginsource` extension.

## Install order

Install `script.module.aetherscraper` first, then install this companion add-on.
