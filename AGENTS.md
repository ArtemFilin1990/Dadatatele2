# AGENTS.md

## Objective
Maintain a reliable bearing-catalog compiler workflow that produces one validated Excel workbook with sheets:
- `GOST`
- `ISO`
- `SCHEMA`
- `PREFIX_DICT`
- `SUFFIX_DICT`

## Repository map
- Implementation: `compiler.py`
- Domain rules: `codex.md`
- Stage guides: `skills/01_ingest` ... `skills/05_report`
- Primary local inputs: `catalog_full_brands_aprom_enriched.xlsx`, `catalog_full_brands_aprom_patch.xlsx`, `brands.json`, extracted CSV files

## Operating mode (Codex-oriented)
- Default to **implementing**, not only planning.
- Use minimal diffs and keep scope tight to the user request.
- Search using `rg` / `rg --files` first.
- Batch discovery/reads when possible; avoid repetitive one-by-one exploration.
- Prefer deterministic edits and explicit validation steps.

## Technical constraints
- Python 3 stack with `pandas`, `numpy`, `xlsxwriter`.
- Keep output schema and column order unchanged for `GOST`/`ISO`:
  `Бренд | продукция | префикс | номер | суффикс | префикс аналога | номер аналога | суффикс аналога | Аналог | d мм | D мм | B мм | M кг`
- Preserve designation case.
- Do not invent analogs, prefixes, suffixes, dimensions, or mass.
- If direct equivalence is not confirmed, set `Аналог = NO DIRECT EQUIV`.
- Matching only by similar number is not enough; require technical confirmation.

## Source-of-truth priority
1. `REF_GOST_ISO_размеры`
2. `MASTER_PRODUCTS` + brand source sheets
3. `REF_ISO_суффиксы`
4. `DICT_*`, `CROSSREF_*` (auxiliary only)

## Data quality rules
- Split designation into `префикс` / `номер` / `суффикс` only when confirmed.
- Fill size/mass only from confirmed mapping or confirmed source rows.
- Deduplicate GOST/ISO by:
  `Бренд + префикс + номер + суффикс + Аналог`.
- Never delete or rename source data files unless explicitly requested.

## Validation commands
Run relevant checks before finishing:
- `python -m py_compile compiler.py`
- `python compiler.py` (when required inputs/deps are available)

## Pre-finish checklist
- `GOST`/`ISO` contain no empty `номер`.
- Numeric columns are numeric where present (`d мм`, `D мм`, `B мм`, `M кг`).
- `NO DIRECT EQUIV` only where direct analog is not confirmed.
- No duplicates by declared key.
- All five required sheets exist.

## Commit and PR
- Commit message format:
  `type: short description (TASK-id)`
- Include in PR summary: what changed, why, validation done, and known blockers.

## Scope overrides
If nested `AGENTS.md` files appear in subdirectories, they override this file for their subtree.
