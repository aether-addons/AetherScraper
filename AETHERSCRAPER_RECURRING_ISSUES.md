# AetherScraper Recurring Issues Log

Purpose: store problems, decisions, fixes, and gotchas that may recur across chat sessions. Use this when context memory would otherwise be lost.

Related docs:

- Standards: [`AGENTS.md`](AGENTS.md)
- Plan: [`AETHERSCRAPER_FEATURE_PARITY_PLAN.md`](AETHERSCRAPER_FEATURE_PARITY_PLAN.md)
- Checklist: [`AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md`](AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md)
- Missing features source: [`AETHERSCRAPER_MISSING_FEATURES.md`](AETHERSCRAPER_MISSING_FEATURES.md)

## When to add an entry

Add an entry when:

- Same bug or confusion could happen again.
- Fix required investigation and should not be rediscovered.
- Kodi-specific behavior was surprising.
- Provider/API behavior was undocumented or changed.
- Tooling/build/test command had a non-obvious requirement.
- A safety/legal boundary decision was made.
- A compatibility decision was made.

Do not add one-off trivial typos.

## Entry format

```md
## YYYY-MM-DD — Short issue title

Status: open | fixed | workaround | decision
Area: Kodi | provider | network | settings | packaging | tests | safety | docs | other

### Symptom

What happened.

### Cause

Why it happened.

### Fix / Decision

What solved it or what standard was chosen.

### Prevention

How future agents should avoid it.

### References

- File/path/commit/checklist item/link
```

## Issues

## 2026-05-18 — TorBox Torznab duplicate provider/settings entry

Status: fixed
Area: settings

### Symptom

Kodi settings/provider list showed duplicate TorBox Torznab entries after adding Magneto-compatible `tbtorznab`.

### Cause

A legacy internal `TorBoxTorznabProvider` with id `torbox_torznab` remained discoverable and had visible settings next to the new Magneto-compatible `TbTorznabProvider` id `tbtorznab`. TorBox settings also reused localization ids already used by UI highlight color settings.

### Fix / Decision

Remove discoverable legacy `TorBoxTorznabProvider` and remove `provider.torbox_torznab.*` from `resources/settings.xml`/defaults. Preserve legacy user config by reading `provider.torbox_torznab.*` as aliases for `provider.tbtorznab.*`, including Kodi cases where new canonical settings return default values. Move TorBox/TB strings to unique ids `30150`-`30155`.

### Prevention

When replacing provider ids for Magneto parity, do not keep old provider classes discoverable unless intentionally shown as separate providers. Add alias-only migration in `KodiSettings` instead.

### References

- `script.module.aetherscraper/lib/aetherscraper/providers/torznab.py`
- `script.module.aetherscraper/lib/aetherscraper/kodi/settings.py`
- `script.module.aetherscraper/resources/settings.xml`
- `tests/test_phase14_tbtorznab_provider.py`

## 2026-05-18 — tbtorznab uses TorBox fixed endpoint and Magneto aliases

Status: fixed
Area: provider

### Symptom

Initial AetherScraper tbtorznab draft treated TorBox Torznab like a generic user-configured Torznab endpoint only.

### Cause

Magneto's `tbtorznab` provider has provider id `tbtorznab`, enable setting `provider.tbtorznab`, token setting `torbox.token`, fixed base `https://search-api.torbox.app`, endpoint `/torznab/api`, and sends `limit` plus IMDb/season/episode params.

### Fix / Decision

Implement `TbTorznabProvider` with default endpoint `https://search-api.torbox.app/torznab/api`, alias support for `provider.tbtorznab` and `torbox.token`, shared Torznab parser, shared torrent normalization, `limit` derived from `SearchOptions.max_results`, full `tt...` IMDb ids, no generic `q`/`year` params, and magnet URLs built from Torznab `infohash` values.

### Prevention

Before adding Phase 14 providers, inspect matching Magneto provider file and settings IDs; preserve safe compatible IDs/aliases without copying unsafe or broad exception behavior.

### References

- `examples/script.module.magneto/lib/magneto/providers/torrents/tbtorznab.py`
- `script.module.aetherscraper/lib/aetherscraper/providers/torznab.py`
- `script.module.aetherscraper/lib/aetherscraper/kodi/settings.py`
- `tests/test_phase14_tbtorznab_provider.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 14

## 2026-05-18 — Magneto setting aliases must override fallback defaults

Status: fixed
Area: settings

### Symptom

Magneto-style alias settings such as `scraping_timeout` could be ignored outside Kodi because canonical fallback defaults like `scrape_timeout=30` were read first.

### Cause

`KodiSettings` merges built-in defaults with fallback values. Alias lookups checked canonical keys before aliases, so default canonical values masked user-provided alias values.

### Fix / Decision

Normalize known aliases into canonical fallback keys during `KodiSettings` initialization when the caller did not provide the canonical key. Keep dynamic provider aliases (`provider.<id>` ↔ `provider.<id>.enabled`) in lookup candidates.

### Prevention

When adding compatibility aliases, test both direct canonical ids and legacy alias ids against fallback settings, not only Kodi XML defaults.

### References

- `script.module.aetherscraper/lib/aetherscraper/kodi/settings.py`
- `tests/test_phase1_settings_storage.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 13.5

