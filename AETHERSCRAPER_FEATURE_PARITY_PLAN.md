# AetherScraper Feature Parity Plan

Source: [`AETHERSCRAPER_MISSING_FEATURES.md`](AETHERSCRAPER_MISSING_FEATURES.md)  
Execution tracker: [`AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md`](AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md)  
Agent standards: [`AGENTS.md`](AGENTS.md)

## Goal

Move `script.module.aetherscraper` from clean scraper framework seed toward safe, maintainable Magneto feature parity.

Priority: build reusable module foundations first, then provider adapters, then Kodi UI/service features.

## Ground rules

1. Follow [`AGENTS.md`](AGENTS.md) before code changes.
2. Update [`AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md`](AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md) as work starts/finishes.
3. Keep changes small and validated.
4. Do not implement anti-bot or access-control bypass behavior.
5. Prefer user-authorized/configurable providers before public-site scraping.

## Phase 0 — Baseline audit

1. Audit current package API, module layout, and addon manifest.
2. Compare actual code against missing-feature source list.
3. Record exact scope per phase in checklist.
4. Add minimal tests/validation commands if missing.

Deliverables:

- Confirmed current capability map.
- Validation command list in checklist.

## Phase 1 — Kodi settings, profile, and storage foundation

1. Add Kodi-safe settings helper with fallback behavior outside Kodi.
2. Add profile/addon data path helper using `xbmcvfs` when available.
3. Add first-run profile folder setup.
4. Add settings mirror/cache object.
5. Add version-update cleanup hook design, but keep destructive cleanup explicit.

Covers missing features: lifecycle, cache/persistence, settings surface.

## Phase 2 — Provider metadata and discovery

1. Extend provider contract with:
   - `priority`
   - `pack_capable`
   - `has_movies`
   - `has_episodes`
   - `media_types`
   - `provider_type`
   - `timeout`
2. Add folder scanning for provider modules.
3. Add dynamic import loader with safe error reporting.
4. Add per-provider enable checks from Kodi settings.
5. Add provider group actions:
   - restore defaults
   - enable all
   - disable all
   - enable torrent providers
   - enable pack-capable providers

Covers missing features: provider discovery, dynamic loading, provider capabilities.

## Phase 3 — Torrent normalization utilities

1. Add robust size parser and byte conversion helpers.
2. Add base32-to-hex infohash converter.
3. Add magnet/hash extraction helpers.
4. Add release-title cleanup pipeline.
5. Add provider normalization helpers for inconsistent result fields.

Covers missing features: size/hash utilities, source validation prep.

## Phase 4 — Quality, codec, language, and undesirable filters

1. Add quality detector for `4K`, `1080p`, `720p`, `SD`, `SCR`, `CAM`.
2. Add CAM/SCR tagging.
3. Add codec/HDR parser for HEVC, AV1, Dolby Vision, HDR, hybrid DV/HDR.
4. Add language and foreign-audio detection.
5. Add default undesirable keyword database.
6. Add user-managed undesirable keyword settings.
7. Add filter settings for HEVC/AV1/DV/HDR and foreign audio.

Covers missing features: filters and release metadata.

## Phase 5 — Movie, episode, and pack search contract

1. Add separate movie search adapter.
2. Add separate episode search adapter.
3. Add season pack search.
4. Add show pack search.
5. Add episode-range detection inside season packs.
6. Add total-season-aware show pack filtering.
7. Add host dictionary compatibility where needed.

Covers missing features: search contract and pack logic.

## Phase 6 — Title and source validation

1. Add title normalizer with ASCII/unprintable cleanup.
2. Add alias-aware matching.
3. Add year-aware movie validation and alternate-year support.
4. Add `SxxExx` episode validator.
5. Add season pack validator.
6. Add show pack validator.
7. Integrate validators into manager result flow.

Covers missing features: source validation and title matching.

## Phase 7 — Network stack upgrades

1. Add response abstraction with body, headers, cookies, final URL, status.
2. Add session and cookie support.
3. Add redirect control.
4. Add proxy support.
5. Add request header presets: browser, XHR, referer.
6. Add gzip/encoding handling.
7. Add partial content and file-size probe helpers.
8. Add provider-level retry/backoff config.
9. Add random user-agent support.

Boundary: no anti-bot/access-control bypass implementation without explicit safe/legal review.

Covers missing features: network stack.

## Phase 8 — Authorized provider adapters first

1. Add generic Torznab XML/RSS parser.
2. Add generic Torznab provider.
3. Add Prowlarr provider using configured URL/API key.
4. Add TorBox Torznab adapter using configured API key.
5. Add AIOStreams provider with instance URL and auth config.
6. Normalize all results through shared torrent helpers.

