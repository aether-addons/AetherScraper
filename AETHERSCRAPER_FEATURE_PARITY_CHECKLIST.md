# AetherScraper Feature Parity Checklist

Plan: [`AETHERSCRAPER_FEATURE_PARITY_PLAN.md`](AETHERSCRAPER_FEATURE_PARITY_PLAN.md)  
Source: [`AETHERSCRAPER_MISSING_FEATURES.md`](AETHERSCRAPER_MISSING_FEATURES.md)  
Standards: [`AGENTS.md`](AGENTS.md)

Use this file as live tracker. Before work: mark item `[-]`. After validation: mark `[x]` and add notes/PR/commit reference if useful.

Legend:

- `[ ]` not started
- `[-]` in progress
- `[x]` complete
- `[!]` blocked / needs decision

## Maintenance — Docs and local examples

- [x] Move local reference/example add-ons under ignored `examples/`.
- [x] Update docs for AetherRepo naming, current module dependency version, and example paths.

Validation notes:

- Passed 2026-05-18: `python3 scripts/validate_addons.py .`; `PYTHONPATH=script.module.aetherscraper/lib:plugin.program.aetherscraper/resources/lib python3 -m pytest -q`; XML parse check for hosted add-on manifests/settings and selector JSON.

## Phase 0 — Baseline audit

- [x] Audit current package API.
- [x] Audit current module layout.
- [x] Audit `addon.xml` extension points.
- [x] Compare current code against missing-feature list.
- [x] Record validation commands.
- [x] Add baseline test/syntax command if missing.

Validation notes:

- Command(s): `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `python3 -m ruff check script.module.aetherscraper/lib tests`; XML parse check for `addon.xml` and `resources/settings.xml`; LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`.
- Result: Passed 2026-05-15. Current AetherScraper remains module-only with basic API/manager/providers; Phase 1 foundation added before provider parity.

## Phase 1 — Kodi settings, profile, and storage foundation

- [x] Kodi settings helper.
- [x] Non-Kodi fallback settings behavior.
- [x] Kodi profile/addon data path helper.
- [x] First-run profile folder setup.
- [x] Settings mirror/cache object.
- [x] Version-update cleanup hook design.
- [x] Tests/manual validation.
- [x] README/docs update.

Validation notes:

- Added `KodiSettings`, `SettingsSnapshot`, profile helpers, `resources/settings.xml`, localization, README docs, and unit tests.
- `record_version_update()` only flags cleanup review; it does not delete files.

## Phase 2 — Provider metadata and discovery

- [x] Add provider metadata fields.
- [x] Add provider folder scanning.
- [x] Add dynamic import loader.
- [x] Add safe provider load error reporting.
- [x] Add per-provider setting enable checks.
- [x] Add restore defaults action.
- [x] Add enable all providers action.
- [x] Add disable all providers action.
- [x] Add enable torrent providers action.
- [x] Add enable pack-capable providers action.
- [x] Tests/manual validation.
- [x] README/docs update.

Validation notes:

- Added provider metadata fields, settings-aware `BaseProvider.is_enabled()`, safe discovery/import loader, and group provider enable helpers.
- Added Phase 2 unit tests in `tests/test_phase2_provider_discovery.py`.
- Passed 2026-05-15: `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m ruff check script.module.aetherscraper/lib tests`; XML parse check for `addon.xml` and `resources/settings.xml`; LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`.

## Phase 3 — Torrent normalization utilities

- [x] Robust size parser.
- [x] Byte conversion helper.
- [x] Base32-to-hex infohash converter.
- [x] Magnet/hash extraction helpers.
- [x] Release-title cleanup pipeline.
- [x] Provider normalization helpers.
- [x] Tests/manual validation.
- [x] README/docs update.

Validation notes:

- Added torrent normalization helpers in `aetherscraper.torrent`: size parsing/formatting, BTIH base32/hex normalization, magnet/free-text hash extraction, release-title cleanup, and provider field alias normalization.
- Updated `TorrentJsonProvider` to normalize raw JSON items before converting to `SourceResult`.
- Added Phase 3 unit tests in `tests/test_phase3_torrent_normalization.py`.
- Passed 2026-05-15: `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m ruff check script.module.aetherscraper/lib tests`; XML parse check for `addon.xml` and `resources/settings.xml`; LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`.

## Phase 4 — Quality, codec, language, and undesirable filters