## 2026-05-18 — Umbrella uncached seeder sort expects seeders key

Status: fixed
Area: Kodi

### Symptom

Umbrella can sort uncached torrent results with `k['seeders']`, which can raise/display poorly if external source dicts omit `seeders`.

### Cause

AetherScraper external bridge only emitted core Magneto-style keys plus hash/pack metadata, while Umbrella/FenLight consumers also use optional compatibility fields.

### Fix / Decision

Emit torrent `seeders` with safe default `0`, `true_size` for trusted size values, and `usenet` for Usenet metadata. Keep title-derived size as `true_size=False`.

### Prevention

When changing external source dict conversion, validate optional consumer fields, not only core keys.

### References

- `script.module.aetherscraper/lib/aetherscraper/external.py`
- `tests/test_phase13_5_umbrella_bridge.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 13.5

## 2026-05-18 — MediaPlay selector route belongs to companion plugin

Status: decision
Area: Kodi

### Symptom

Selector JSON previously pointed `MediaPlay` at `plugin://script.module.aetherscraper/?action=MediaPlay`, but the module add-on has no plugin-source extension.

### Cause

Kodi plugin URLs are only guaranteed for add-ons declaring `xbmc.python.pluginsource`. `script.module.aetherscraper` is intentionally module-only after invalid-structure install failures.

### Fix / Decision

Point selector playback/settings actions at `plugin://plugin.program.aetherscraper/`. Keep module route unsupported unless manual Kodi testing proves it safe.

### Prevention

Do not publish new player-selector URLs using `plugin://script.module.aetherscraper`. Use the companion Program add-on for routes and keep core scraping code in the module.

### References

- `script.module.aetherscraper/resources/aetherscraper.select.json`
- `plugin.program.aetherscraper/resources/aetherscraper.select.json`
- `plugin.program.aetherscraper/resources/lib/aetherscraper_program/routes.py`

## 2026-05-18 — Program add-ons visibility requires companion add-on

Status: decision
Area: Kodi

### Symptom

`script.module.aetherscraper` does not appear under Kodi Program add-ons, while `examples/script.module.magneto` may appear there.

### Cause

AetherScraper is intentionally module-only with `xbmc.python.module`, so Kodi lists it as an Add-on library. Magneto mixes `xbmc.python.pluginsource`, `xbmc.service`, and `xbmc.python.module` in one `script.module.*` manifest, which can make it visible but previously caused invalid-structure risk for AetherScraper packaging.

### Fix / Decision

Do not re-add plugin/source or service extension points to `script.module.aetherscraper`. Add a separate companion `plugin.program.aetherscraper` for visible Program add-ons UI and optional safe route ownership.

### Prevention

Keep module, plugin, and service lifecycles split by add-on family. If a user-visible launcher is needed, implement/package a sibling `plugin.program.*` add-on depending on the module.

### References

- `AETHERSCRAPER_FEATURE_PARITY_PLAN.md` Phase 13.6
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 13.6
- `script.module.aetherscraper/addon.xml`

## 2026-05-17 — script.module install failed invalid structure

Status: fixed
Area: packaging

### Symptom

Kodi failed to install `script.module.aetherscraper` zip with invalid structure.

### Cause

`addon.xml` for a `script.module.*` add-on declared `xbmc.python.pluginsource` and `xbmc.service` extensions in addition to `xbmc.python.module`. Kodi add-on family/extension structure must stay consistent; module add-ons should expose module code only.

### Fix / Decision

Removed plugin-source and service extensions from `addon.xml`. Keep plugin/service helper code as importable library functions only unless split into separate `plugin.*` / `service.*` add-ons later.

### Prevention

Do not add `xbmc.python.pluginsource` or `xbmc.service` extension points to `script.module.*` manifests. Package zip must have one top-level `script.module.aetherscraper/` folder with `addon.xml` directly inside.

### References

- `script.module.aetherscraper/addon.xml`
- `script.module.aetherscraper-0.1.0.zip`

## 2026-05-16 — Umbrella size values could show N/A or impossible GB values

Status: fixed
Area: Kodi

### Symptom

Umbrella sometimes showed AetherScraper scraper rows with `N/A` size or impossible values such as `246800.48 GB` / `1864647.59 GB`.

