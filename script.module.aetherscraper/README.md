# AetherScraper

Configurable Kodi `script.module` scraper framework.

## Safety / scope

Use this module only for sources you own, have permission to access, or that publish legal/public content. It does not bypass DRM, paywalls, auth, geo restrictions, or access controls.

## Repository builds

Source development stays in `../AetherScraper/`. Kodi repository output is generated in sibling folder `../AetherRepo/`.

After changes, bump this add-on's `addon.xml` version and rebuild:

```bash
cd ../AetherRepo
python3 build_repo.py
```

Install/update through the AetherRepo feed; it packages this module and the `plugin.program.aetherscraper` launcher only.

## Consumer add-on dependency

```xml
<requires>
  <import addon="xbmc.python" version="3.0.1" />
  <import addon="script.module.aetherscraper" version="0.1.2" />
</requires>
```

## Basic use

```python
from aetherscraper import ScraperManager, SearchQuery, load_providers

providers, load_errors = load_providers()
manager = ScraperManager.from_defaults()
for provider in providers:
    manager.register(provider)

query = SearchQuery(title="Big Buck Bunny", year=2008, media_type="movie")
results = manager.search(query)

for result in results:
    print(result.provider, result.title, result.url)
```

## Config layers

Order, highest wins:

1. Per-call `SearchOptions`
2. Kodi settings via `KodiSettings` / `GlobalConfig.from_kodi_settings()`
3. Provider config passed by consumer
4. JSON files in `resources/providers.d/*.json`
5. Built-in defaults

## Kodi settings and profile storage

`resources/settings.xml` exposes safe foundation settings: debug logging, scrape timeout, max results, provider timeout, provider retries, release filters, and initial provider enable toggles.

```python
from aetherscraper import GlobalConfig, KodiSettings, first_run_setup

settings = KodiSettings()
config = GlobalConfig.from_kodi_settings(settings)
first_run_setup(version="0.1.0")
```

Outside Kodi, `KodiSettings` uses in-memory fallback defaults and optional `AETHERSCRAPERS_*` environment variables. Runtime state is stored under `special://profile/addon_data/script.module.aetherscraper/` when Kodi is available, or a user profile fallback outside Kodi. Version-update cleanup is recorded with `record_version_update()` and never deletes data automatically.

## Cache and persistence

`SQLiteCache` stores disposable cache data under the add-on profile cache folder (`cache/aetherscraper.sqlite3`). It provides JSON values, TTL expiry, explicit invalidation/cleanup, persistent provider state, and a small undesirable-keyword database. It never performs destructive cleanup unless a caller invokes `delete()`, `invalidate()`, `cleanup()`, or `clear()`.

```python
from aetherscraper import SQLiteCache

cache = SQLiteCache.from_profile()
cache.set("search", "movie:big-buck-bunny", {"result_count": 3}, ttl=3600)
print(cache.get("search", "movie:big-buck-bunny"))

cache.set_provider_state("prowlarr", {"last_indexer": 7})
cache.set_undesirable_keywords(["cam", "watermark"])
cache.cleanup()
```

Do not store API keys, cookies, auth headers, or signed URLs in cache/provider state unless the consumer add-on has a documented redaction and cleanup policy.

## Health, debug, and support tools

Phase 11 adds module-safe support helpers for consumer add-ons and Kodi UI layers:

- `run_provider_health_checks()` runs provider diagnostics and returns structured success/failure records.
- `DebugConfig.from_settings()` reads debug/support settings.
- `AddonLogBackend` writes redacted logs under profile storage (`logs/aetherscraper.log`).
- `log_text()`, `help_text()`, and `changelog_text()` provide viewer text hooks; `show_text()` opens a Kodi text viewer when Kodi UI is available.
- `clear_log(confirm=True)` and `cleanup_settings(confirm=True)` require explicit confirmation before destructive cleanup.

```python
from aetherscraper import AddonLogBackend, run_provider_health_checks, clear_log

summary = run_provider_health_checks(providers)
backend = AddonLogBackend.from_profile()
backend.write(f"health ok={summary.ok} failed={summary.failed}")
print(backend.tail())
clear_log(backend, confirm=True)
```