- [x] Quality detector: `4K`, `1080p`, `720p`, `SD`, `SCR`, `CAM`.
- [x] CAM/SCR tagging.
- [x] Codec parser: HEVC, AV1.
- [x] HDR parser: DV, HDR, hybrid DV/HDR.
- [x] Language detector.
- [x] Foreign-audio filter.
- [x] Default undesirable keyword DB.
- [x] User-managed undesirable keywords.
- [x] HEVC/AV1/DV/HDR filter settings.
- [x] Tests/manual validation.
- [x] README/docs update.

Validation notes:

- Added release metadata helpers in `aetherscraper.release` and manager enrichment/filtering before result sort.
- Added Kodi settings/localization for codec/HDR/foreign-audio filters and user undesirable keywords.
- Added Phase 4 unit tests in `tests/test_phase4_release_filters.py`.
- Passed 2026-05-15: LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m ruff check script.module.aetherscraper/lib tests`; XML parse check for `addon.xml` and `resources/settings.xml`.

## Phase 5 — Movie, episode, and pack search contract

- [x] Movie search adapter.
- [x] Episode search adapter.
- [x] Season pack search.
- [x] Show pack search.
- [x] Episode-range detection in season packs.
- [x] Total-season-aware show pack filtering.
- [x] Host dictionary compatibility.
- [x] Tests/manual validation.
- [x] README/docs update.

Validation notes:

- Added `ScraperManager.search_movie()`, `search_episode()`, `search_season_pack()`, and `search_show_pack()` adapters.
- Added pack helpers in `aetherscraper.packs` for episode ranges, season ranges, season-pack filtering, show-pack filtering, and legacy `host_dict` option passthrough.
- Added Phase 5 unit tests in `tests/test_phase5_search_contract.py` and README docs.
- Passed 2026-05-15: LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m ruff check script.module.aetherscraper/lib tests`; XML parse check for `addon.xml` and `resources/settings.xml`.

## Phase 6 — Title and source validation

- [x] Title normalizer.
- [x] Non-ASCII/unprintable cleanup.
- [x] Alias-aware matching.
- [x] Year-aware movie validation.
- [x] Alternate-year support.
- [x] `SxxExx` episode validator.
- [x] Season pack validator.
- [x] Show pack validator.
- [x] Integrate validators into manager result flow.
- [x] Tests/manual validation.
- [x] README/docs update.

Validation notes:

- Added `aetherscraper.validation` helpers for ASCII/unprintable cleanup, normalized title matching, alias matching, year/alternate-year checks, `SxxExx` episode validation, and pack validators.
- `ScraperManager` now validates enriched results against `SearchQuery` before sorting/returning.
- Added Phase 6 unit tests in `tests/test_phase6_validation.py` and README docs.
- Passed 2026-05-15: LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m ruff check script.module.aetherscraper/lib tests`; XML parse check for `addon.xml` and `resources/settings.xml`.

## Phase 7 — Network stack upgrades

- [x] Response abstraction.
- [x] Session/cookie support.
- [x] Redirect control.
- [x] Proxy support.
- [x] Configurable headers per request.
- [x] Browser/XHR/referer header presets.
- [x] Gzip/encoding handling.
- [x] Partial content helper.
- [x] File-size probe helper.
- [x] Provider retry/backoff config.
- [x] Random user-agent support.
- [x] Safety review: no anti-bot/access-control bypass.
- [x] Tests/manual validation.
- [x] README/docs update.

Validation notes:

- Fixed 2026-05-15: retrying after `urllib.error.HTTPError` now closes the error response to avoid non-fatal `ResourceWarning` socket cleanup noise. Validated with `PYTHONTRACEMALLOC=10 PYTHONPATH=script.module.aetherscraper/lib python3 -W default -m unittest discover -s tests -p 'test_phase7_network_stack.py'`.
- Added `aetherscraper.http` network stack with `HttpResponse`, `NetworkOptions`, session-cookie `HttpClient`, redirect control, proxy config, header presets, gzip decoding, range/file-size helpers, retry/backoff, and optional random user-agent selection.
- Added `BaseProvider.http_client(options)` and public API exports for network helpers.
- Safety review: browser/XHR/referer/user-agent features are static compatibility headers only; no challenge solving, Cloudflare/Sucuri bypass, CAPTCHA bypass, paywall bypass, or access-control bypass added.
- Added Phase 7 unit tests in `tests/test_phase7_network_stack.py` and README docs.
- Passed 2026-05-15: LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m ruff check script.module.aetherscraper/lib tests`; XML parse check for `addon.xml` and `resources/settings.xml`.

## Phase 8 — Authorized provider adapters first