### Cause

Shared `parse_size()` treated any mixed text with digits as a byte count when no size unit existed, so release titles could become bogus sizes. Fractional numeric sizes such as `2.5` were treated as bytes instead of likely GB, producing near-zero size in Umbrella. Some provider adapters selected the first non-empty size alias, so values like `N/A` in `size` hid valid `size_bytes`. Umbrella conversion only used `SourceResult.size`, so size embedded in torrent titles could still display as N/A.

### Fix / Decision

`parse_size()` now only accepts unit-bearing strings or numeric-only byte strings, treats fractional numeric values as GB, and rejects sizes above a generous 50 TiB video cap. `parse_size_candidates()` tries ordered aliases and skips invalid fields. Torrent/AIO normalization prefer byte aliases, then human size, then title text. Umbrella source conversion derives size from result size, metadata aliases, size label, then title, and clamps impossible values.

### Prevention

Provider adapters should send unit-bearing size strings or byte counts. Do not parse arbitrary release-title text as size. Never stop on `N/A`; try all size aliases. Keep external source dictionaries bounded before handing values to Umbrella/FenLight.

### References

- `script.module.aetherscraper/lib/aetherscraper/torrent.py`
- `script.module.aetherscraper/lib/aetherscraper/external.py`
- `tests/test_phase3_torrent_normalization.py`
- `tests/test_phase13_5_umbrella_bridge.py`

## 2026-05-17 — Empty string defaults break Kodi settings load

Status: fixed
Area: settings

### Symptom

Kodi logged repeated `CSettingString: error reading the default value` for empty string settings such as `undesirable_keywords`, Torznab/Prowlarr URLs/API keys, AIOStreams URL/token, and Torrentio config path.

### Cause

Modern Kodi settings XML did not accept `<default></default>` for these empty string settings in this add-on context.

### Fix / Decision

Use self-closing empty defaults (`<default />`) and add `<allowempty>true</allowempty>` constraints for empty string settings.

### Prevention

For optional string settings, use `<default />` plus `allowempty=true`; do not use paired empty default tags.

### References

- `script.module.aetherscraper/resources/settings.xml`

## 2026-05-16 — Some direct/AIO stream sizes showed N/A

Status: fixed
Area: provider

### Symptom

Some external-player rows showed size as `N/A` even when provider payload included a human-readable size such as `1.5 GB`, `2.5 G`, or `850 M`.

### Cause

AIOStreams direct-result normalization used `int()`-only parsing for `size`, unlike torrent normalization. Short units without `B` were also not recognized by `parse_size()`.

### Fix / Decision

AIOStreams direct results now use shared `parse_size()`. `parse_size()` accepts short units `K`, `M`, `G`, and `T`; longer binary units still match before short units so `MiB` remains binary.

### Prevention

Provider adapters should use shared size parsing for all provider size fields, not local `int()` parsing, unless field is guaranteed bytes.

### References

- `script.module.aetherscraper/lib/aetherscraper/providers/aiostreams.py`
- `script.module.aetherscraper/lib/aetherscraper/torrent.py`
- `tests/test_phase3_torrent_normalization.py`
- `tests/test_phase8_authorized_providers.py`

## 2026-05-16 — External bridge now returns per-provider adapters

Status: decision
Area: Kodi

### Symptom

FenLight calls `sources(specified_folders=['torrents'])`; Umbrella calls `sources()` / `sources(ret_all=True)`. Aggregate-only `aetherscraper` adapter lost provider ids, priorities, folder filtering, and per-provider cache labels.

### Cause

Magneto-style external contracts expect `sources(specified_folders=None, ret_all=False)` and one `(provider_id, source_class)` tuple per provider where possible.

### Fix / Decision

`aetherscraper.sources()` now accepts `specified_folders`, filters aliases such as `torrents`, and returns generated per-provider adapter classes backed by `ScraperManager` provider-id filtering. `ret_all=True` includes disabled providers for picker validation; default `sources()` returns enabled providers only. `resources/aetherscraper.select.json` and direct-url-only `MediaPlay` alias were added for selector parity without adding resolver bypass behavior.

### Prevention

Future bridge changes must preserve per-provider tuple shape, folder aliases, source dict keys, pack metadata, and disabled-provider behavior for external picker validation.

### References