Covers missing features: Torznab/Prowlarr, AIOStreams, safer provider path.

## Phase 9 — Concurrency, timeout, and progress API

1. Add concurrent provider runner.
2. Add global timeout budget.
3. Add per-provider timeout budget.
4. Add cancellation hook.
5. Add progress callback API.
6. Add quality counters during scrape.
7. Add Kodi progress dialog adapter later if UI is in scope.

Covers missing features: concurrency and progress.

## Phase 10 — Cache and persistence

1. Add SQLite cache under Kodi profile path.
2. Add TTL cache API.
3. Add cache invalidation and cleanup.
4. Add persistent provider state.
5. Add undesirable keyword database persistence.

Covers missing features: cache and persistence.

## Phase 11 — Health, debug, and support tools

1. Add provider health check runner.
2. Add debug config.
3. Add addon log file backend.
4. Add log viewer/clearer hooks.
5. Add changelog/help viewer hooks.
6. Add settings cleanup action with confirmation.

Covers missing features: health/debug/support tools.

## Phase 12 — Kodi multi-extension lifecycle

1. Decide if `script.module.aetherscraper` should remain module-only or become module + plugin + service.
2. If yes, update `addon.xml` extension points.
3. Add plugin router entrypoint.
4. Add service entrypoint.
5. Add settings monitor.
6. Add Kodi window-property cache/coordination.

Covers missing features: multi-extension Kodi lifecycle.

## Phase 13 — Kodi UI/player integration

1. Add Kodi ListItem builders.
2. Add source selection UI adapter.
3. Add autoplay ranking policy.
4. Add result display formatting.
5. Add highlight color settings and color picker action.
6. Add playback resolver hook.
7. Add metadata lookup layer if needed.

Covers missing features: player/UI integration.

## Phase 13.5 — Umbrella / FenLight / external-provider compatibility bridge

1. Inspect Umbrella external-provider contract from local `plugin.video.umbrella` reference before implementation.
2. Inspect FenLight external-scraper contract from local `plugin.video.fenlight` reference before implementation.
3. Add compatibility module surface expected by Umbrella and FenLight: importable `aetherscraper.sources()` from `special://home/addons/script.module.aetherscraper/lib`.
4. Match Magneto's `sources(specified_folders=None, ret_all=False)` signature. FenLight calls `sources(specified_folders=['torrents'])`; Umbrella calls `sources()` and `sources(ret_all=True)`.
5. Return Magneto-style provider tuples, preferably one adapter class per enabled AetherScraper provider rather than one aggregate adapter, so provider names, priorities, enable flags, progress labels, and provider caches behave like Magneto in Umbrella/FenLight.
6. Add provider metadata lists needed by external-provider consumers: all providers, torrent providers, hoster/direct providers if applicable, pack-capable providers, and per-folder aliases such as `torrents`.
7. Add adapter class(es) exposing Umbrella/FenLight/Magneto-style methods such as `sources(data, hostDict)` and `sources_packs(data, hostDict, search_series=False, total_seasons=None, bypass_filter=False)` while internally using `ScraperManager`, shared validation, shared filters, and shared network helpers.
8. Normalize Umbrella/FenLight movie payloads (`imdb`, `title`, `aliases`, `year`, optional debrid fields) into AetherScraper `SearchQuery` objects.
9. Normalize Umbrella/FenLight episode payloads (`imdb`, `tvdb`, `tvshowtitle`, `title`, `year`, `season`, `episode`, `premiered`, aliases, optional debrid fields) into AetherScraper `SearchQuery` objects.
10. Normalize pack calls into AetherScraper season/show pack search, including `episode_start`, `episode_end`, `last_season`, `package`, and total-season semantics expected by consuming add-ons.
11. Normalize AetherScraper `SourceResult` objects back into external-compatible source dictionaries without logging secrets or bypassing access controls. Required fields include `provider`, `source`, `name`, `name_info`, `quality`, `language`, `url`, `info`, `direct`, `debridonly`, `size` in GB, and `hash` for torrent results.
12. Preserve debrid/cache handoff fields safely: accept `debrid_service` and `debrid_token` payload keys where providers need authorized APIs, but never log tokens or include them in returned sources.
13. Add duplicate/cache/sort compatibility metadata where consumers depend on it, including stable provider id, stable hash, package type, and direct-vs-torrent flags.
14. Add external selection metadata for AIOStreams/player-selector consumers: `resources/aetherscraper.select.json` equivalent to Magneto's `magneto.select.json` when player-selector flow is in scope.
15. Add plugin action aliases needed by selector JSON, especially `MediaPlay`, and map them to existing safe source-selection/playback flow.
16. Add tests with local Umbrella and FenLight contract fixtures, including import smoke tests for `sources()`, `sources(ret_all=True)`, and `sources(specified_folders=['torrents'])`.
17. Document setup paths: Umbrella Tools > Providers > Enable External Providers / External Provider; FenLight Tools > Accounts/External Scraper > choose AetherScraper.
18. Keep unsupported consumer behavior explicit: no Cloudflare/cfscrape/Sucuri bypass, no access-control bypass, no secret logging.
19. Maintain compatibility mappings for Magneto-style settings semantics where external consumers depend on behavior, especially provider enable flags, scrape timeout, filter toggles, language options, and result display/color options. Exact internal setting IDs may differ if documented.
20. Audit external source dictionaries against Umbrella/FenLight post-processing fields: core torrent keys, pack keys, `seeders`, `true_size`, `usenet`, size-as-GB float, and stable provider/cache/dedupe fields.
21. Validate that selector/player JSON routes are either executable in Kodi or documented as unsupported while module-only packaging remains in force.

