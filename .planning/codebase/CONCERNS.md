# Codebase Concerns

**Analysis Date:** 2026-04-03

## Data Schema Inconsistency

**events.json has mixed field schemas across records:**

- 1 event uses old format: `person`, `type`, `from`, `to`, `date`, `source` (event 0, `evt-f8f9a6b9`)
- 136 events use new format without `tags`: `person_name`, `event_type`, `from_company`, `to_company`, `date_event`, `source_url`
- 13 events use new format with `tags`

- Files: `data/events.json`
- Impact: The old-format event (Awni Hannun) is invisible on `detail.html` and `index.html` because they filter on `e.person_name`, `e.from_company`, `e.event_type` etc. The old event uses `person`, `from`, `type` instead. It silently disappears from the UI.
- Fix approach: Migrate event 0 to the new schema, or add backward-compat field reads like `add-event.js` already does at lines 95-98. Better: write a one-time migration script and enforce a JSON schema.

## XSS Risk via innerHTML

**User-controlled data from events.json is injected via innerHTML:**

- `index.html` lines 912, 985, 999: Renders `person_name`, `from_company`, `to_company`, `role` via template literals into `innerHTML`
- `detail.html` lines 478, 486, 524, 581, 593: Same pattern
- An `escapeHtml` helper exists in `index.html` but is not consistently applied to all interpolated values

- Files: `index.html`, `detail.html`
- Risk: If `events.json` is compromised or an attacker modifies event data (e.g., via a PR), arbitrary HTML/JS can execute in visitors' browsers.
- Current mitigation: Data is static JSON served from GitHub Pages; no user-submitted forms.
- Recommendations: Use `textContent` instead of `innerHTML` for all data-derived values, or consistently apply `escapeHtml()` to every interpolated field.

## URL Parameter Injection in detail.html

**detail.html reads URL params without sanitization:**

- `detail.html` lines 460-465: `type` and `name` from `URLSearchParams` are used directly in filter logic and rendered into the DOM via `textContent` (line 493) and template literals.
- Risk: Low (textContent escapes), but the `type` parameter is not validated against allowed values (`person`/`company`).

## Hardcoded Event Data in add-event.js

**add-event.js requires manual code editing for each new event:**

- File: `add-event.js` lines 15-48
- The `newEvent` object is hardcoded in the script. Users must edit the source file, then run it.
- This means every event addition creates a git diff on `add-event.js` itself.
- Risk: Stale event data left in the file from previous additions; easy to accidentally commit wrong data.

## Timestamp-Based ID Generation

**add-event.js uses Date.now() for event IDs:**

- File: `add-event.js` line 17: `id: Date.now().toString()`
- If two events are added within the same millisecond, IDs collide.
- The Python scripts use UUID-based IDs (`evt-{uuid}`), creating inconsistent ID formats across the dataset.
- One existing event has a raw timestamp ID: `1775259648301` (Joel Jang event).

## insights.html is Entirely Static

**The 1945-line insights.html has all data hardcoded in HTML:**

- File: `insights.html`
- Contains zero JavaScript data fetching. All insight entries are static HTML blocks.
- No connection to `events.json`. Insights must be manually maintained separately.
- Risk: Data drift between `events.json` and `insights.html`. High maintenance burden.
- Fix approach: Refactor to load insights from a JSON data file, similar to `index.html`/`detail.html`.

## Monolithic HTML Files

**All three HTML files are single-file monoliths with inline CSS and JS:**

- `insights.html`: 1945 lines
- `index.html`: 1046 lines
- `detail.html`: 601 lines

- No shared CSS/JS modules. CSS variables and styles are duplicated between `index.html` and `insights.html` (identical `:root` definitions, grid background, noise overlay).
- Risk: Style drift between pages. Changes must be replicated in multiple files.

## No Tests

**Zero test files exist in the repository:**

- No test runner configured (no `jest.config`, `vitest.config`, `pytest.ini`, etc.)
- The GitHub Actions workflow (`pages.yml`) deploys without running any tests.
- The `deduplicate.py` script has no unit tests despite performing destructive data operations (deleting records).
- Risk: Data corruption from script bugs goes undetected until manual review.

## Missing Error Handling in Python Scripts

**File operations lack robust error handling:**

- `scripts/talent_search.py` lines 27-28: `save_events()` opens file for writing without try/except. A disk-full or permission error would crash with no recovery.
- `scripts/tavily_search.py` line 219: Calls `load_events()` but the function definition uses a different default path (`"data/events.json"`) than the call site constructs (`data_path`). This works only because `main()` overrides it.
- `scripts/deduplicate.py` line 140: `save_events()` overwrites the original file directly. No backup is created before destructive merge operations.

## Race Conditions in Data Writes

**No file locking on events.json:**

- `add-event.js` reads the file, appends in memory, then writes back (lines 57-76).
- `scripts/deduplicate.py` reads, merges, then overwrites (lines 109, 140).
- If both run concurrently (e.g., two contributors adding events), data loss occurs.
- Risk: Low for single-user workflow, but becomes critical if automated pipelines run alongside manual edits.

## GitHub Actions Deployment Copies All HTML

**pages.yml deploys raw HTML files without build step:**

- File: `.github/workflows/pages.yml` lines 31-35
- Copies `index.html`, `detail.html`, `insights.html`, `README.md`, and `data/events.json` directly.
- No minification, no cache-busting, no integrity checks.
- Risk: Browser caching may serve stale HTML/data after deployments.

## Dependency on External CDN

**Google Fonts loaded from CDN without fallback:**

- All three HTML files load `fonts.googleapis.com` (e.g., `index.html` line 9).
- If Google Fonts is unavailable, text renders with system fallback fonts (visual degradation, no functional breakage).

## .cowork-temp/ Artifacts Present

**Temporary directory with Playwright artifacts exists on disk:**

- Directory: `.cowork-temp/` contains `node-compile-cache` and `playwright-artifacts-*` subdirectories.
- Properly listed in `.gitignore`, so not committed. But indicates leftover tool artifacts from prior sessions.

## Tavily API Key Handling

**Scripts require manual env var setup, no .env file support:**

- `scripts/talent_search.py` line 125: `os.environ.get('TAVILY_API_KEY')`
- `scripts/tavily_search.py` line 209: Same pattern
- No `.env` file loading (no `python-dotenv`). Users must manually export the key.
- Risk: Low security risk (`.env` is gitignored), but poor developer experience.
- Note: `.gitignore` correctly excludes `.env` files.

## Duplicate Script Logic

**talent_search.py and tavily_search.py are near-duplicates:**

- Both scripts implement: `load_events()`, `save_events()`, URL dedup, query construction, Tavily API calls, candidate event generation.
- `talent_search.py` (162 lines) and `tavily_search.py` (261 lines) share ~70% identical logic.
- Risk: Bug fixes must be applied to both files. Already diverged in query construction and output format.
- Fix approach: Extract shared functions to a common module.

## No Input Validation on Event Schema

**add-event.js validates required fields but not values:**

- File: `add-event.js` lines 110-125
- Checks that required fields exist, but does not validate `event_type` against allowed values (`join`/`leave`/`move`).
- `person_name` can be any string, including HTML/script tags.
- No validation that `source_url` is a valid URL.

## Scaling Limit

**Flat JSON file as database:**

- File: `data/events.json` (150 events, 1884 lines)
- The entire file is loaded into memory on every page view (`fetch('data/events.json')`).
- At current size (~150 events), performance is fine. At 1000+ events, page load will degrade.
- No pagination, no indexing, no search capability beyond client-side filtering.

---

*Concerns audit: 2026-04-03*