- `script.module.aetherscraper/lib/aetherscraper/external.py`
- `script.module.aetherscraper/lib/aetherscraper/kodi/plugin.py`
- `script.module.aetherscraper/resources/aetherscraper.select.json`
- `tests/test_phase13_5_umbrella_bridge.py`
- `tests/test_phase12_kodi_lifecycle.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 13.5

## 2026-05-15 — Torrentio provider requires IMDb stream IDs

Status: decision
Area: provider

### Symptom

Phase 14 catalog includes `torrentio`, but Torrentio's Stremio stream API is ID-route based rather than free-text search based.

### Cause

Torrentio-compatible endpoints return streams at `/stream/movie/{imdb}.json` and `/stream/series/{imdb}:{season}:{episode}.json`. Without IMDb IDs, the provider cannot build a safe precise query.

### Fix / Decision

Implement `TorrentioProvider` as disabled-by-default movie/episode torrent provider requiring `SearchQuery.imdb_id`. Support optional base URL and config path. Normalize `streams[]` entries with `infoHash`, trackers, filename/title, size, and seed metadata into magnet-backed `SourceResult` rows. Do not add scraping, browser challenge, CAPTCHA, Cloudflare, or access-control bypass behavior.

### Prevention

Future Torrentio work should keep searches ID-based unless a documented public API supports safe free-text search. Keep `pack_capable=False` unless a clear pack contract is added.

### References

- `script.module.aetherscraper/lib/aetherscraper/providers/torrentio.py`
- `tests/test_phase14_torrentio_provider.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 14

## 2026-05-15 — Prowlarr provider uses user-owned Torznab endpoints

Status: decision
Area: provider

### Symptom

Phase 14 catalog includes `prowlarr`, but Prowlarr can expose many indexers and endpoint styles.

### Cause

Prowlarr Torznab access is user-owned/configured and may be copied as a full indexer Torznab URL or represented as a root URL plus indexer ID. API key and categories are optional query parameters.

### Fix / Decision

Keep `ProwlarrProvider` as disabled-by-default Torznab integration. Accept a full `provider.prowlarr.base_url`, or build `/<indexer_id>/api` from root URL plus `provider.prowlarr.indexer_id`. Pass optional `api_key` and comma-separated categories as Torznab params. Hide API-key input in Kodi settings. Do not add public scraping or anti-bot/access-control bypass behavior.

### Prevention

Future Prowlarr work should stay in authorized endpoint mode unless a separate safe-use decision approves other APIs. Do not log API keys or full signed/auth URLs.

### References

- `script.module.aetherscraper/lib/aetherscraper/providers/torznab.py`
- `tests/test_phase14_prowlarr_provider.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 14

## 2026-05-15 — YTS.mx provider is movie-only public JSON API

Status: decision
Area: provider

### Symptom

Phase 14 catalog includes many torrent providers with mixed API/scrape behavior.

### Cause

YTS.mx has a documented `list_movies.json` endpoint for movie torrents, but no episode or pack support. It returns torrent hashes inside movie objects rather than ready AetherScraper source rows.

### Fix / Decision

Implement `YtsMxProvider` as disabled-by-default, movie-only provider. Read optional `provider.ytsmx.base_url`; no API key. Normalize each YTS torrent to a magnet-backed `SourceResult` with info hash/seed/size/language metadata. Do not add browser challenge, scraping, CAPTCHA, Cloudflare, or access-control bypass behavior.

### Prevention

Keep YTS provider `has_episodes=False` and `pack_capable=False`. Future catalog providers must document capability flags and safe-use notes before enablement.

### References

- `script.module.aetherscraper/lib/aetherscraper/providers/ytsmx.py`
- `tests/test_phase14_ytsmx_provider.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 14

## 2026-05-15 — Umbrella bridge uses one adapter source class

Status: decision
Area: Kodi

### Symptom

Umbrella external-provider contract wants a `sources` callable returning `(provider_id, source_class)` entries, while AetherScraper internally has many providers behind `ScraperManager`.

### Cause

Umbrella calls each external source class with Magneto-style `sources(data, hostDict)` / `sources_packs(...)`. Returning each AetherScraper provider directly would duplicate manager validation/filtering and require many compatibility shims.

### Fix / Decision

Expose one `("aetherscraper", UmbrellaSourceAdapter)` entry from `aetherscraper.sources()`. Adapter maps Umbrella payloads to AetherScraper manager search adapters and maps `SourceResult` back to Umbrella dictionaries. `sources(ret_all=True)` always returns adapter for validation; default `sources()` returns adapter only if at least one AetherScraper provider is enabled.

### Prevention

Keep Umbrella compatibility logic centralized in `aetherscraper.external`; do not make individual AetherScraper providers implement Umbrella APIs unless contract changes.

### References

- `script.module.aetherscraper/lib/aetherscraper/external.py`
- `tests/test_phase13_5_umbrella_bridge.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 13.5

## 2026-05-15 — Umbrella external-provider validation requires `aetherscraper.sources()`

Status: open
Area: Kodi

### Symptom

Umbrella reports `SCRIPT.MODULE.AETHERSCRAPERS is not a valid module selection` when selecting AetherScraper as an external provider module.

### Cause

Umbrella external-provider picker appends `special://home/addons/<addonid>/lib`, imports the last add-on id segment (`aetherscraper`), and validates that module has a `sources` callable. Current AetherScraper public API does not expose a Magneto/Umbrella-style `sources()` function or source adapter classes.

