# AGENTS.md — AetherScraper Working Standards

Primary plan: [`AETHERSCRAPER_FEATURE_PARITY_PLAN.md`](AETHERSCRAPER_FEATURE_PARITY_PLAN.md)  
Live checklist: [`AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md`](AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md)  
Recurring issues log: [`AETHERSCRAPER_RECURRING_ISSUES.md`](AETHERSCRAPER_RECURRING_ISSUES.md)  
Feature source: [`AETHERSCRAPER_MISSING_FEATURES.md`](AETHERSCRAPER_MISSING_FEATURES.md)

## Repository / install feed

Development stays in this source repo (`AetherScraper`): https://github.com/aether-addons/AetherScraper.
Kodi-installable repo feed is generated in `AetherRepo`: https://github.com/aether-addons/AetherRepo.

Automatic release flow:

1. Change hosted add-on code here.
2. Bump changed add-on `addon.xml` version.
3. Push `AetherScraper`.
4. `.github/workflows/publish-repo.yml` dispatches `AetherRepo` event `source-updated`.
5. `AetherRepo` clones all repos in its `repo-sources.json`, rebuilds/validates feed, commits zips/checksums.

Do **not** commit generated Kodi repo zips here. Do **not** manually rebuild `../AetherRepo` unless user asks for local release/testing.

If adding/removing hosted add-ons or moving add-ons between repos, update `AetherRepo/repo-sources.json`.

`AetherRepo` default feed must stay: `https://raw.githubusercontent.com/aether-addons/AetherRepo/main/`.

## Required AI workflow

1. Read this file before working in this repository.
2. Read the feature parity plan before implementing missing features.
3. Read the recurring issues log before debugging or touching known-problem areas.
4. Use the checklist as the task tracker.
5. Before coding, mark relevant checklist item `[-]`.
6. After coding and validation, mark item `[x]` and add validation notes when useful.
7. Add recurring bugs, gotchas, decisions, and non-obvious fixes to the recurring issues log.
8. Keep implementation aligned with phase order unless there is a clear reason to skip ahead.
9. If scope changes, update plan and checklist in the same change.
10. Keep source-only changes in `AetherScraper`; never commit generated Kodi repo zips here.
11. After hosted add-on changes, rely on auto-publish workflow after push; manually rebuild `../AetherRepo` only when user asks or debugging release tooling.
12. For new hosted repos/add-ons, update `AetherRepo/repo-sources.json` and ensure source repo has notify workflow.

## Project goal

Build `script.module.aetherscraper` into a safe, maintainable Kodi scraper module with selected Magneto feature parity. Foundations first: settings, provider metadata, normalization, validation, network, cache, then providers and UI.

## Safety boundaries

- Do not implement anti-bot bypass or access-control bypass behavior.
- Do not add Cloudflare/Sucuri bypass code without explicit legal/safe-use review.
- Do not log API keys, tokens, usernames, passwords, cookies, or full auth headers.
- Store secrets only through Kodi settings or documented user config paths.
- Destructive actions, including settings cleanup/cache deletion, must require explicit confirmation.

## Kodi standards

- Target Kodi Omega baseline unless a decision record changes it.
- Keep `xbmc.python` compatibility in sync with `addon.xml`.
- Kodi imports must have safe fallbacks or be isolated so tests can run outside Kodi.
- Use `xbmcvfs` for Kodi profile paths when available.
- Keep plugin/service/UI code separate from reusable module logic.
- Do not break module-only usage while adding plugin/service features.

## Python standards

- Prefer small modules with clear responsibilities.
- Keep public API backward-compatible where practical.
- Use type hints for new public functions/classes.
- Avoid broad `except Exception` unless logging context and continuing safely.
- Normalize provider output into shared models before filtering/sorting.
- Keep provider-specific parsing inside provider modules or provider helpers.

## Provider standards

Each provider must document:

- provider name and type
- required settings
- capability flags: movie, episode, pack
- timeout behavior
- auth/API key requirements
- parser assumptions
- safe-use notes

Provider implementation must:

- use shared network helpers
- use shared torrent normalization helpers
- honor enabled/disabled settings
- honor global and per-provider timeout
- never log secrets
- fail gracefully and report useful provider errors

## Testing and validation standards

Before marking checklist items complete:

- Run Python syntax validation for changed Python files.
- Run available tests if present.
- For Kodi-specific behavior, add manual Kodi validation notes.
- Validate `addon.xml` after manifest changes.
- Update README/docs for new public behavior or settings.

Suggested baseline commands may be recorded in checklist Phase 0 after audit.

## Documentation standards

- New features need README or help text when user-visible.
- New settings need purpose, default, and safety notes.
- Plan/checklist must stay current when phases change.
- Recurring issues log must capture non-obvious fixes, repeated bugs, compatibility decisions, and safety decisions.
- Cross-link docs instead of duplicating large sections.

## File ownership map

- `AETHERSCRAPER_MISSING_FEATURES.md`: source gap list. Do not casually rewrite.
- `AETHERSCRAPER_FEATURE_PARITY_PLAN.md`: step-by-step implementation plan.
- `AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md`: live work tracker.
- `AETHERSCRAPER_RECURRING_ISSUES.md`: cross-session memory for recurring bugs, gotchas, and decisions.
- `script.module.aetherscraper/`: active implementation target.
- `examples/script.module.magneto/`: reference only. Do not copy unsafe behavior blindly.

## Done definition

Work is done when:

- checklist item is `[x]`
- validation completed or manual validation noted
- docs updated if user-visible
- recurring issue logged when fix/decision may matter in future sessions
- no safety boundary violated
- plan still matches implementation direction