Optional log uploading is intentionally not implemented. Support logs may still contain sensitive context despite redaction, so users/consumer add-ons should review content before sharing.

## Torrent mode

Torrent support is provider-agnostic and legal-source only. Built-in `TorrentJsonProvider` searches a user-managed JSON list of magnet or `.torrent` links.

Phase 14 real-provider expansion includes:

- `YtsMxProvider` (`provider.ytsmx.enabled`, disabled by default): uses the YTS.mx public `list_movies.json` API for movie torrents only, normalizes torrent hashes to magnets, and does not implement any anti-bot or access-control bypass. Users can override `provider.ytsmx.base_url` for testing or compatible mirrors.
- `ProwlarrProvider` (`provider.prowlarr.enabled`, disabled by default): uses a user-owned Prowlarr Torznab endpoint. Set `provider.prowlarr.base_url` to a full Torznab endpoint, or set it to the Prowlarr root URL plus `provider.prowlarr.indexer_id` so AetherScraper builds `/<indexer_id>/api`. Optional `provider.prowlarr.api_key` and comma-separated `provider.prowlarr.categories` are passed as Torznab query parameters. No challenge, CAPTCHA, Cloudflare, or access-control bypass behavior is implemented.
- `TbTorznabProvider` (`provider.tbtorznab.enabled`, disabled by default): uses the TorBox/TB Torznab endpoint (`https://search-api.torbox.app/torznab/api` by default) with the user's TorBox API key. Magneto-compatible aliases `provider.tbtorznab` and `torbox.token` are supported. No challenge, CAPTCHA, Cloudflare, or access-control bypass behavior is implemented.
- `TorrentioProvider` (`provider.torrentio.enabled`, disabled by default): uses Torrentio-compatible public Stremio `stream/{type}/{id}.json` responses for movie and episode torrents. It requires IMDb IDs (`tt...`) because Torrentio stream routes are ID-based. Optional `provider.torrentio.base_url` and `provider.torrentio.config_path` support compatible instances/config paths. No API key, browser challenge, scraping, CAPTCHA, Cloudflare, or access-control bypass behavior is implemented.

```python
from aetherscraper import ScraperManager, SearchQuery, SearchOptions
from aetherscraper.providers.torrent_json import TorrentJsonProvider

manager = ScraperManager.from_defaults()
manager.register(TorrentJsonProvider(path="/path/to/torrents.json"))

results = manager.search(
    SearchQuery(title="Big Buck Bunny", media_type="movie"),
    SearchOptions(min_quality="720p")
)
```

`torrents.json`:

```json
{
  "items": [
    {
      "title": "Big Buck Bunny 1080p",
      "magnet": "magnet:?xt=urn:btih:REPLACE_WITH_LEGAL_INFOHASH&dn=Big%20Buck%20Bunny",
      "quality": "1080p",
      "seeders": 10,
      "language": "en"
    }
  ]
}
```

## Provider discovery and group actions

`load_providers()` scans `aetherscraper.providers`, imports provider modules safely, and returns `(providers, load_errors)`. Load errors are structured as `ProviderLoadError(module, message)` so consumer add-ons can report failures without crashing a full scrape.

Provider enable settings use `provider.<id>.enabled`. Helpers support common group actions:

```python
from aetherscraper import (
    KodiSettings,
    disable_all_providers,
    enable_all_providers,
    enable_pack_capable_providers,
    enable_torrent_providers,
    restore_provider_defaults,
)

settings = KodiSettings()
configs = [provider.config for provider in providers]
enable_torrent_providers(settings, configs)
```

## Movie, episode, and pack search contract

`ScraperManager` exposes adapters for common Kodi/Magneto-style searches:

```python
manager.search_movie("Big Buck Bunny", year=2008, host_dict={"torrent": ["magnet"]})
manager.search_episode("Example Show", season=1, episode=2)
manager.search_season_pack("Example Show", season=1)
manager.search_show_pack("Example Show", total_seasons=3)
```

Adapters build `SearchQuery.media_type` values `movie`, `episode`, `season`, or `show`. Legacy `hostDict` data is carried in `SearchOptions.extra["host_dict"]` for consumer/provider compatibility. Pack searches only return results that look like season/show packs; helpers include `detect_episode_range()`, `detect_season_range()`, `is_season_pack()`, and `is_show_pack()`.