### Fix / Decision

Added Phase 13.5 plan/checklist for an Umbrella/external-provider compatibility bridge. Implement `aetherscraper.sources()` and adapters that translate Umbrella payloads to AetherScraper `SearchQuery`/`ScraperManager`, then translate `SourceResult` back to Umbrella-compatible source dictionaries. Keep AIOStreams-style `*.select.json` as separate optional selector metadata.

### Prevention

Do not treat Kodi video-addon visibility as external-provider compatibility. Umbrella compatibility must pass its import contract and scrape-source contract, not only `addon.xml` `<provides>video</provides>`.

### References

- `examples/plugin.video.umbrella/resources/lib/modules/tools.py`
- `examples/plugin.video.umbrella/resources/lib/modules/sources.py`
- `AETHERSCRAPER_FEATURE_PARITY_PLAN.md` Phase 13.5
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 13.5

## 2026-05-15 — Kodi service crash from collections.abc Callable type alias

Status: fixed
Area: Kodi

### Symptom

Kodi service startup crashed with `TypeError: 'ABCMeta' object is not subscriptable` at `SettingsChangedCallback = Callable[[KodiSettings], None]`.

### Cause

Some Kodi Python runtimes expose `collections.abc.Callable` without runtime generic subscripting. Type aliases are evaluated at import time even with `from __future__ import annotations`.

### Fix / Decision

Runtime-evaluated type aliases now use `typing.Callable`/`typing.Mapping` and `typing.Optional` where needed. Kept `collections.abc` imports for annotation-only uses.

### Prevention

Do not use `collections.abc` generics in import-time type aliases for Kodi modules. If alias must be evaluated, use `typing` aliases and add ruff `UP035`/`UP007` comments explaining Kodi compatibility.

### References

- `script.module.aetherscraper/lib/aetherscraper/kodi/lifecycle.py`
- `script.module.aetherscraper/lib/aetherscraper/kodi/ui.py`
- `script.module.aetherscraper/lib/aetherscraper/progress.py`

## 2026-05-15 — HTTP retry ResourceWarning from unclosed HTTPError response

Status: fixed
Area: network

### Symptom

Network-stack tests passed but emitted non-fatal `ResourceWarning: unclosed <socket.socket ...>` during interpreter cleanup.

### Cause

`urllib.request` raises `HTTPError` with an attached response/socket for retryable HTTP statuses such as 503. Retry path caught the exception but did not close the attached error response before issuing the next request.

### Fix / Decision

`HttpClient._with_retries()` now calls `HTTPError.close()` before retry/raise cleanup. Do not suppress `ResourceWarning`; close error responses.

### Prevention

When catching `HTTPError`, close or fully consume its response before retrying. Validate with warnings enabled when changing `aetherscraper.http`.

### References

- `script.module.aetherscraper/lib/aetherscraper/http.py`
- `tests/test_phase7_network_stack.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 7

## 2026-05-15 — Cache stores JSON payloads, not secrets

Status: decision
Area: cache

### Symptom

Phase 10 adds persistent SQLite cache/provider state under profile storage.

### Cause

Kodi profile files are plaintext on disk. Cache/provider state can be tempting for API tokens, cookies, signed URLs, or auth headers.

### Fix / Decision

`SQLiteCache` stores JSON payloads for disposable cache data, provider state, and undesirable keywords only. Public docs warn consumers not to store secrets unless they own explicit redaction/cleanup policy. Destructive cache cleanup/invalidation remains explicit caller action.

### Prevention

When adding providers, do not persist API keys, cookies, auth headers, or signed URLs in `SQLiteCache`. Keep secrets in Kodi settings or documented user config paths and redact logs.

### References

- `script.module.aetherscraper/lib/aetherscraper/cache.py`
- `script.module.aetherscraper/README.md`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 10

## 2026-05-15 — Timed-out provider threads cannot be forcibly killed safely

Status: decision
Area: providers

### Symptom

Phase 9 needs global and per-provider timeout budgets for concurrent scraping.

### Cause

Python threads cannot safely terminate arbitrary provider code once running. `Future.cancel()` only cancels work that has not started.

### Fix / Decision

Concurrent manager stops waiting on timed-out/cancelled providers, emits timeout/cancel progress, and returns accepted results. Providers must honor `SearchOptions.timeout` and shared network helpers for real request timeouts. Consumer UI should treat timeout progress as scrape-level completion, not guaranteed provider-thread termination.

### Prevention

Do not add unsafe thread-kill behavior. Keep provider/network code timeout-aware and cooperative.

### References

- `script.module.aetherscraper/lib/aetherscraper/manager.py`
- `script.module.aetherscraper/lib/aetherscraper/progress.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 9