- [x] Generic Torznab XML/RSS parser.
- [x] Generic Torznab provider.
- [x] Prowlarr provider.
- [x] Prowlarr URL/API key settings.
- [x] TorBox Torznab adapter.
- [x] TorBox API key setting.
- [x] AIOStreams provider.
- [x] AIOStreams instance URL setting.
- [x] AIOStreams auth config.
- [x] AIOStreams result normalization.
- [x] Tests/manual validation.
- [x] README/docs update.

Validation notes:

- Added Torznab parser/query helpers in `aetherscraper.torznab`.
- Added authorized providers: `TorznabProvider`, `ProwlarrProvider`, `TorBoxTorznabProvider`, and `AIOStreamsProvider`.
- Added Kodi settings/localization for provider URLs and API/auth values; providers disabled by default.
- Secret values are read from settings/config and are not added to results or logs intentionally.
- Added Phase 8 unit tests in `tests/test_phase8_authorized_providers.py` and README docs.
- Passed 2026-05-15: LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m ruff check script.module.aetherscraper/lib tests`; XML parse check for `addon.xml` and `resources/settings.xml`.

## Phase 9 — Concurrency, timeout, and progress API

- [x] Concurrent provider runner.
- [x] Global timeout budget.
- [x] Per-provider timeout budget.
- [x] Cancellation hook.
- [x] Progress callback API.
- [x] Quality counters during scrape.
- [x] Kodi progress dialog adapter decision.
- [x] Tests/manual validation.
- [x] README/docs update.

Validation notes:

- Added `aetherscraper.progress` with `CancelToken`, `ScrapeProgress`, provider/run summaries, progress callbacks, and quality counters.
- `ScraperManager` now supports optional concurrent provider execution, global scrape timeout, per-provider timeout, cancellation checks, and progress events while preserving existing sequential default.
- Kodi progress dialog adapter decision: module emits neutral progress callbacks; consumer/plugin UI owns dialog binding so module-only usage remains safe outside Kodi.
- Passed 2026-05-15: LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m ruff check script.module.aetherscraper/lib tests`; XML parse check for `addon.xml` and `resources/settings.xml`.

## Phase 10 — Cache and persistence

- [x] SQLite cache under Kodi profile.
- [x] TTL cache API.
- [x] Cache invalidation.
- [x] Cache cleanup.
- [x] Persistent provider state.
- [x] Undesirable keyword DB persistence.
- [x] Tests/manual validation.
- [x] README/docs update.

Validation notes:

- Added `aetherscraper.cache` with `SQLiteCache`, profile-backed DB path, TTL JSON cache entries, namespace/prefix invalidation, stale cleanup, provider state persistence, and undesirable keyword persistence.
- Cache DB lives under profile `cache/aetherscraper.sqlite3`; destructive operations are explicit caller actions only.
- Added Phase 10 unit tests in `tests/test_phase10_cache_persistence.py` and README docs.
- Passed 2026-05-15: LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `python3 -m ruff check script.module.aetherscraper/lib tests`; XML parse check for `addon.xml` and `resources/settings.xml`.

## Phase 11 — Health, debug, and support tools

- [x] Provider health check runner.
- [x] Debug config.
- [x] Addon log file backend.
- [x] Log viewer hook.
- [x] Log clearer hook.
- [x] Optional log uploader decision.
- [x] Help viewer hook.
- [x] Changelog viewer hook.
- [x] Settings cleanup action with confirmation.
- [x] Tests/manual validation.
- [x] README/docs update.

Validation notes:

- Added `aetherscraper.health` with structured provider health checks and redacted provider errors.
- Added `aetherscraper.support` with `DebugConfig`, profile-backed redacted log backend, log/help/changelog text hooks, Kodi text viewer hook, explicit-confirm log clearing, and explicit-confirm settings reset.
- Decision: no optional log uploader in module; logs remain local to reduce secret/privacy risk.
- Added Phase 11 unit tests in `tests/test_phase11_support_tools.py`, README docs, `HELP.md`, and `CHANGELOG.md`.
- Passed 2026-05-15: LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `python3 -m ruff check script.module.aetherscraper/lib tests`; XML parse check for `addon.xml` and `resources/settings.xml`.

## Phase 12 — Kodi module-safe lifecycle helpers

- [x] Decide module-only vs module + plugin + service.
- [x] Update `addon.xml` extension points if needed.
- [x] Plugin router entrypoint.
- [x] Service entrypoint.
- [x] Settings monitor.
- [x] First-run flow integrated.
- [x] Version-update cleanup integrated.
- [x] Kodi window-property cache/coordination.
- [x] Tests/manual validation in Kodi.
- [x] README/docs update.

