# AetherScraper vs Magneto — Missing Feature List

Status: early scaffold, not feature parity yet.

## Current AetherScraper has

- Kodi `script.module` manifest for Omega (`xbmc.python` `3.0.1`).
- Basic public API: `ScraperManager`, `BaseProvider`, `SearchQuery`, `SearchOptions`, `SourceResult`.
- Basic provider registration + enable/disable filtering.
- Basic result sorting by score + quality.
- Basic HTTP helpers.
- Basic magnet parsing/building.
- Basic torrent normalization (`TorrentItem` -> `SourceResult`).
- Example user-supplied `TorrentJsonProvider`.

## Magneto features not yet in AetherScraper

### 1. Multi-extension Kodi lifecycle

Magneto is not only a module. It declares:

- `xbmc.python.module`
- `xbmc.python.pluginsource`
- `xbmc.service`

Missing in AetherScraper:

- plugin router entrypoint
- service entrypoint
- settings monitor
- first-run profile folder setup
- version-update settings cleanup
- Kodi window-property cache/coordination

### 2. Provider discovery + dynamic loading

Magneto scans `magneto/providers/<folder>/*.py`, loads provider classes dynamically, and checks `provider.<name>` Kodi settings.

Missing in AetherScraper:

- provider folder scanning
- dynamic import loader
- per-provider Kodi setting enable checks
- provider default restore action
- enable/disable all providers action
- enable/disable all torrent providers action
- enable only pack-capable providers action

### 3. Real provider catalog

Magneto includes 24 torrent/indexer providers:

- `1337x`
- `bitmagnet`
- `bitsearch`
- `comet`
- `dmm`
- `eztv`
- `kickass2`
- `knaben`
- `mediafusion`
- `meteor`
- `nyaa`
- `piratebay`
- `prowlarr`
- `rutor`
- `tbtorznab`
- `torlock`
- `torrentdownload`
- `torrentio`
- `torrentproject2`
- `torrentsdb`
- `torrentz2`
- `torz`
- `ytsmx`
- `zilean`

Missing in AetherScraper:

- all real providers above
- site/API-specific parsers
- instance selectors for Comet/MediaFusion/Torz/Zilean/AIOStreams
- Prowlarr/Torznab token + URL providers
- TorBox Torznab support

Note: add all torrent providers.

### 4. Provider capability metadata

Magneto providers expose:

- `priority`
- `pack_capable`
- `hasMovies`
- `hasEpisodes`
- provider-specific `timeout`

Missing in AetherScraper:

- explicit movie/episode capability flags
- explicit pack-capable flag
- provider category/type metadata
- per-provider timeout override enforcement
- per-provider priority parity behavior

### 5. Movie/episode/pack search contract

Magneto provider contract uses:

- `sources(data, hostDict)`
- `sources_packs(data, hostDict)` for packs
- movie search
- episode search
- season pack search
- show pack search
- episode-range detection inside season packs

Missing in AetherScraper:

- separate movie search adapter
- separate episode search adapter
- season pack search
- show pack search
- episode-range matching
- total-season-aware show pack filtering
- host dictionary compatibility

### 6. Source validation and title matching

Magneto has large `source_utils` logic:

- aliases handling
- clean-title matching
- movie year matching
- alternate year matching
- episode `SxxExx` matching
- title/alias/year release validation
- season pack filtering
- show pack filtering
- release title cleanup
- non-ASCII/unprintable stripping

Missing in AetherScraper:

- robust title normalizer
- alias-aware matching
- year-aware validation
- episode pattern validator
- season/show pack validator
- release-name cleanup pipeline

### 7. Quality, codec, language, undesirable filters

Magneto detects/filters:

- `4K`, `1080p`, `720p`, `SD`, `SCR`, `CAM`
- CAM/SCR terms
- foreign audio
- dubbed/subbed markers
- language abbreviations
- user-selectable undesirable keywords
- default undesirable keyword database
- optional user-defined undesirable list
- HEVC filter
- AV1 filter
- Dolby Vision filter
- HDR filter
- hybrid DV/HDR behavior

Missing in AetherScraper:

- detailed release quality detection
- CAM/SCR tagging
- codec/HDR metadata parsing
- language detection
- foreign-audio filter
- undesirable keyword DB
- user-managed undesirable keywords
- HEVC/AV1/DV/HDR filter settings

### 8. Size and hash utilities

Magneto includes:

- size parsing (`MB`, `GB`, etc.)
- byte-size conversion
- base32 infohash to hex conversion
- magnet/hash extraction per provider

Missing in AetherScraper:

- robust torrent size parser
- byte conversion helper
- base32-to-hex infohash converter
- provider normalization helpers for inconsistent hash/magnet formats

### 9. Network stack

Magneto `client.py` supports:

- random user agents
- gzip
- cookies
- referer
- XHR headers
- proxy
- no-redirect mode
- partial reads/chunks
- file-size probe
- raw bytes
- SSL verify toggle
- Cloudflare/cfscrape fallback
- Sucuri fallback
- response headers/cookie/geturl outputs

Missing in AetherScraper:

- requests-like response abstraction
- session/cookie support
- redirect control
- proxy support
- configurable headers per request
- partial content/file-size probing
- gzip/encoding handling beyond urllib defaults
- browser/user-agent rotation
- retry/backoff policy config per provider

Do not implement anti-bot or access-control bypass without clear legal/safe use.

### 10. Cache and persistence

Magneto uses SQLite cache under Kodi profile:

- function-result cache with TTL hours
- profile data directory setup
- cache DB connection helpers
- undesirable keyword DB
- settings dict/window properties

Missing in AetherScraper:

- Kodi profile path helpers
- SQLite cache
- TTL cache API
- cache invalidation/cleanup
- persistent provider state
- settings mirror/cache

### 11. Concurrency and progress

Magneto uses threads to run providers and update live counts:

- threaded scraper execution
- timeout-driven progress dialog
- per-quality live counts
- provider remaining list
- cancel handling
- abort handling

Missing in AetherScraper:

- concurrent provider execution
- global timeout budget
- per-provider timeout budget
- cancellation hook
- progress callback API
- Kodi progress dialog integration
- quality counters during scrape

### 12. Player/UI integration

Magneto includes UI/player features:

- `MagnetoPlayer().source_select(params)`
- source selection window
- autoplay
- result display modes: list/wide list
- result highlighting by resolution/single color
- color picker
- Kodi ListItem metadata objects
- Cinemeta metadata lookup/navigation
- movie/series/episode navigator
- playback wrapper

Missing in AetherScraper:

- source selection UI
- autoplay ranking policy
- Kodi result-window XML/UI
- configurable result formats
- result highlight colors
- color picker actions
- metadata lookup layer
- Kodi ListItem builders
- playback adapter/resolver hook

### 13. AIOStreams integration

Magneto includes AIOStreams client:

- instance selector
- custom instance URL
- username/password auth
- `/api/v1/search`
- movie/series query by IMDb + season/episode
- source parsing into internal display format

Missing in AetherScraper:

- AIOStreams provider
- instance config
- auth config
- AIOStreams result normalization

### 14. Torznab/Prowlarr integration

Magneto includes:

- Prowlarr provider
- Prowlarr API key and URL settings
- TorBox Torznab provider
- TorBox API key setting

Missing in AetherScraper:

- generic Torznab provider
- Prowlarr adapter
- TorBox adapter
- API key storage/read helpers
- RSS/XML Torznab parser

### 15. Health/debug/support tools

Magneto includes:

- health check: test all torrent providers
- log file clear/view/upload actions
- debug enabled setting
- Kodi log vs addon log setting
- reversed addon log setting
- changelog viewer
- help/readme viewer
- clean settings action

Missing in AetherScraper:

- provider health check runner
- debug config
- addon log file backend
- log viewer/clearer/uploader
- help viewer
- changelog viewer
- settings cleanup action

### 16. Settings surface

Magneto `resources/settings.xml` exposes broad config:

- per-provider bools
- provider groups
- instance selectors
- API tokens/URLs
- undesirable filters
- language priority
- scraping timeout
- result display format
- colors
- AIOStreams setup
- debug/logging tools

Missing in AetherScraper:

- `resources/settings.xml`
- all per-provider settings
- all filter settings
- all UI/result settings
- all debug/tool settings
- settings read/write helper tied to Kodi