## 2026-05-15 — Provider setting typed getters only bool for enabled

Status: fixed
Area: settings

### Symptom

Phase 8 provider URL/API key string settings would be read through Kodi boolean getter if all `provider.*` keys were treated as booleans.

### Cause

`KodiSettings._typed_getter()` previously returned `getSettingBool` for every `provider.*` key.

### Fix / Decision

Only `provider.*.enabled` uses `getSettingBool`. Provider URL/API/auth settings use string getter fallback.

### Prevention

When adding provider secrets or URLs, keep key suffixes explicit and avoid broad `provider.*` typed getter rules.

### References

- `script.module.aetherscraper/lib/aetherscraper/kodi/settings.py`
- `script.module.aetherscraper/resources/settings.xml`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 8

## 2026-05-15 — Phase 7 browser headers are compatibility only

Status: decision
Area: safety

### Symptom

Network parity needs browser/XHR/referer presets and optional user-agent rotation.

### Cause

Some legitimate APIs or feeds expect common headers, but these features can be confused with anti-bot bypass.

### Fix / Decision

`aetherscraper.http` only sets static compatibility headers and optional cosmetic user-agent choice. It does not solve challenges, bypass CAPTCHAs, evade paywalls, or bypass access controls.

### Prevention

Do not add Cloudflare/Sucuri/challenge handling or access-control bypass behavior without explicit legal/safe-use review.

### References

- `script.module.aetherscraper/lib/aetherscraper/http.py`
- `script.module.aetherscraper/README.md`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 7

## 2026-05-15 — Phase 6 validation allows missing release years

Status: decision
Area: provider

### Symptom

Many provider titles include release title and quality but omit movie/show year.

### Cause

Strict year requirement would drop otherwise valid sources when title/alias match is strong and provider metadata has no explicit year.

### Fix / Decision

`year_matches()` rejects explicit mismatched years but allows titles with no detected year. Alternate years are accepted through `SearchQuery.extra["alternate_years"]`.

### Prevention

Do not require year presence unless provider later exposes reliable structured year metadata. Keep explicit wrong years rejected.

### References

- `script.module.aetherscraper/lib/aetherscraper/validation.py`
- `tests/test_phase6_validation.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 6

## 2026-05-15 — Phase 5 pack search stays heuristic until title validators land

Status: decision
Area: provider

### Symptom

Phase 5 needs season/show pack search before Phase 6 title/source validators exist.

### Cause

Pack detection can identify obvious `S01E01-E08`, `S01-S03`, `Season 1`, and `Complete Series` patterns, but cannot yet prove title/year/alias correctness.

### Fix / Decision

`ScraperManager.search_season_pack()` and `search_show_pack()` filter with shared heuristics in `aetherscraper.packs`. Legacy Magneto `hostDict` compatibility passes through `SearchOptions.extra["host_dict"]`. Strong title/year validation remains Phase 6 work.

### Prevention

Do not overfit provider-specific pack parsing in manager. Add strict alias/year/SxxExx validators in Phase 6 and keep Phase 5 helpers as lightweight pack-shape detection.

### References

- `script.module.aetherscraper/lib/aetherscraper/packs.py`
- `script.module.aetherscraper/lib/aetherscraper/manager.py`
- `tests/test_phase5_search_contract.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 5

## 2026-05-15 — Release filters enrich before option filtering

Status: decision
Area: provider

### Symptom

Phase 4 filter settings need codec/HDR/language/undesirable decisions, but many providers only return `SourceResult.title` and no parsed metadata.

### Cause

Provider output is inconsistent and Phase 3 normalization does not guarantee release metadata fields.

### Fix / Decision

`ScraperManager._normalize()` enriches each `SourceResult` with `aetherscraper.release.enrich_source_result()` before `allowed_by_options()`. Kodi filter settings default to allowing HEVC/AV1/DV/HDR/foreign audio. Built-in undesirable keyword filtering is enabled by default and can be disabled with `use_default_undesirables`.

### Prevention

Keep release parsing shared and manager-level unless provider-specific metadata is more reliable. Do not require every provider to duplicate codec/HDR/language parsing.

### References

