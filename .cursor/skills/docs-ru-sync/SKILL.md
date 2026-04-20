---
name: docs-ru-sync
description: Sync README.ru.md with README.md using scripts/sync_readme_ru.py and the SYNC_EN_SHA256 marker. Use when editing README.md, README.ru.md, or running Russian doc parity checks.
---

# Docs RU sync (email2telegram)

## When to use

- User or task changes `README.md` and Russian mirror should stay aligned.
- Auditing whether `README.ru.md` is stale relative to English README.

## How sync works

- `README.ru.md` contains an HTML comment marker `<!-- SYNC_EN_SHA256: <64-hex> -->` (see `MARKER_RE` in `scripts/sync_readme_ru.py`).
- The script hashes `README.md` and compares to the marker to detect drift.

## Commands (from repo root)

- Check status / update marker and body: `python3 scripts/sync_readme_ru.py`
- Dry run: `python3 scripts/sync_readme_ru.py --dry-run`
- Fetch latest EN README from GitHub (optional workflow in script): see `python3 scripts/sync_readme_ru.py --help`

## After automation

- Reread `README.ru.md`: headings and links should still read naturally in Russian; adjust phrasing manually if the English structure changed heavily.

## Related material

- Plan with doc restructure notes: `.cursor/plans/docs_restructure_and_ru_sync_8be09007.plan.md`
- Dev index: `docs/dev/README.md`
