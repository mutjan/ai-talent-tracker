# Technology Stack

**Analysis Date:** 2026-04-03

## Languages

**Primary:**
- JavaScript (Node.js) - CLI tooling (`add-event.js`) and inline frontend scripts in HTML files
- Python 3 - Data processing and search scripts (`scripts/`)
- HTML/CSS - Static frontend pages (all CSS is inline `<style>` blocks)

**Secondary:**
- Shell (Bash) - Git hooks (`pre-commit`)

## Runtime

**Environment:**
- Node.js (runtime for `add-event.js`; version detected from compile cache: v24.11.1-arm64)
- Python 3 (scripts use `#!/usr/bin/env python3`)
- No `package.json`, `requirements.txt`, or `pyproject.toml` present -- dependencies are managed manually

**Package Manager:**
- None configured. No `package.json` or `requirements.txt` exists.
- Python dependencies are installed ad-hoc via `pip install tavily-python`

## Frameworks

**Core:**
- None -- this is a zero-framework project. All HTML is hand-written static files with inline CSS and vanilla JavaScript.
- No React, Vue, Svelte, or any frontend framework.

**Testing:**
- None detected. No test framework, no test files.

**Build/Dev:**
- None -- no build step, no bundler, no transpiler.
- Static files are served directly from the repository root.

## Key Dependencies

**Python (runtime, not pinned):**
- `tavily-python` - Tavily API client for AI news search (`scripts/talent_search.py`, `scripts/tavily_search.py`)
- Standard library only for `deduplicate.py` (`json`, `sys`, `collections`, `pathlib`)

**JavaScript (runtime):**
- Node.js built-in `fs` and `path` modules only (`add-event.js`)

**External CDN (frontend):**
- Google Fonts: `Space Mono` (400, 700) and `DM Sans` (300-700, italic) -- loaded via `<link>` in all three HTML files

## Configuration

**Environment:**
- `TAVILY_API_KEY` -- required env var for search scripts (`scripts/talent_search.py:125`, `scripts/tavily_search.py:209`)
- No `.env` file committed (listed in `.gitignore`)

**Build:**
- No build configuration. No bundler config, no `tsconfig.json`, no linter config.

**Data storage:**
- `data/events.json` -- flat JSON file, 1884 lines, 150 event records
- Two schema versions coexist in the same file:
  - **Old schema** (first entry): `person`, `type`, `date`, `from`, `to`, `source`, `tags`
  - **New schema** (subsequent entries): `person_name`, `event_type`, `date_event`, `from_company`, `to_company`, `source_url`, `date_discovered`
- `add-event.js` handles both schemas in its duplicate check (`lines 94-98`)

## Platform Requirements

**Development:**
- Node.js (for `add-event.js`)
- Python 3 with `tavily-python` pip package (for search scripts)
- Git with hooks support

**Production:**
- GitHub Pages -- static hosting of HTML files and `data/events.json`
- No server-side runtime in production
- Deployed via `.github/workflows/pages.yml` to `https://mutjan.github.io/ai-talent-tracker/`

## CI/CD

**GitHub Actions:**
- Workflow: `.github/workflows/pages.yml`
- Triggers: push to `main` branch, manual dispatch
- Steps: checkout, configure-pages, copy static files to `_site/`, upload artifact, deploy to GitHub Pages
- Uses: `actions/checkout@v4`, `actions/configure-pages@v5`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`

**Git Hooks:**
- `pre-commit` (shell script, must be manually installed to `.git/hooks/`)
- Runs `python3 scripts/deduplicate.py` when `data/events.json` is staged
- Validates JSON format for all staged `.json` files

---

*Stack analysis: 2026-04-03*