## Title and source validation

`ScraperManager` validates normalized provider results before sorting. Validation checks cleaned title/alias tokens, movie year (including optional `SearchQuery.extra["alternate_years"]`), `SxxExx` episode numbers, and season/show pack shape.

```python
from aetherscraper import normalize_title, title_matches, validate_result

print(normalize_title("Show.Title.2024.S01E02.1080p.x265"))  # show title
print(title_matches("Edge.of.Tomorrow.2014", "Live Die Repeat", ["Edge of Tomorrow"]))
```

If provider output includes a wrong title, wrong explicit year, wrong episode number, or wrong pack shape, manager drops it. Releases without a year are allowed when title matches; explicit mismatched years are rejected.

## Provider contract

Subclass `BaseProvider` and implement `search(self, query, options)`. Provider metadata documents capabilities and controls discovery/filtering:

- `provider_type`: e.g. `torrent`, `direct`, `generic`
- `priority`: lower runs first
- `pack_capable`: supports season/show packs
- `has_movies` / `has_episodes`
- `media_types`: accepted query media types (`movie`, `episode`, `season`, `show`)
- `timeout`: per-provider timeout default

Torrent helpers normalize inconsistent provider fields before conversion:

- `parse_size()` / `bytes_to_size()` convert common size text (`1.5 GB`, `700 MiB`) to bytes and display labels.
- `normalize_info_hash()` accepts BTIH hex or base32 and returns lowercase hex.
- `extract_info_hash()` reads hashes from magnets or provider text.
- `clean_release_title()` removes common release noise for later validation.
- `normalize_torrent_item()` maps provider aliases (`name`, `magnet_uri`, `seeds`, `resolution`, etc.) into `TorrentItem`.

Release metadata helpers detect quality (`4K`, `1080p`, `720p`, `SD`), CAM/SCR tags, HEVC/AV1, Dolby Vision/HDR, likely language, foreign audio, and undesirable keywords. `ScraperManager` enriches `SourceResult.metadata` before filtering.

```python
from aetherscraper import SearchOptions, inspect_release

release = inspect_release("Movie.2024.2160p.x265.DoVi.HDR.TrueFrench")
print(release.quality, release.codec, release.hdr, release.language)

options = SearchOptions(
    allow_hevc=False,
    allow_av1=False,
    allow_dolby_vision=False,
    allow_hdr=False,
    allow_foreign_audio=False,
    undesirable_keywords=["sample", "watermark"],
)
```

Kodi filter settings default to allowing codecs/HDR/foreign audio, while built-in undesirable keyword filtering is enabled. Custom undesirable keywords are comma-separated. Consumer add-ons can override per search with `SearchOptions`.

## Network helpers

`aetherscraper.http` provides a safe urllib-based network layer for provider adapters. It supports response objects, session cookies, redirect control, proxies, per-request headers, browser/XHR/referer header presets, gzip decoding, byte-range requests, file-size probes, retry/backoff config, and optional random user-agent selection.

```python
from aetherscraper import HttpClient, NetworkOptions

client = HttpClient(NetworkOptions(timeout=10, retries=1, allow_redirects=True))
response = client.request("https://example.invalid/feed.json", headers={"Accept": "application/json"})
print(response.status_code, response.text)
```

Providers can derive network options from `ProviderConfig` and per-call `SearchOptions.extra["network"]`:

```python
client = self.http_client(options)
response = client.partial_content(url, 0, 1023)
size = client.file_size(url)
```

Safety note: browser-style headers and user-agent selection are compatibility presets only. They do not solve challenges, bypass CAPTCHAs, evade paywalls, or bypass access controls.

## Concurrency, timeout, and progress

`GlobalConfig(concurrent=True)` or Kodi setting `concurrent_scraping` runs providers in parallel. `scrape_timeout` caps the whole scrape budget; `provider_timeout` caps each provider and is passed into `SearchOptions.timeout` for provider/network helpers. Python cannot forcibly kill arbitrary provider code, so cancelled/timed-out thread work may finish in the background; manager stops waiting and returns accepted results.