Covers missing features: external-provider compatibility and easy configuration from Umbrella/FenLight-like consumers.

## Phase 13.6 — Companion Program add-on for visible Kodi launcher

Keep `script.module.aetherscraper` module-only. Add a separate `plugin.program.aetherscraper` companion if user-visible Programs menu access or `plugin://...` route compatibility is needed.

1. Create companion add-on id/folder `plugin.program.aetherscraper`, name `AetherScraper`, provider `AetherScraper`.
2. Manifest: use `xbmc.python.pluginsource` with `<provides>executable</provides>` and depend on `script.module.aetherscraper`; do not add plugin/service extension points back into the module manifest.
3. Entrypoint: thin `addon.py` or `default.py` that parses `sys.argv`, dispatches short routes, and always calls `xbmcplugin.endOfDirectory(handle)` for listings.
4. Routes:
   - `root`: status, settings, provider tools, external setup help, validation/debug tools.
   - `providers`: enabled/disabled provider summary and group actions.
   - `settings`: open module settings.
   - `external_help`: show Umbrella/FenLight setup notes.
   - `MediaPlay`: optional compatibility alias for selector JSON; route to safe source selection only if Kodi can execute it from companion plugin path.
5. Reuse `script.module.aetherscraper` APIs only; keep UI/routing code in companion add-on.
6. Add localization strings, README/help notes, icon/fanart reuse or companion assets.
7. Package as separate zip or repository sibling with module dependency ordering documented.
8. Validate manifest family rules, Python syntax, route smoke tests, and real Kodi visibility under Program add-ons.

Covers missing features: visible Program add-on launcher and safe replacement for Magneto's mixed module/plugin manifest behavior.

## Phase 14 — Real provider catalog expansion

1. Add provider interface tests before each provider.
2. Add providers one at a time.
3. Prefer API/config-backed providers.
4. For each provider, document settings, capability flags, timeout, parser assumptions, and legal/safe-use notes.
5. Target catalog from source list only after foundations are stable.

Target providers from [`AETHERSCRAPER_MISSING_FEATURES.md`](AETHERSCRAPER_MISSING_FEATURES.md): `1337x`, `bitmagnet`, `bitsearch`, `comet`, `dmm`, `eztv`, `kickass2`, `knaben`, `mediafusion`, `meteor`, `nyaa`, `piratebay`, `prowlarr`, `rutor`, `tbtorznab`, `torlock`, `torrentdownload`, `torrentio`, `torrentproject2`, `torrentsdb`, `torrentz2`, `torz`, `ytsmx`, `zilean`.

## Phase 15 — Packaging, assets, docs, and release validation

1. Add icon/fanart assets.
2. Add help docs for filters/tools/providers.
3. Add changelog file.
4. Finalize external player/select JSON packaging after Phase 13.5 compatibility is validated, including `resources/aetherscraper.select.json` and `MediaPlay` route if AIOStreams/player-selector consumers require Magneto-equivalent behavior.
5. Resolve module-only packaging compatibility gap for `plugin://script.module.aetherscraper/?action=MediaPlay`: split companion plugin/service add-ons, prove safe manifest structure, or document as unsupported non-goal.
6. Validate addon XML.
7. Validate Python syntax.
8. Build zip package.
9. Smoke test in Kodi.

Covers missing features: packaging/assets/help.

## Done definition

A phase is done only when:

- Checklist items are checked.
- Code paths have tests or manual validation notes.
- README or docs mention new public behavior.
- Kodi compatibility remains Omega/Python 3 baseline unless explicitly changed.
- No unsafe anti-bot/access-control bypass behavior added.
