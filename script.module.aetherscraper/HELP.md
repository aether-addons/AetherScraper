# AetherScraper Help

Use AetherScraper only with sources you own, control, or have permission to access.

## Common support actions

- Run provider health checks to verify enabled/configured providers respond.
- View support logs from the add-on profile folder.
- Clear support logs only after explicit confirmation.
- Reset settings only after explicit confirmation.
- Consumer add-ons can import support helpers for startup, health checks, help, changelog, log viewing, and settings dialogs.
- Startup helpers create the profile folder and record version changes when called; they never delete data automatically.
- Umbrella external-provider setup: enable/configure AetherScraper providers, then in Umbrella use Tools > Providers > Enable External Providers and choose `script.module.aetherscraper`.
- FenLight external-scraper setup: choose `script.module.aetherscraper`; AetherScraper supports `sources(specified_folders=['torrents'])` and returns per-provider adapters.
- Program launcher: install `plugin.program.aetherscraper` after this module to show AetherScraper under Kodi Program add-ons. The module stays under Add-on libraries by design.
- Player selector setup: `resources/aetherscraper.select.json` is packaged and points to `plugin://plugin.program.aetherscraper/?action=MediaPlay` for direct `url`/`path` playback params only.
- Prowlarr setup: use a full Prowlarr Torznab endpoint URL, or use Prowlarr root URL plus indexer ID; API key and category list are optional settings.
- Torrentio setup: enable the provider and keep the default base URL, or set a compatible Stremio add-on root/config path. Movie/episode searches need IMDb IDs.

Secrets such as API keys, cookies, tokens, and authorization headers are redacted before support logs are written and are not mirrored to Kodi window properties.