### 17. Packaging/assets/help

Magneto includes:

- icon assets
- help text files
- changelog
- external select JSON (`magneto.select.json`)

Missing in AetherScraper:

- icon/fanart assets
- help docs per tool/filter
- changelog file
- external player/select JSON equivalent

### 18. External consumer compatibility: Umbrella and FenLight

Magneto works as an external provider module for add-ons that import the module by add-on id suffix and call `sources`.

Umbrella local contract:

- User picks an enabled `xbmc.python.module` add-on.
- Umbrella appends `special://home/addons/<module_id>/lib` to `sys.path`.
- Umbrella imports `<module_id last segment>` and checks for `sources`.
- Scrape uses `sources()` or `sources(ret_all=True)`.
- Returned value is a list of `(provider_id, source_class)` tuples.
- Source classes expose `priority`, `pack_capable`, `hasMovies`, `hasEpisodes`.
- Source instances expose `sources(data, hostDict)` and optionally `sources_packs(data, hostDict, search_series=False, total_seasons=None, ...)`.
- Returned source dicts are filtered/sorted/deduped and may be checked against debrid cache by `hash`, `url`, `source`, `quality`, `provider`, `direct`, `debridonly`, `size`, and `info`.

FenLight local contract:

- User picks an enabled `xbmc.python.module` add-on.
- FenLight appends `special://home/addons/<module_id>/lib` to `sys.path`.
- FenLight imports `<module_id last segment>` and calls `sources(specified_folders=['torrents'])` during compatibility selection.
- Scrape uses `sources(data, hostDict)` and `sources_packs(data, hostDict, search_series=True, total_seasons=<n>)`.
- Returned source dicts are post-processed for `hash`, display name, quality, info labels, size in GB, `package`, `episode_start`, `episode_end`, and `last_season`.
- FenLight may pass `debrid_service` and `debrid_token` in data; these must remain secret and only be used for authorized APIs.

Missing in AetherScraper / needs verification:

- `sources(specified_folders=None, ret_all=False)` signature parity.
- `specified_folders=['torrents']` support for FenLight selection.
- One provider tuple per AetherScraper provider where practical, not only a single aggregate adapter.
- Stable provider ids matching returned source `provider` values.
- Per-provider priority/capability/enable behavior visible to external consumers.
- FenLight fixture tests and Kodi manual validation.
- Umbrella fixture tests for `ret_all=True` and per-provider tuple behavior.
- External source dict field audit against both consumers.
- `resources/aetherscraper.select.json` and `MediaPlay` route for Magneto-style player-selector compatibility.

## 2026-05-18 parity audit additions

Audit sources: local `script.module.magneto`, `plugin.video.umbrella`, and `plugin.video.fenlight` references.

### Magneto settings IDs that must be covered or deliberately mapped

Magneto settings IDs include provider booleans and exact integration names: `module.provider`, `provider.<name>`, `provider.aiostreams`, `provider.prowlarr`, `provider.tbtorznab`, `comet.url`, `mediafusion.url`, `torz.url`, `zilean.url`, `prowlarr.token`, `prowlarr.url`, `torbox.token`, `filter.foreign.single.audio`, `filter.undesirables`, `debug.enabled`, `debug.location`, `debug.reversed`, `results.list_format`, `highlight.type`, per-quality highlight/display settings, `results.language_filter`, `results.language`, `scraping_timeout`, `aiostreams_instance`, `aio.*_url`, `aio.username`, and `aio.password`.

AetherScraper may keep safer/internal setting names, but parity work must provide compatibility mapping where Umbrella/FenLight/Magneto-style code expects behavior equivalent to these settings. Provider enablement especially must be visible to external consumers as if `provider.<id>` flags existed.

### Magneto provider contract details to preserve

Every external provider tuple should behave like Magneto provider classes:

- class attrs: `priority`, `pack_capable`, `hasMovies`, `hasEpisodes`; some providers also carry `timeout` and internal queues
- methods: `sources(data, hostDict)` and, where packs are supported, `sources_packs(data, hostDict, search_series=False, total_seasons=None, ...)`
- stable provider id equal to tuple id and returned `provider` field
- pack-aware classes must support normal episode, season pack, and show pack execution without collapsing provider labels into one aggregate adapter

