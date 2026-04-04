# Architecture

**Analysis Date:** 2026-04-03

## Pattern Overview

**Overall:** Zero-backend static site with offline data pipeline

**Key Characteristics:**
- No server, no framework, no build step — pure static HTML/CSS/JS served via GitHub Pages
- Single JSON file (`data/events.json`) as the sole data store
- Python scripts provide offline search automation; results require manual review before merging
- All data fetching and rendering happens client-side via `fetch()` + DOM manipulation
- Git-based workflow: edit data locally, push to main, GitHub Actions deploys to Pages

## Layers

**Presentation Layer (Static HTML):**
- Purpose: User-facing pages for browsing AI talent movement data
- Location: Project root — `index.html`, `detail.html`, `insights.html`
- Contains: Inline CSS, inline JS, no external framework dependencies
- Depends on: `data/events.json` (fetched at runtime)
- Used by: End users via GitHub Pages URL

**Data Layer (JSON Store):**
- Purpose: Single source of truth for all talent movement events
- Location: `data/events.json`
- Contains: Array of event objects with dual schema (old and new field naming)
- Depends on: Nothing at runtime; scripts write to it at edit time
- Used by: All three HTML pages + Python scripts + Node.js add-event script

**Automation Layer (Python Scripts):**
- Purpose: Search for new talent events via Tavily API, deduplicate existing data
- Location: `scripts/` directory
- Contains: `tavily_search.py`, `talent_search.py`, `deduplicate.py`
- Depends on: `tavily-python` package, `TAVILY_API_KEY` env var
- Used by: Operator manually running scripts, GitHub Actions pre-commit hook

**Utility Layer (Node.js Script):**
- Purpose: Manual event entry with validation and duplicate checking
- Location: `add-event.js` (project root)
- Contains: Event template, validation, duplicate detection, JSON append
- Depends on: Node.js runtime, `data/events.json`
- Used by: Operator editing the `newEvent` object and running `node add-event.js`

**CI/CD Layer (GitHub Actions):**
- Purpose: Deploy static files to GitHub Pages on push to main
- Location: `.github/workflows/pages.yml`
- Contains: Single workflow — checkout, copy files to `_site/`, deploy
- Depends on: Push to `main` branch
- Used by: Automatic on git push

**Git Hooks Layer:**
- Purpose: Enforce data quality before commits
- Location: `pre-commit` (project root, must be symlinked or copied to `.git/hooks/`)
- Contains: Deduplication check via `scripts/deduplicate.py`, JSON format validation
- Depends on: Python3, `scripts/deduplicate.py`
- Used by: Git commit process

## Data Flow

**Event Ingestion Flow:**

1. Operator runs `python3 scripts/tavily_search.py --days 1` (or `talent_search.py`)
2. Script queries Tavily API with 4-6 predefined search queries
3. Results saved to `.temp/candidates_*.json` as candidate events needing manual review
4. Operator reviews candidates, fills in `person_name`, `from_company`, `to_company`, etc.
5. Operator either:
   - Edits `add-event.js` `newEvent` object and runs `node add-event.js`, OR
   - Manually appends to `data/events.json`
6. Pre-commit hook runs `scripts/deduplicate.py` if `events.json` is staged
7. Commit and push to `main`
8. GitHub Actions deploys updated `data/events.json` to GitHub Pages

**Display Flow:**

1. Browser loads `index.html` (or `detail.html` / `insights.html`)
2. Inline JS calls `fetch('data/events.json')` to load event data
3. Events are parsed, filtered, sorted client-side based on URL params and UI controls
4. DOM elements are generated via template literals and inserted into the page
5. User interactions (search, filter, sort) re-render the timeline without page reload

**Data Deduplication Flow:**

1. Pre-commit hook detects `data/events.json` in staged files
2. Runs `scripts/deduplicate.py` which:
   - Groups events by composite key: `person_name + from_company + to_company + date_event`
   - For duplicate groups, keeps the most complete record (scored by field presence)
   - Writes deduplicated array back to `data/events.json`
3. If file was modified by dedup, commit is blocked with instructions to re-stage

## State Management

**Application State:** All state is ephemeral, held in JS variables within each HTML page's inline `<script>` block. No shared state between pages — each page fetches `events.json` independently.

**Persistent State:** `data/events.json` is the only persistent store. No database, no localStorage, no cookies.

**Dual Schema Handling:** The first event in `events.json` uses old field names (`person`, `type`, `date`, `from`, `to`, `source`). All subsequent events use new field names (`person_name`, `event_type`, `date_event`, `from_company`, `to_company`, `source_url`). The `add-event.js` duplicate detection and `deduplicate.py` handle both formats via fallback: `event.person_name || event.person`.

## Key Abstractions

**Event Object:**
- Purpose: Represents a single AI talent movement event
- New schema fields: `id`, `person_name`, `event_type` (join/leave/move), `date_event`, `from_company`, `to_company`, `role`, `source_url`, `date_discovered`, `summary`, `tags`
- Old schema fields: `id`, `person`, `type`, `date`, `from`, `to`, `role`, `source`, `date_discovered`, `summary`, `tags`
- Location: `data/events.json` (array of ~150 events)

**Candidate Event:**
- Purpose: Search result pending manual review before being promoted to a real event
- Additional fields: `_candidate`, `_source_title`, `_source_content`, `_source_url`, `_needs_review`
- Location: `.temp/candidates_*.json` (generated, not committed)

## Entry Points

**User Entry Point:**
- Location: `index.html`
- Triggers: Browser navigation to GitHub Pages URL
- Responsibilities: Main timeline view, stats, search, filtering, flow network visualization

**Detail Entry Points:**
- Location: `detail.html?type=person&name=X` or `detail.html?type=company&name=X`
- Triggers: Clicking person/company links from index.html or insights.html
- Responsibilities: Person or company detail view with stats and timeline

**Analysis Entry Point:**
- Location: `insights.html`
- Triggers: Navigation link from index.html
- Responsibilities: Manually curated analysis blog (hardcoded, not data-driven)

**Data Entry Point:**
- Location: `add-event.js`
- Triggers: `node add-event.js` from command line
- Responsibilities: Validate and append a single event to events.json

**Search Entry Point:**
- Location: `scripts/tavily_search.py`
- Triggers: `python3 scripts/tavily_search.py --days 1` from command line
- Responsibilities: Query Tavily API and produce candidate events

## Error Handling

**Strategy:** Fail-fast with user-facing console/alert messages

**Patterns:**
- `fetch()` errors caught with `.catch()`, logged to console
- Missing/invalid `events.json` results in empty page with console error
- `add-event.js` validates required fields before writing, exits with error message on failure
- `deduplicate.py` returns exit code 1 on failure, blocking the commit
- Pre-commit hook uses `set -e` for fail-fast on any command error

## Cross-Cutting Concerns

**Logging:** `console.log` in browser JS, `print()` in Python scripts
**Validation:** `add-event.js` validates required fields and date format; `deduplicate.py` validates JSON structure
**Authentication:** None — public static site, API key only needed for search scripts (env var `TAVILY_API_KEY`)

---

*Architecture analysis: 2026-04-03*
