<!-- GSD:project-start source:PROJECT.md -->
## Project

**AI Talent Tracker — 搜索策略优化**

追踪全球顶级AI公司人才流动的项目，当前已有 150 条事件数据。本次优化聚焦于**扩大搜索覆盖范围**——从固定的 4-6 个英文查询 + 少数科技媒体，扩展到覆盖中英文社交媒体（微博、知乎、脉脉、X/Twitter、LinkedIn、HN 等），确保当天内发现新的人才动态。

**Core Value:** 尽可能全面、及时地发现AI人才流动消息，让用户不漏掉重要的人事变动。

### Constraints

- **API**: 只用 Tavily API，不引入额外搜索服务
- **时效性**: 当天发现即可，不需要实时
- **人工审核**: 搜索结果必须经过人工确认才能入库
- **兼容性**: 新搜索策略必须兼容现有的 events.json 数据结构和去重逻辑
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- JavaScript (Node.js) - CLI tooling (`add-event.js`) and inline frontend scripts in HTML files
- Python 3 - Data processing and search scripts (`scripts/`)
- HTML/CSS - Static frontend pages (all CSS is inline `<style>` blocks)
- Shell (Bash) - Git hooks (`pre-commit`)
## Runtime
- Node.js (runtime for `add-event.js`; version detected from compile cache: v24.11.1-arm64)
- Python 3 (scripts use `#!/usr/bin/env python3`)
- No `package.json`, `requirements.txt`, or `pyproject.toml` present -- dependencies are managed manually
- None configured. No `package.json` or `requirements.txt` exists.
- Python dependencies are installed ad-hoc via `pip install tavily-python`
## Frameworks
- None -- this is a zero-framework project. All HTML is hand-written static files with inline CSS and vanilla JavaScript.
- No React, Vue, Svelte, or any frontend framework.
- None detected. No test framework, no test files.
- None -- no build step, no bundler, no transpiler.
- Static files are served directly from the repository root.
## Key Dependencies
- `tavily-python` - Tavily API client for AI news search (`scripts/talent_search.py`, `scripts/tavily_search.py`)
- Standard library only for `deduplicate.py` (`json`, `sys`, `collections`, `pathlib`)
- Node.js built-in `fs` and `path` modules only (`add-event.js`)
- Google Fonts: `Space Mono` (400, 700) and `DM Sans` (300-700, italic) -- loaded via `<link>` in all three HTML files
## Configuration
- `TAVILY_API_KEY` -- required env var for search scripts (`scripts/talent_search.py:125`, `scripts/tavily_search.py:209`)
- No `.env` file committed (listed in `.gitignore`)
- No build configuration. No bundler config, no `tsconfig.json`, no linter config.
- `data/events.json` -- flat JSON file, 1884 lines, 150 event records
- Two schema versions coexist in the same file:
- `add-event.js` handles both schemas in its duplicate check (`lines 94-98`)
## Platform Requirements
- Node.js (for `add-event.js`)
- Python 3 with `tavily-python` pip package (for search scripts)
- Git with hooks support
- GitHub Pages -- static hosting of HTML files and `data/events.json`
- No server-side runtime in production
- Deployed via `.github/workflows/pages.yml` to `https://mutjan.github.io/ai-talent-tracker/`
## CI/CD
- Workflow: `.github/workflows/pages.yml`
- Triggers: push to `main` branch, manual dispatch
- Steps: checkout, configure-pages, copy static files to `_site/`, upload artifact, deploy to GitHub Pages
- Uses: `actions/checkout@v4`, `actions/configure-pages@v5`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`
- `pre-commit` (shell script, must be manually installed to `.git/hooks/`)
- Runs `python3 scripts/deduplicate.py` when `data/events.json` is staged
- Validates JSON format for all staged `.json` files
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Python scripts: `snake_case.py` (e.g., `deduplicate.py`, `tavily_search.py`, `talent_search.py`)
- JavaScript: `kebab-case.js` (e.g., `add-event.js`)
- HTML: `kebab-case.html` (e.g., `index.html`, `detail.html`, `insights.html`)
- Python: `snake_case` (e.g., `load_events()`, `find_duplicates()`, `parse_date_from_text()`)
- JavaScript: `camelCase` (e.g., `loadEvents()`, `saveEvents()`, `isDuplicate()`, `validateEvent()`, `escapeHtml()`)
- Python: `snake_case` (e.g., `data_path`, `existing_events`, `date_from`, `all_results`)
- JavaScript: `camelCase` (e.g., `newEvent`, `DATA_FILE`, `existingEvents`), with constants in `UPPER_SNAKE_CASE` for `DATA_FILE`
- No formal type definitions or TypeScript used anywhere. All data is plain objects/dicts.
## Code Style
- No formatter or linter configured (no `.eslintrc`, `.prettierrc`, `biome.json`, or `flake8` config)
- Python: 4-space indentation, standard library imports at top
- JavaScript: 2-space indentation (in `add-event.js`), single quotes for strings
- HTML: Inline CSS and JS within the same files, no build tooling
- None. No linting tools detected in the project.
## Import Organization
- CommonJS `require()` / `module.exports` pattern
- Only `fs` and `path` (Node.js built-ins) are imported in `add-event.js`
- Not applicable. No bundler or path aliases used.
## Error Handling
- Bare `except Exception as e` with `print()` and `continue` — see `talent_search.py:71` and `tavily_search.py:143`
- `sys.exit(1)` for fatal errors (missing API key, missing data file) — see `tavily_search.py:213`
- No custom exception classes
- `try/catch` around file I/O with `console.error()` and `process.exit(1)` — see `add-event.js:58-69`
- Validation function returns `{ valid: bool, error: string }` object — see `add-event.js:110-125`
## Logging
- Chinese-language log messages throughout Python scripts (e.g., `print("已加载 {len(existing_events)} 条现有事件")`)
- Chinese-language console output in JavaScript with emoji prefixes (e.g., `console.log('✅ 事件添加成功！')`)
- No structured logging or log levels
## Comments
- Section headers in JavaScript: `// ==================== 配置区域 ====================` style block comments
- Chinese docstrings in Python functions using triple-quoted strings — see `deduplicate.py`, `tavily_search.py`
- JSDoc-style block comment in `add-event.js:1-8` for script usage instructions
- Not used. Python uses plain string docstrings instead.
## Function Design
- Python: return dicts or lists directly; `find_duplicates()` returns `dict` of `{key: [ids]}`
- JavaScript: `validateEvent()` returns `{ valid: bool, error?: string }` result object pattern
## Module Design
- JavaScript: `module.exports = { main, validateEvent, isDuplicate }` in `add-event.js:203`
- Python: No `__init__.py`, no package structure. Scripts are standalone with `if __name__ == "__main__"` guards.
- Not applicable. No module system beyond individual scripts.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- No server, no framework, no build step — pure static HTML/CSS/JS served via GitHub Pages
- Single JSON file (`data/events.json`) as the sole data store
- Python scripts provide offline search automation; results require manual review before merging
- All data fetching and rendering happens client-side via `fetch()` + DOM manipulation
- Git-based workflow: edit data locally, push to main, GitHub Actions deploys to Pages
## Layers
- Purpose: User-facing pages for browsing AI talent movement data
- Location: Project root — `index.html`, `detail.html`, `insights.html`
- Contains: Inline CSS, inline JS, no external framework dependencies
- Depends on: `data/events.json` (fetched at runtime)
- Used by: End users via GitHub Pages URL
- Purpose: Single source of truth for all talent movement events
- Location: `data/events.json`
- Contains: Array of event objects with dual schema (old and new field naming)
- Depends on: Nothing at runtime; scripts write to it at edit time
- Used by: All three HTML pages + Python scripts + Node.js add-event script
- Purpose: Search for new talent events via Tavily API, deduplicate existing data
- Location: `scripts/` directory
- Contains: `tavily_search.py`, `talent_search.py`, `deduplicate.py`
- Depends on: `tavily-python` package, `TAVILY_API_KEY` env var
- Used by: Operator manually running scripts, GitHub Actions pre-commit hook
- Purpose: Manual event entry with validation and duplicate checking
- Location: `add-event.js` (project root)
- Contains: Event template, validation, duplicate detection, JSON append
- Depends on: Node.js runtime, `data/events.json`
- Used by: Operator editing the `newEvent` object and running `node add-event.js`
- Purpose: Deploy static files to GitHub Pages on push to main
- Location: `.github/workflows/pages.yml`
- Contains: Single workflow — checkout, copy files to `_site/`, deploy
- Depends on: Push to `main` branch
- Used by: Automatic on git push
- Purpose: Enforce data quality before commits
- Location: `pre-commit` (project root, must be symlinked or copied to `.git/hooks/`)
- Contains: Deduplication check via `scripts/deduplicate.py`, JSON format validation
- Depends on: Python3, `scripts/deduplicate.py`
- Used by: Git commit process
## Data Flow
## State Management
## Key Abstractions
- Purpose: Represents a single AI talent movement event
- New schema fields: `id`, `person_name`, `event_type` (join/leave/move), `date_event`, `from_company`, `to_company`, `role`, `source_url`, `date_discovered`, `summary`, `tags`
- Old schema fields: `id`, `person`, `type`, `date`, `from`, `to`, `role`, `source`, `date_discovered`, `summary`, `tags`
- Location: `data/events.json` (array of ~150 events)
- Purpose: Search result pending manual review before being promoted to a real event
- Additional fields: `_candidate`, `_source_title`, `_source_content`, `_source_url`, `_needs_review`
- Location: `.temp/candidates_*.json` (generated, not committed)
## Entry Points
- Location: `index.html`
- Triggers: Browser navigation to GitHub Pages URL
- Responsibilities: Main timeline view, stats, search, filtering, flow network visualization
- Location: `detail.html?type=person&name=X` or `detail.html?type=company&name=X`
- Triggers: Clicking person/company links from index.html or insights.html
- Responsibilities: Person or company detail view with stats and timeline
- Location: `insights.html`
- Triggers: Navigation link from index.html
- Responsibilities: Manually curated analysis blog (hardcoded, not data-driven)
- Location: `add-event.js`
- Triggers: `node add-event.js` from command line
- Responsibilities: Validate and append a single event to events.json
- Location: `scripts/tavily_search.py`
- Triggers: `python3 scripts/tavily_search.py --days 1` from command line
- Responsibilities: Query Tavily API and produce candidate events
## Error Handling
- `fetch()` errors caught with `.catch()`, logged to console
- Missing/invalid `events.json` results in empty page with console error
- `add-event.js` validates required fields before writing, exits with error message on failure
- `deduplicate.py` returns exit code 1 on failure, blocking the commit
- Pre-commit hook uses `set -e` for fail-fast on any command error
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