```python
from aetherscraper import CancelToken, SearchOptions

progress_events = []
cancel_token = CancelToken()
results = manager.search(
    query,
    SearchOptions(extra={
        "concurrent": True,
        "scrape_timeout": 30,
        "provider_timeout": 10,
        "progress_callback": progress_events.append,
        "cancel_token": cancel_token,
    })
)
```

Progress callbacks receive `ScrapeProgress` events: `started`, `provider_started`, `provider_finished`, `provider_failed`, `provider_timed_out`, `cancelled`, and `finished`. Events include completed/total providers plus quality counters. Kodi progress dialog integration is intentionally left to consumer/plugin layers so this module remains safe outside Kodi.

## Kodi lifecycle hooks

The add-on is packaged as a module-only add-on (`xbmc.python.module`). Lifecycle, support, and UI helpers are importable library functions for consumer add-ons; AetherScraper does not register plugin-source or service extension points in `addon.xml`. For visible Kodi Program add-ons navigation, install the companion `plugin.program.aetherscraper` launcher after this module.

- `run_startup()` performs safe first-run profile setup and version-change recording when called by a consumer add-on.
- `SettingsMonitor` can be embedded by a consumer service if settings-change polling is needed.
- Version changes only set `cleanup_required`; cache/settings deletion still requires explicit confirmation through support APIs.
- Window properties mirror non-secret coordination settings under `script.module.aetherscraper.*`. API keys, auth tokens, cookies, and similar secrets are never mirrored.

```python
from aetherscraper import run_startup, sync_settings_to_window

status = run_startup(version="0.1.0")
sync_settings_to_window()
```

## Kodi UI and playback helpers

Phase 13 adds reusable UI/player helpers without turning the module into a full `plugin.video` add-on. Consumer add-ons can build playable Kodi `ListItem` rows, show source-selection dialogs, apply autoplay ranking, format colored source labels, resolve playback through a hook, and optionally overlay metadata from their own lookup layer.

```python
from aetherscraper import (
    KodiUiSettings,
    add_source_directory,
    choose_autoplay_source,
    resolve_to_kodi,
)

ui_settings = KodiUiSettings.from_settings()
best = choose_autoplay_source(results, ui_settings)

# Listing route in a consumer plugin.video add-on:
add_source_directory(handle, results, base_url, settings=ui_settings)

# Resolver route: direct sources play immediately; non-direct sources need a resolver hook.
resolve_to_kodi(handle, best, resolver=my_resolver)
```

`kodi_stream_url()` only appends safe non-secret playback headers (`User-Agent`, `Referer`, `Origin`, `Accept`, and `Accept-Language`). Authorization, cookies, API keys, and auth tokens are never added to Kodi pipe headers by these helpers. Metadata lookup is intentionally a consumer-provided callable; this module does not call TMDb/IMDb or store lookup API keys.

UI settings include colored source labels, result format (`list` or `wide`), highlight type (`resolution` or `single_color`), quality/direct highlight colors, priority language filtering, and autoplay policy (`score_quality_size`, `quality_score_size`, or `size_quality_score`). `pick_highlight_color()` provides a Kodi color-picker hook when Kodi UI is available. Magneto-style setting ids are accepted as aliases where practical: `scraping_timeout`, `provider.<id>`, `filter.foreign.single.audio`, `results.language_filter`, `results.language`, `results.list_format`, `highlight.type`, and `scraper_*_highlight` map to AetherScraper settings.

## Umbrella / external-provider bridge

Umbrella validates external provider modules by appending this add-on `lib` path, importing `aetherscraper`, and checking for a callable `sources`. AetherScraper now exposes that bridge:

```python
import aetherscraper

provider_entries = aetherscraper.sources(ret_all=True)
# [("prowlarr", <class ...>), ("torrentio", <class ...>), ...]
fenlight_entries = aetherscraper.sources(specified_folders=["torrents"], ret_all=True)
```

`UmbrellaSourceAdapter` implements Magneto/Umbrella/FenLight-style `sources(data, hostDict)` and `sources_packs(data, hostDict, ...)` methods. `sources(specified_folders=None, ret_all=False)` returns one adapter tuple per AetherScraper provider, preserving provider id, priority, movie/episode flags, pack flag, and folder aliases such as `torrents`. Each generated adapter filters `ScraperManager` to that provider id.

