# AGENTS.md — AetherScraper Working Standards

Primary plan: [`AETHERSCRAPER_FEATURE_PARITY_PLAN.md`](AETHERSCRAPER_FEATURE_PARITY_PLAN.md)  
Live checklist: [`AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md`](AETHERSCRAPER_FEATURE_PARITY_CHECKLIST.md)  
Recurring issues log: [`AETHERSCRAPER_RECURRING_ISSUES.md`](AETHERSCRAPER_RECURRING_ISSUES.md)  
Feature source: [`AETHERSCRAPER_MISSING_FEATURES.md`](AETHERSCRAPER_MISSING_FEATURES.md)

## Repository / install feed

Development stays in this source tree (`AetherScraper`): https://github.com/aether-addons/AetherScraper.
Kodi-installable repository output lives next to it in `../AetherRepo/`: https://github.com/aether-addons/AetherRepo.

After changing any hosted add-on, bump the changed add-on version in `addon.xml`, then rebuild the install repo:

```bash
cd ../AetherRepo
python3 build_repo.py
python3 scripts/validate_repo.py .
```

`AetherRepo` defaults to the GitHub raw feed: `https://raw.githubusercontent.com/aether-addons/AetherRepo/main/`.
Use `python3 build_repo.py --local-file-url` only for local Kodi testing.

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
10. Keep source-only changes in `AetherScraper`; do not commit generated Kodi repo zips here.
11. After any hosted add-on change, rebuild and validate sibling `../AetherRepo` before release.
12. Commit/push `AetherScraper` first, then commit/push regenerated `AetherRepo` output.

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
- `script.module.magneto/`: reference only. Do not copy unsafe behavior blindly.

## Done definition

Work is done when:

- checklist item is `[x]`
- validation completed or manual validation noted
- docs updated if user-visible
- recurring issue logged when fix/decision may matter in future sessions
- no safety boundary violated
- plan still matches implementation direction