- `script.module.aetherscraper/lib/aetherscraper/release.py`
- `script.module.aetherscraper/lib/aetherscraper/manager.py`
- `script.module.aetherscraper/resources/settings.xml`
- `tests/test_phase4_release_filters.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 4

## 2026-05-15 — Profile cleanup must be explicit

Status: decision
Area: settings

### Symptom

Feature parity needs first-run/version-update lifecycle and cache cleanup behavior.

### Cause

Kodi add-on profile data may contain user-managed provider files, state, and future secrets/settings mirrors.

### Fix / Decision

`record_version_update()` records `cleanup_required=true` when version changes but never deletes data. Destructive cleanup must be implemented later as an explicit, confirmed user action.

### Prevention

Keep automatic migrations non-destructive. Add confirmation UI before any cache/settings cleanup action.

### References

- `script.module.aetherscraper/lib/aetherscraper/kodi/storage.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 1

## 2026-05-15 — Provider discovery must not fail whole scrape

Status: decision
Area: provider

### Symptom

Phase 2 dynamic provider imports can fail because optional provider code may have missing deps or parser bugs.

### Cause

Provider modules are discovered and imported at runtime from `aetherscraper.providers`.

### Fix / Decision

`load_providers()` returns `(providers, load_errors)` and records `ProviderLoadError(module, message)` instead of raising for normal import/instantiation failures.

### Prevention

Keep provider import errors structured and non-fatal. Consumer UI/logging may surface module + sanitized message, but should not stop all providers unless explicit fail-fast behavior is added.

### References

- `script.module.aetherscraper/lib/aetherscraper/loader.py`
- `tests/test_phase2_provider_discovery.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 2

## 2026-05-15 — Torrent size commas are ambiguous

Status: fixed
Area: provider

### Symptom

Phase 3 size parser must accept both decimal comma (`1,5 GB`) and thousands comma (`1,024 MB`).

### Cause

Naively replacing every comma with a dot turns `1,024 MB` into `1.024 MB` instead of `1024 MB`.

### Fix / Decision

`parse_size()` treats a comma followed by exactly three trailing digits as a thousands separator; otherwise it treats comma as decimal separator.

### Prevention

Keep tests for both `1.5 GB` and `1,024 MB` when changing size parsing.

### References

- `script.module.aetherscraper/lib/aetherscraper/torrent.py`
- `tests/test_phase3_torrent_normalization.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 3

## 2026-05-15 — Support logs stay local; uploads omitted

Status: decision
Area: safety

### Symptom

Phase 11 includes health/debug support tooling and asks for optional log uploader decision.

### Cause

Support logs can contain sensitive context even with redaction. Uploading logs would create data-sharing and consent risks outside module scope.

### Fix / Decision

Add local profile-backed support log backend with default redaction and explicit log clearing. Do not implement log upload. Consumers may build their own upload/review flow if they handle consent and redaction.

### Prevention

Do not add automatic or one-click upload from `script.module.aetherscraper` without explicit safety review. Keep destructive log/settings cleanup behind confirmation.

### References