### External source dictionary field audit

Magneto providers and Umbrella/FenLight post-processors use more than the minimal fields. AetherScraper source dicts should populate or safely omit with documented behavior:

- core: `provider`, `source`, `name`, `name_info`, `quality`, `language`, `url`, `info`, `direct`, `debridonly`, `hash`, `size`
- pack: `package`, `episode_start`, `episode_end`, `last_season`
- torrent metadata: `seeders`, `true_size`, `usenet`
- consumer-added/cache fields may include `external`, `scrape_provider`, `display_name`, `extraInfo`, `size_label`, `cache_provider`, and `debrid`

Size must be GB float for Umbrella/FenLight external dicts. Invalid or unknown size should be `0`/missing, not bogus parsed title digits.

### Umbrella/FenLight compatibility obligations

Compatibility target is same user flow as Magneto: choose `script.module.aetherscraper` as external provider/scraper, add-on appends `<addon>/lib`, imports `aetherscraper`, and calls `sources`.

Required behavior:

- `sources(specified_folders=None, ret_all=False)` accepts both arguments.
- `sources(ret_all=True)` returns disabled providers too for Umbrella selection/config views.
- `sources(specified_folders=['torrents'])` works for FenLight selection.
- `hasMovies`, `hasEpisodes`, and `pack_capable` control provider filtering before scrape.
- FenLight debrid payload keys `debrid_service` and `debrid_token` remain secret and never appear in logs/source dicts.
- Pack responses let FenLight filter episode membership by `episode_start <= episode <= episode_end` and show membership by `last_season >= season`.
- Real Kodi validation with both add-ons remains required before declaring compatibility complete.

### Module-only packaging vs Magneto plugin/service parity

Magneto declares plugin and service extension points. AetherScraper currently stays `xbmc.python.module` only because adding plugin/service extensions to `script.module.aetherscraper` caused Kodi install-structure failure. This means Magneto-style `plugin://script.module.aetherscraper/?action=MediaPlay` / selector JSON behavior is not proven equivalent until one of these is done:

- split plugin/service behavior into companion add-ons, or
- find a Kodi-safe manifest/package structure that supports module + plugin/service, or
- document selector/player route as unsupported non-goal.

This is a compatibility gap for AIOStreams/player-selector style use even if Umbrella/FenLight import scraping works.

### Safety non-goals still excluded from parity

Do not copy Magneto `cfscrape`, Cloudflare/Sucuri challenge handling, CAPTCHA solver hooks, or access-control bypass code. Record these as intentionally unsupported, not missing implementation bugs.

## Suggested implementation order

1. Add Kodi settings/profile/storage layer.
2. Add provider metadata: `capabilities`, `pack_capable`, `media_types`, `priority`, `timeout`.
3. Add robust torrent parsing helpers: quality, size, infohash, title cleanup.
4. Add movie/episode/season-pack query contract.
5. Add generic Torznab/Prowlarr provider first (user-authorized, configurable, safer than piracy-site scraping).
6. Add concurrency + timeout + progress callback API.
7. Add cache layer.
8. Add undesirable/language/codec filters.
9. Add health check + debug logs.
10. Add optional Kodi UI/player adapter if this module should be user-facing like Magneto.
11. Verify external-provider compatibility with Umbrella and FenLight before declaring parity.
12. Add external player/select JSON and `MediaPlay` route if matching Magneto's AIOStreams/player-selector integration is in scope.

## Feature parity verdict

Not full Magneto parity yet. AetherScraper now has many foundations and first provider/external-bridge implementations, but parity still requires remaining provider catalog work, real Kodi validation with Umbrella + FenLight, exact external field/settings behavior checks, assets/release packaging, and resolution of module-only packaging vs Magneto plugin/service/player-selector behavior.

2026-05-18 audit note: AetherScraper has `sources(specified_folders=None, ret_all=False)`, per-provider external adapters, selector JSON, and `MediaPlay` helper code, but compatibility is not complete until non-core source dict fields/settings mappings are verified and `plugin://script.module.aetherscraper/?action=MediaPlay` is proven executable in Kodi or explicitly descoped.