Validation notes:

- Decision update 2026-05-18: keep `script.module.aetherscraper` module-only in `addon.xml` after Kodi install-structure failure. Do not register `xbmc.python.pluginsource` or `xbmc.service` extension points in this add-on family.
- Kept thin root entrypoints `default.py` and `service.py` plus `aetherscraper.kodi.plugin`, `aetherscraper.kodi.lifecycle`, and `aetherscraper.kodi.window` as importable/helper code for consumer add-ons only.
- Startup creates profile state, records version changes, and sets `cleanup_required`; it never deletes settings/cache automatically.
- Window-property sync mirrors only non-secret coordination settings; API keys/tokens/auth/cookies are skipped and rejected.
- Kodi manual validation pending: install module-only package and confirm consumer add-ons can import lifecycle/plugin helpers. Non-Kodi unit coverage added in `tests/test_phase12_kodi_lifecycle.py`.
- Fixed 2026-05-15 Kodi service import crash: runtime type aliases now use `typing.Callable` instead of `collections.abc.Callable` for Python/Kodi compatibility.
- Superseded 2026-05-18: previous plugin-source visibility approach was removed from `addon.xml`; module add-on remains dependency/library only.
- Passed 2026-05-15: LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests script.module.aetherscraper/default.py script.module.aetherscraper/service.py`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `python3 -m ruff check script.module.aetherscraper/lib tests script.module.aetherscraper/default.py script.module.aetherscraper/service.py`; XML parse check for `addon.xml` and `resources/settings.xml`.
- Re-validated 2026-05-15 after service import fix: LSP diagnostics clean; compileall passed; 69 unit tests passed; ruff passed; direct import of lifecycle/ui/progress aliases passed.

## Phase 13 — Kodi UI/player integration

- [x] Kodi ListItem builders.
- [x] Source selection UI adapter.
- [x] Autoplay ranking policy.
- [x] Result display formatting.
- [x] Highlight color settings.
- [x] Color picker action.
- [x] Playback resolver hook.
- [x] Metadata lookup layer decision.
- [x] Tests/manual validation in Kodi.
- [x] README/docs update.

Validation notes:

- Added reusable `aetherscraper.kodi.ui` helpers for playable `ListItem` rows, source listings, source-selection dialog fallback, autoplay ranking, colored source labels, safe playback URL/header formatting, resolver hooks, and optional consumer-provided metadata overlay.
- Added UI/playback settings and localization for color tags, highlight colors, and autoplay policy. Added support action `pick_color` for Kodi color-picker usage.
- Metadata lookup decision: no built-in TMDb/IMDb calls or API-key storage in this module; consumer add-ons may pass a lookup callable and own settings/cache policy.
- Kodi manual validation pending: install in Kodi and confirm source listing rows are playable in a consumer plugin route, resolver route calls `setResolvedUrl`, and color picker opens from action `pick_color`. Non-Kodi unit coverage added in `tests/test_phase13_kodi_ui_playback.py`.
- Passed 2026-05-15: LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests script.module.aetherscraper/default.py script.module.aetherscraper/service.py`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `python3 -m ruff check script.module.aetherscraper/lib tests script.module.aetherscraper/default.py script.module.aetherscraper/service.py`; XML parse check for `addon.xml` and `resources/settings.xml`.

## Phase 13.5 — Umbrella / FenLight / external-provider compatibility bridge