The bridge maps Umbrella and FenLight movie/episode/pack payloads to `ScraperManager` search adapters, including `tvshowtitle`, aliases, IMDb/TMDb ids, and optional `debrid_service` / `debrid_token` in `SearchOptions.extra`. It converts `SourceResult` objects to source dictionaries with `provider`, `source`, `name`, `name_info`, `quality`, `language`, `url`, `info`, `direct`, `debridonly`, `size` in GB, `true_size`, torrent `hash`, torrent `seeders`, `usenet` when applicable, and pack metadata (`episode_start`, `episode_end`, `last_season`, `package`) where available.

Setup in Umbrella: Tools > Providers > Enable External Providers, choose `script.module.aetherscraper` where the host expects an importable external-provider module. Enable and configure AetherScraper providers in AetherScraper settings first; `sources(ret_all=True)` exposes providers for validation, while default `sources()` only returns enabled providers.

Setup in FenLight: use external scraper picker with `script.module.aetherscraper`; FenLight can call `sources(specified_folders=['torrents'])` to list torrent adapters.

Program launcher: install `plugin.program.aetherscraper` to make AetherScraper visible under Kodi Program add-ons. Its root menu opens module settings, provider summaries, confirmed provider group actions, external setup help, health checks, and module help. For player-selector actions, prefer `plugin://plugin.program.aetherscraper/?action=MediaPlay`; `plugin://script.module.aetherscraper` remains unsupported as a plugin route until manually proven safe in Kodi.

Metadata helpers for consumers: `external_provider_summaries()`, `torrent_provider_summaries()`, `hoster_provider_summaries()`, and `pack_capable_provider_summaries()`.

`resources/aetherscraper.select.json` is packaged for AIOStreams/player-selector style discovery and now points playback/settings actions at `plugin.program.aetherscraper`. `dispatch_action()` includes a `MediaPlay` action for consumer add-ons that choose to expose it from a real plugin route; it only accepts direct `url`/`path` parameters and does not resolve protected or secret-bearing URLs.

## Authorized providers

Built-in authorized adapters prefer user-configured APIs over public-site scraping:

- `TorznabProvider` parses generic Torznab/Newznab RSS/XML.
- `ProwlarrProvider` wraps a user-owned Prowlarr Torznab endpoint; either supply a full endpoint URL or a root URL plus indexer ID.
- `TorBoxTorznabProvider` wraps an authorized TorBox Torznab endpoint.
- `AIOStreamsProvider` parses AIOStreams-style JSON from a configured instance.

Settings are disabled by default and include endpoint URLs plus API/auth values. Secrets are read from Kodi settings or explicit config only and are not logged intentionally.

```python
from aetherscraper import KodiSettings, SearchOptions, SearchQuery
from aetherscraper.providers.torznab import ProwlarrProvider

settings = KodiSettings(fallback={
    "provider.prowlarr.base_url": "http://127.0.0.1:9696",
    "provider.prowlarr.indexer_id": "1",
    "provider.prowlarr.api_key": "USER_API_KEY",
    "provider.prowlarr.categories": "2000,5000",
})
provider = ProwlarrProvider(settings=settings)
results = provider.search(SearchQuery("Big Buck Bunny", year=2008), SearchOptions())
```

For torrent providers, return `torrent_to_source(self.id, TorrentItem(...))` or normalize raw provider dictionaries first.

```python
from aetherscraper import BaseProvider, ProviderConfig, normalize_torrent_item, torrent_to_source

class MyTorrentProvider(BaseProvider):
    config = ProviderConfig(
        id="my_torrents",
        name="My Torrents",
        enabled=True,
        provider_type="torrent",
        pack_capable=True,
        media_types=["movie", "episode", "season"],
    )

    def search(self, query, options):
        raw = {"title": query.title, "magnet": "magnet:?xt=urn:btih:LEGAL_INFOHASH"}
        item = normalize_torrent_item(raw)
        return [torrent_to_source(self.id, item)]
```