- `script.module.aetherscraper/lib/aetherscraper/support.py`
- `tests/test_phase11_support_tools.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 11

## 2026-05-15 — Multi-extension lifecycle stays support-only before UI phase

Status: decision
Area: Kodi

### Symptom

Phase 12 needed Magneto-style module/plugin/service lifecycle, but AetherScraper is still primarily a reusable `script.module` and Phase 13 owns media UI/player behavior.

### Cause

Adding a full video plugin surface during lifecycle work would mix support/lifecycle plumbing with source selection and playback design.

### Fix / Decision

Keep `xbmc.python.module`, add `xbmc.python.pluginsource` with `<provides>executable</provides>` for support/lifecycle actions, and add `xbmc.service` for startup/settings monitoring. The plugin router handles startup, health, help, changelog, log, and settings actions only. No playable media listings or resolver behavior were added.

### Prevention

Do not add video ListItems, playback resolution, or source-selection windows to Phase 12 helpers. Implement those in Phase 13 with Kodi UI/player validation.

### References

- `script.module.aetherscraper/addon.xml`
- `script.module.aetherscraper/default.py`
- `script.module.aetherscraper/service.py`
- `script.module.aetherscraper/lib/aetherscraper/kodi/plugin.py`
- `script.module.aetherscraper/lib/aetherscraper/kodi/lifecycle.py`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 12

## 2026-05-15 — Phase 13 metadata lookup remains consumer-owned

Status: decision
Area: Kodi

### Symptom

Phase 13 needed a metadata lookup layer for Kodi UI/player display.

### Cause

Adding TMDb/IMDb calls inside `script.module.aetherscraper` would introduce new API keys, cache policy, rate-limit behavior, and user-visible provider behavior before real provider catalog work.

### Fix / Decision

`with_metadata_lookup()` accepts an optional consumer-provided callable and merges returned metadata onto `SourceResult.metadata`. The module does not call external metadata services or store lookup API keys. Consumers own lookup settings, cache, and legal/API terms.

### Prevention

Do not add built-in metadata service calls to Kodi UI helpers without explicit plan/checklist update and settings/secrets review. Keep `SourceResult.metadata` and consumer lookup callables as the Phase 13 boundary.

### References

- `script.module.aetherscraper/lib/aetherscraper/kodi/ui.py`
- `tests/test_phase13_kodi_ui_playback.py`
- `script.module.aetherscraper/README.md`
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 13

## 2026-05-16 — FenLight external scraper needs Magneto `sources` signature

Status: open
Area: Kodi

### Symptom

Feature-parity checklist treated the external-provider bridge as Umbrella-only and marked most Phase 13.5 items complete. FenLight compatibility was not fully planned.

### Cause

FenLight's external scraper picker differs from Umbrella: it imports the module by add-on id suffix, then calls `sources(specified_folders=['torrents'])` during compatibility validation. Current AetherScraper `aetherscraper.sources()` only accepts `ret_all=False`, so FenLight selection would fail with an unexpected keyword argument.

### Fix / Decision

Expand Phase 13.5 scope to Umbrella + FenLight + Magneto external-provider parity. Plan `sources(specified_folders=None, ret_all=False)`, `specified_folders=['torrents']`, per-provider adapter tuples, source-dict field audits, FenLight fixture tests, and real Kodi validation. Keep debrid tokens secret and do not add anti-bot/access-control bypass behavior.

### Prevention

Before declaring external-provider parity, test all consumer import paths: `sources()`, `sources(ret_all=True)`, and `sources(specified_folders=['torrents'])`. Compare returned tuples and source dicts against local Umbrella/FenLight scrape code, not only Magneto.

### References

- `examples/plugin.video.fenlight/resources/lib/indexers/dialogs.py`
- `examples/plugin.video.fenlight/resources/lib/scrapers/external.py`
- `examples/plugin.video.umbrella/resources/lib/modules/tools.py`
- `examples/plugin.video.umbrella/resources/lib/modules/sources.py`
- `examples/script.module.magneto/lib/magneto/__init__.py`
- `AETHERSCRAPER_FEATURE_PARITY_PLAN.md` Phase 13.5
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 13.5

## 2026-05-18 — Parity doc must include Magneto external edge fields and module-only route gap

Status: open
Area: Kodi

### Symptom

AetherScraper had many Phase 13.5 items checked, but parity documentation did not explicitly track every Magneto/Umbrella/FenLight compatibility edge: Magneto setting semantics, non-core source dict keys, and selector JSON route executability.

### Cause

Earlier parity work focused on minimal import/scrape contracts. Magneto also exposes exact settings behavior, provider class attrs, optional source keys (`seeders`, `true_size`, `usenet`), and plugin/service routes. AetherScraper is currently module-only after Kodi install failure with plugin/service extensions, so `plugin://script.module.aetherscraper/?action=MediaPlay` is not proven equivalent to Magneto.

### Fix / Decision

Expanded `AETHERSCRAPER_MISSING_FEATURES.md`, Phase 13.5 plan, and checklist follow-ups. Compatibility target remains same user flow as Magneto for Umbrella/FenLight external scraping. Module-only packaging vs player-selector route remains a tracked gap: prove route works, split companion plugin/service add-ons, or document selector route as unsupported.

### Prevention

Before declaring parity, audit Magneto settings XML, provider attrs/methods, source dict fields, Umbrella scraper code, and FenLight scraper code together. Do not mark selector/player JSON complete until Kodi can execute the route or a non-goal decision is documented.

### References

- `AETHERSCRAPER_MISSING_FEATURES.md` — 2026-05-18 parity audit additions
- `AETHERSCRAPER_FEATURE_PARITY_PLAN.md` Phase 13.5 / Phase 15
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md` Phase 13.5 / Global parity audit follow-ups
- `examples/script.module.magneto/resources/settings.xml`
- `examples/script.module.magneto/lib/magneto/providers/torrents/`
- `examples/plugin.video.umbrella/resources/lib/modules/sources.py`
- `examples/plugin.video.fenlight/resources/lib/scrapers/external.py`

## 2026-05-18 — Local reference add-ons live under ignored examples folder

Status: decision
Area: docs

### Symptom

Root-level third-party/reference add-on folders cluttered repository layout and required per-add-on `.gitignore` entries.

### Cause

Local compatibility examples (`plugin.video.umbrella`, `plugin.video.fenlight`, `script.module.magneto`) are not first-party hosted add-ons.

### Fix / Decision

Move local reference/example add-ons under `examples/` and ignore that folder as one local-only workspace.

### Prevention

Keep first-party hosted add-ons at repository root. Put local compatibility/reference add-ons in `examples/` unless explicitly promoted.

### References

- `.gitignore`
- `README.md`
- `examples/plugin.video.umbrella`
- `examples/plugin.video.fenlight`
- `examples/script.module.magneto`