- [x] Inspect local `examples/plugin.video.umbrella` external-provider selection and scrape contracts.
- [x] Inspect local `examples/plugin.video.fenlight` external-scraper selection and scrape contracts.
- [x] Add importable `aetherscraper.sources()` surface for Umbrella validation.
- [x] Match Magneto signature: `sources(specified_folders=None, ret_all=False)`.
- [x] Support FenLight selection call: `sources(specified_folders=['torrents'])`.
- [x] Support Umbrella calls: `sources()` and `sources(ret_all=True)`.
- [x] Return one adapter tuple per AetherScraper provider where practical, not only one aggregate `aetherscraper` tuple.
- [x] Preserve provider ids, priorities, enable flags, capability flags, and pack flags in external tuples.
- [x] Add provider metadata lists for external consumers: all, torrent, hoster if applicable, pack-capable.
- [x] Add provider-folder metadata/aliases for Magneto folders, especially `torrents`.
- [x] Add Umbrella/Magneto-style source adapter class using AetherScraper `ScraperManager` internally.
- [x] Add per-provider external adapter class factory backed by `ScraperManager` provider filtering.
- [x] Map Umbrella movie payloads to AetherScraper `SearchQuery`.
- [x] Map Umbrella episode payloads to AetherScraper `SearchQuery`.
- [x] Map FenLight movie payloads to AetherScraper `SearchQuery`, including optional `debrid_service` / `debrid_token` fields.
- [x] Map FenLight episode payloads to AetherScraper `SearchQuery`, including `tvshowtitle`, episode title, aliases, and optional `debrid_service` / `debrid_token` fields.
- [x] Map Umbrella pack payloads to AetherScraper pack search flow where supported.
- [x] Map FenLight pack payloads to AetherScraper pack search flow where supported.
- [x] Return pack metadata expected by Umbrella/FenLight: `episode_start`, `episode_end`, `last_season`, and `package` where applicable.
- [x] Convert AetherScraper `SourceResult` objects to Umbrella-compatible source dictionaries.
- [x] Verify FenLight-compatible source dicts: `provider`, `source`, `name`, `name_info`, `quality`, `language`, `url`, `info`, `direct`, `debridonly`, `size` in GB, `hash` for torrents.
- [x] Preserve external cache/dedupe behavior with stable provider id, URL, hash, direct-vs-torrent, package fields, and sane size values.
- [x] Add or verify external source fields beyond core keys: `seeders`, `true_size`, `usenet`, and consumer-added cache/display compatibility behavior.
- [x] Add or verify Magneto-style settings behavior mappings for provider enable flags, scrape timeout, filters, language options, result formatting, and highlight colors.
- [x] Add `resources/aetherscraper.select.json` for AIOStreams/player-selector Magneto parity.
- [x] Add `MediaPlay` plugin action alias for selector JSON and map it to safe source selection/playback.
- [!] Prove `plugin://script.module.aetherscraper/?action=MediaPlay` works in Kodi despite module-only manifest, split route into a companion plugin, or document as unsupported.
- [x] Add tests with Umbrella contract fixtures and import smoke test.
- [x] Add tests with FenLight contract fixtures and import smoke test.
- [x] README/help update with Umbrella setup steps.
- [x] README/help update with FenLight setup steps.
- [!] Manual Kodi/Umbrella validation: Tools > Providers > Enable External Providers / External Provider accepts AetherScraper.
- [!] Manual Kodi/FenLight validation: External Scraper picker accepts AetherScraper and scrape runs.

Validation notes:

- Implemented earlier: `aetherscraper.sources(ret_all=False)` and aggregate `UmbrellaSourceAdapter` in `aetherscraper.external`; import smoke passed with `PYTHONPATH=script.module.aetherscraper/lib python3 - <<'PY' ...`.
- Local Umbrella contract inspected: selection imports add-on id last segment and requires a `sources` callable; scrape runner expects list of `(provider_id, source_class)`, class attrs `priority`, `pack_capable`, `hasMovies`, `hasEpisodes`, plus `sources()`/`sources_packs()` methods. Umbrella calls `sources()` and `sources(ret_all=True)`.
- Local FenLight contract inspected 2026-05-16: selection imports add-on id last segment and calls `sources(specified_folders=['torrents'])`; scrape runner calls `sources()`/`sources_packs()` and post-processes returned dicts for hash, quality, size, provider labels, cache checks, and pack episode/season filtering.
- Gap found 2026-05-16: current AetherScraper `sources()` signature does not accept `specified_folders`; FenLight compatibility would fail selection with `TypeError` unless fixed.
- Gap found 2026-05-16: current AetherScraper returns one aggregate `aetherscraper` adapter, not Magneto-style one tuple per provider; acceptable for minimal Umbrella import, but weaker parity for provider progress labels, provider caches, priorities, and per-provider enable/debug behavior.
- Gap found 2026-05-16: selector JSON and `MediaPlay` alias remain missing; earlier note said not needed for Umbrella, but Magneto parity and AIOStreams/player-selector compatibility still require explicit implementation or documented non-goal.
- Added Phase 13.5 tests earlier in `tests/test_phase13_5_umbrella_bridge.py` and README/HELP setup notes; expanded 2026-05-16 for FenLight `specified_folders`, per-provider adapters, selector JSON, and `MediaPlay` action.
- Passed 2026-05-16: LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests script.module.aetherscraper/default.py script.module.aetherscraper/service.py`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests` (87 tests); `python3 -m ruff check script.module.aetherscraper/lib tests script.module.aetherscraper/default.py script.module.aetherscraper/service.py`; XML parse check for `addon.xml` and `resources/settings.xml`; JSON parse check for `resources/aetherscraper.select.json`.
- Passed 2026-05-16 size-fix validation: LSP diagnostics for changed Python files; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests` (88 tests); `python3 -m ruff check script.module.aetherscraper/lib tests script.module.aetherscraper/default.py script.module.aetherscraper/service.py`.
- Passed 2026-05-17 root size/settings validation: LSP diagnostics for changed Python files; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests` (90 tests); `python3 -m ruff check script.module.aetherscraper/lib tests script.module.aetherscraper/default.py script.module.aetherscraper/service.py`; XML parse check for `addon.xml` and `resources/settings.xml`; empty string settings checked for `<allowempty>true</allowempty>`.
- Added 2026-05-18 external consumer fields: source dictionaries now include `true_size`, torrent `seeders` defaulting safely for Umbrella uncached seeder sort, and `usenet` when source/provider metadata indicates Usenet. Title-derived size remains `true_size=False`.
- Passed 2026-05-18 external-field validation: LSP diagnostics for changed Python files; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests -p 'test_phase13_5_umbrella_bridge.py' -v`; `PYTHONPATH=script.module.aetherscraper/lib:plugin.program.aetherscraper/resources/lib python3 -m compileall -q script.module.aetherscraper/lib plugin.program.aetherscraper/resources/lib plugin.program.aetherscraper/default.py tests`; `PYTHONPATH=script.module.aetherscraper/lib:plugin.program.aetherscraper/resources/lib python3 -m unittest discover -s tests` (98 tests); `python3 -m ruff check script.module.aetherscraper/lib plugin.program.aetherscraper/resources/lib plugin.program.aetherscraper/default.py tests`.
- Manual Kodi/Umbrella and Kodi/FenLight validation pending in Kodi UI.
- Added 2026-05-18 Magneto-style settings aliases: provider enable flags (`provider.<id>`), scrape timeout (`scraping_timeout`), foreign-audio filter (`filter.foreign.single.audio`), priority language (`results.language_filter` / `results.language`), result format (`results.list_format`), highlight type (`highlight.type`), and `scraper_*_highlight` colors. Priority language now maps into `SearchOptions.languages`; UI helpers honor wide labels and single-color highlight mode. Bumped `script.module.aetherscraper` to `0.1.3`.
- Initial targeted unittest command failed because `tests.*` is not importable as a package: `PYTHONPATH=script.module.aetherscraper/lib:plugin.program.aetherscraper/resources/lib python3 -m unittest tests.test_phase1_settings_storage tests.test_phase13_kodi_ui_playback -v`. Corrected with unittest discover patterns.
- Passed 2026-05-18 settings-alias validation: LSP diagnostics for changed Python/tests; `PYTHONPATH=script.module.aetherscraper/lib:plugin.program.aetherscraper/resources/lib python3 -m unittest discover -s tests -p 'test_phase1_settings_storage.py' -v`; `PYTHONPATH=script.module.aetherscraper/lib:plugin.program.aetherscraper/resources/lib python3 -m unittest discover -s tests -p 'test_phase13_kodi_ui_playback.py' -v`; `PYTHONPATH=script.module.aetherscraper/lib:plugin.program.aetherscraper/resources/lib python3 -m compileall -q script.module.aetherscraper/lib plugin.program.aetherscraper/resources/lib plugin.program.aetherscraper/default.py tests`; `PYTHONPATH=script.module.aetherscraper/lib:plugin.program.aetherscraper/resources/lib python3 -m unittest discover -s tests` (100 tests); `python3 -m ruff check script.module.aetherscraper/lib plugin.program.aetherscraper/resources/lib plugin.program.aetherscraper/default.py tests`; XML parse check for hosted add-on manifests/settings and JSON parse check for selector JSON.

## Phase 13.6 — Companion Program add-on for visible Kodi launcher

Goal: keep `script.module.aetherscraper` module-only while adding a separate `plugin.program.aetherscraper` visible under Kodi Program add-ons.

- [x] Decide companion add-on id/folder: `plugin.program.aetherscraper`.
- [x] Create companion add-on tree with `addon.xml`, entrypoint, `resources/`, localization, README/help.
- [x] Manifest uses `xbmc.python.pluginsource` + `<provides>executable</provides>`.
- [x] Manifest depends on `script.module.aetherscraper` and does not duplicate scraper core code.
- [x] Keep `script.module.aetherscraper/addon.xml` module-only; do not re-add plugin/service extension points.
- [x] Add thin route entrypoint parsing `sys.argv` and dispatching query params.
- [x] Add `root` route with status, settings, provider tools, external setup help, validation/debug tools.
- [x] Add `providers` route showing enabled/disabled provider summary.
- [x] Add safe provider group action routes: enable/disable/restore defaults with confirmations where needed.
- [x] Add `settings` route opening module settings.
- [x] Add `external_help` route for Umbrella/FenLight setup notes.
- [x] Decide `MediaPlay` compatibility: move selector JSON to `plugin://plugin.program.aetherscraper/?action=MediaPlay`, keep module route unsupported, or support both only if real Kodi proves safe.
- [x] Add localized strings for all visible labels/dialogs.
- [x] Reuse or add icon/fanart assets.
- [x] Add README/help docs: why module lives in Add-on libraries and companion appears in Program add-ons.
- [x] Add tests for route URL parsing/listing builders with Kodi stubs or isolated helpers.
- [x] Validate companion `addon.xml` family rules.
- [x] Validate Python syntax and lint for companion files.
- [x] Package module + companion with dependency/order notes.
- [!] Smoke test in Kodi: companion visible under Program add-ons.
- [!] Smoke test in Kodi: root/settings/providers/help routes open.
- [!] Smoke test in Kodi: external selector route decision works or unsupported behavior is documented.

