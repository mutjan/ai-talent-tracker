# Codebase Structure

**Analysis Date:** 2026-04-03

## Directory Layout

```
ai-talent-tracker/
├── index.html              # Main timeline page (1047 lines)
├── detail.html             # Person/company detail page (602 lines)
├── insights.html           # Curated analysis blog (1946 lines)
├── add-event.js            # Node.js event entry script (203 lines)
├── pre-commit              # Git pre-commit hook (55 lines)
├── README.md               # Project documentation
├── LICENSE                 # License file
├── .gitignore              # Git ignore rules
├── data/
│   └── events.json         # Central event data store (1884 lines, ~150 events)
├── scripts/
│   ├── deduplicate.py      # Event deduplication script (146 lines)
│   ├── tavily_search.py    # Enhanced Tavily search script (261 lines)
│   └── talent_search.py    # Basic Tavily search script (162 lines)
├── .github/
│   └── workflows/
│       └── pages.yml       # GitHub Pages deployment workflow (44 lines)
├── .planning/
│   └── codebase/           # GSD planning documents (this directory)
└── .temp/                  # Temporary search results (gitignored, generated)
```

## Directory Purposes

**Project Root (`/`):**
- Purpose: Contains all HTML pages and top-level scripts
- Contains: Static HTML files, Node.js utility, git hook
- Key files: `index.html`, `detail.html`, `insights.html`, `add-event.js`, `pre-commit`

**`data/`:**
- Purpose: Central data store for the application
- Contains: `events.json` — the sole persistent data file
- Key files: `data/events.json`

**`scripts/`:**
- Purpose: Python automation scripts for data acquisition and maintenance
- Contains: Search scripts (Tavily API integration), deduplication utility
- Key files: `scripts/tavily_search.py`, `scripts/deduplicate.py`, `scripts/talent_search.py`

**`.github/workflows/`:**
- Purpose: CI/CD pipeline configuration
- Contains: GitHub Actions workflow for Pages deployment
- Key files: `.github/workflows/pages.yml`

**`.temp/`:**
- Purpose: Temporary storage for search candidate results
- Contains: Generated candidate JSON files (not committed)
- Key files: Generated at runtime by search scripts

**`.planning/codebase/`:**
- Purpose: GSD codebase analysis documents
- Contains: Architecture, structure, and convention documentation
- Key files: Documents written by gsd:map-codebase agents

## Key File Locations

**Entry Points:**
- `index.html`: Main page — loads `data/events.json` via fetch, renders timeline, stats, filters, flow network
- `detail.html`: Detail page — driven by URL params `?type=person|company&name=X`, filters events client-side
- `insights.html`: Analysis blog — hardcoded HTML entries, not data-driven, links to detail pages

**Configuration:**
- `.github/workflows/pages.yml`: Deployment config — copies `index.html`, `detail.html`, `insights.html`, `README.md`, `data/events.json` to `_site/`
- `.gitignore`: Ignores `.cowork-temp/`, `.temp/`, `__pycache__/`, `node_modules/`, `.env` files

**Core Logic:**
- `data/events.json`: All event data, dual schema (first event uses old fields, rest use new)
- `scripts/deduplicate.py`: Groups by person+from+to+date, keeps most complete record
- `scripts/tavily_search.py`: CLI tool with `--days`, `--output`, `--auto-merge` flags

**Automation:**
- `pre-commit`: Runs `deduplicate.py` when `events.json` is staged, validates JSON format
- `add-event.js`: Manual event entry with validation and duplicate checking

## Naming Conventions

**Files:**
- HTML pages: lowercase with hyphens (`index.html`, `detail.html`, `insights.html`)
- Python scripts: lowercase with underscores (`deduplicate.py`, `tavily_search.py`)
- Node.js scripts: lowercase with hyphens (`add-event.js`)
- Config files: standard names (`.gitignore`, `pages.yml`)

**Directories:**
- Lowercase with hyphens for project-level (`.planning/codebase/`)
- Lowercase with underscores for scripts (`scripts/`)
- Standard hidden directories (`.github/`, `.temp/`)

## Where to Add New Code

**New HTML Page:**
- Place in project root alongside `index.html`, `detail.html`, `insights.html`
- Add to deployment list in `.github/workflows/pages.yml` under the copy step
- Link from `index.html` navigation

**New Python Script:**
- Place in `scripts/` directory
- Follow naming pattern: lowercase with underscores
- Use `tavily_search.py` as reference for CLI structure and API integration

**New Event Data:**
- Preferred: Edit `add-event.js` `newEvent` object, run `node add-event.js`
- Alternative: Run `python3 scripts/tavily_search.py` for automated search
- Always run `python3 scripts/deduplicate.py` after adding events
- The pre-commit hook will enforce deduplication automatically

**New Analysis/Insight:**
- Manually add HTML block to `insights.html` following existing entry pattern
- Insights are hardcoded, not data-driven

## Special Directories

**`.temp/`:**
- Purpose: Stores candidate events from search scripts before manual review
- Generated: Yes — by `tavily_search.py` and `talent_search.py`
- Committed: No — in `.gitignore`

**`.planning/`:**
- Purpose: GSD planning documents and codebase analysis
- Generated: Yes — by gsd:map-codebase agents
- Committed: Depends on workflow; typically used for planning only

**`data/`:**
- Purpose: Central data store
- Generated: No — manually curated
- Committed: Yes — this is the production data

**`.github/workflows/`:**
- Purpose: GitHub Actions CI/CD
- Generated: No — manually maintained
- Committed: Yes — part of project configuration

---

*Structure analysis: 2026-04-03*