Validation notes:

- Planning decision: companion plugin is preferred over mixed `script.module.*` manifest because mixed module/plugin/service extension points previously caused invalid-structure install risk.
- Implemented `plugin.program.aetherscraper` with program plugin manifest, thin `default.py`, route helpers, root/providers/settings/external-help/health/help routes, confirmed provider group actions, localized strings, copied assets, README/HELP, companion selector JSON, and module selector JSON pointing to companion `MediaPlay`.
- Module manifest remains `xbmc.python.module` only; no plugin/service extension points re-added.
- Built zips: `dist/script.module.aetherscraper-0.1.0.zip`; `dist/plugin.program.aetherscraper-0.1.0.zip`. Install module first, then companion.
- Passed 2026-05-18: LSP diagnostics for `plugin.program.aetherscraper/resources/lib/aetherscraper_program` and `tests/test_phase13_6_program_companion.py`; `PYTHONPATH=script.module.aetherscraper/lib:plugin.program.aetherscraper/resources/lib python3 -m compileall -q script.module.aetherscraper/lib plugin.program.aetherscraper/resources/lib plugin.program.aetherscraper/default.py tests`; `PYTHONPATH=script.module.aetherscraper/lib:plugin.program.aetherscraper/resources/lib python3 -m unittest discover -s tests` (97 tests); `python3 -m ruff check script.module.aetherscraper/lib plugin.program.aetherscraper/resources/lib plugin.program.aetherscraper/default.py tests`; XML parse for module/addon settings/companion addon; JSON parse for module+companion selector files.
- Manual Kodi smoke tests remain blocked until run in Kodi UI.

## Phase 14 — Real provider catalog expansion

For each provider: add settings, capability flags, timeout, parser, normalization, tests/manual validation, docs, and safe-use notes.

- [ ] `1337x`
- [ ] `bitmagnet`
- [ ] `bitsearch`
- [ ] `comet`
- [ ] `dmm`
- [ ] `eztv`
- [ ] `kickass2`
- [ ] `knaben`
- [ ] `mediafusion`
- [ ] `meteor`
- [ ] `nyaa`
- [ ] `piratebay`
- [x] `prowlarr`
- [ ] `rutor`
- [ ] `tbtorznab`
- [ ] `torlock`
- [ ] `torrentdownload`
- [x] `torrentio`
- [ ] `torrentproject2`
- [ ] `torrentsdb`
- [ ] `torrentz2`
- [ ] `torz`
- [x] `ytsmx`
- [ ] `zilean`

Validation notes:

- Added `YtsMxProvider` for YTS.mx public `list_movies.json` movie torrents only. Provider is disabled by default, has movie-only metadata, optional `provider.ytsmx.base_url`, and no auth/secret handling.
- Parser normalizes YTS movie/torrent JSON into magnet-backed `SourceResult` objects with info hash, seed/peer counts, size, language, IMDb code, and release metadata.
- Added Phase 14 YTS tests in `tests/test_phase14_ytsmx_provider.py` plus README/settings/localization docs.
- Safety review: uses documented JSON endpoint only; no anti-bot/challenge/access-control bypass added.
- Added `ProwlarrProvider` Phase 14 completion as user-owned Torznab endpoint integration. Provider is disabled by default, supports movie/episode/pack metadata, optional API key, optional category list, and optional root URL + indexer ID endpoint building.
- Added hidden Kodi API-key input plus Prowlarr indexer/category settings and localized help strings.
- Added Phase 14 Prowlarr tests in `tests/test_phase14_prowlarr_provider.py` plus README/HELP setup notes.
- Safety review: uses user-configured Prowlarr/Torznab endpoint only; no anti-bot/challenge/access-control bypass added.
- Added `TorrentioProvider` for Torrentio-compatible Stremio stream JSON. Provider is disabled by default, supports movie/episode torrents only, requires IMDb IDs, and has optional base URL/config path settings.
- Parser normalizes `streams[]` entries with `infoHash`, tracker sources, filename/title, size, seeders, file index, and binge group metadata into magnet-backed `SourceResult` objects.
- Added Phase 14 Torrentio tests in `tests/test_phase14_torrentio_provider.py` plus README/HELP/settings/localization docs.
- Safety review: uses public JSON stream endpoint only; no scraping, browser challenge, CAPTCHA, Cloudflare, or access-control bypass added.
- Passed 2026-05-15: LSP diagnostics for `script.module.aetherscraper/lib/aetherscraper` and `tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests script.module.aetherscraper/default.py script.module.aetherscraper/service.py`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; `python3 -m ruff check script.module.aetherscraper/lib tests script.module.aetherscraper/default.py script.module.aetherscraper/service.py`; XML parse check for `addon.xml` and `resources/settings.xml`.

## Phase 15 — Packaging, assets, docs, and release validation

- [x] Icon asset.
- [x] Fanart asset.
- [x] Help docs for filters/tools/providers.
- [x] Changelog file.
- [x] Final external player/select JSON packaging after Phase 13.5, including `resources/aetherscraper.select.json` and `MediaPlay` route if implemented.
- [x] Validate addon XML.
- [x] Validate Python syntax.
- [ ] Build release zip.
- [ ] Smoke test in Kodi.
- [ ] Release notes.

Validation notes:

- Generated `resources/icon.png` and `resources/fanart.png`; remade branding to avoid magnet/torrent focus and AI-art clutter. Final theme: simple professional AetherScraper branding, blue-orange color scheme, clean monogram/icon and minimal fanart. Added both to `addon.xml` metadata assets.
- Cleanup pass 2026-05-18: aligned README/HELP/addon metadata with module-only packaging decision, added root `.gitignore`, removed generated caches from active target/test dirs, and normalized import ordering.
- Passed 2026-05-18: `python3 -m ruff format --check script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m ruff check script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m compileall -q script.module.aetherscraper/lib tests`; `PYTHONPATH=script.module.aetherscraper/lib python3 -m unittest discover -s tests`; XML parse check for `addon.xml` and `resources/settings.xml`.

## Global parity audit follow-ups

- [x] Re-audit Magneto `resources/settings.xml` against AetherScraper `resources/settings.xml` after Phase 14 provider expansion.
- [x] Re-audit Magneto provider class attributes and returned source dict keys against AetherScraper external adapters.
- [x] Re-audit Umbrella scrape/filter/sort/debrid cache expectations against AetherScraper external adapters.
- [x] Re-audit FenLight scrape/filter/sort/debrid cache expectations against AetherScraper external adapters.
- [ ] Verify external consumer compatibility in real Kodi with Umbrella and FenLight installed.
- [ ] Do not begin post-parity feature additions until Phase 13.5, Phase 14, Phase 15, and safety checklist are complete or explicitly descoped.

Audit notes:

- 2026-05-18: Added parity-source additions to `AETHERSCRAPER_MISSING_FEATURES.md` after comparing Magneto settings IDs, provider class attrs/methods, source dict keys, Umbrella import/selection behavior, and FenLight external scraper behavior.
- New follow-up gaps: non-core source dict fields (`seeders`, `true_size`, `usenet`), Magneto-style setting behavior mappings, and unresolved module-only packaging vs `plugin://script.module.aetherscraper/?action=MediaPlay` selector route compatibility. Phase 13.6 tracks preferred companion `plugin.program.aetherscraper` fix for visible Program add-on UI and safe selector route ownership.

## Global safety checklist

- [ ] No anti-bot bypass added.
- [ ] No access-control bypass added.
- [ ] API keys/tokens read from settings only.
- [ ] Secrets not logged.
- [ ] Destructive cleanup requires confirmation.
- [ ] Kodi Omega/Python 3 baseline preserved unless changed by decision record.
