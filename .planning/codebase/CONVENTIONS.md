# Coding Conventions

**Analysis Date:** 2026-04-03

## Naming Patterns

**Files:**
- Python scripts: `snake_case.py` (e.g., `deduplicate.py`, `tavily_search.py`, `talent_search.py`)
- JavaScript: `kebab-case.js` (e.g., `add-event.js`)
- HTML: `kebab-case.html` (e.g., `index.html`, `detail.html`, `insights.html`)

**Functions:**
- Python: `snake_case` (e.g., `load_events()`, `find_duplicates()`, `parse_date_from_text()`)
- JavaScript: `camelCase` (e.g., `loadEvents()`, `saveEvents()`, `isDuplicate()`, `validateEvent()`, `escapeHtml()`)

**Variables:**
- Python: `snake_case` (e.g., `data_path`, `existing_events`, `date_from`, `all_results`)
- JavaScript: `camelCase` (e.g., `newEvent`, `DATA_FILE`, `existingEvents`), with constants in `UPPER_SNAKE_CASE` for `DATA_FILE`

**Types:**
- No formal type definitions or TypeScript used anywhere. All data is plain objects/dicts.

## Code Style

**Formatting:**
- No formatter or linter configured (no `.eslintrc`, `.prettierrc`, `biome.json`, or `flake8` config)
- Python: 4-space indentation, standard library imports at top
- JavaScript: 2-space indentation (in `add-event.js`), single quotes for strings
- HTML: Inline CSS and JS within the same files, no build tooling

**Linting:**
- None. No linting tools detected in the project.

## Import Organization

**Python:**
1. Standard library imports (`os`, `json`, `sys`, `re`, `datetime`, `pathlib`)
2. Third-party imports (`tavily`)
3. No local imports (no package structure)

**JavaScript:**
- CommonJS `require()` / `module.exports` pattern
- Only `fs` and `path` (Node.js built-ins) are imported in `add-event.js`

**Path Aliases:**
- Not applicable. No bundler or path aliases used.

## Error Handling

**Python patterns:**
- Bare `except Exception as e` with `print()` and `continue` — see `talent_search.py:71` and `tavily_search.py:143`
- `sys.exit(1)` for fatal errors (missing API key, missing data file) — see `tavily_search.py:213`
- No custom exception classes

**JavaScript patterns:**
- `try/catch` around file I/O with `console.error()` and `process.exit(1)` — see `add-event.js:58-69`
- Validation function returns `{ valid: bool, error: string }` object — see `add-event.js:110-125`

## Logging

**Framework:** Plain `print()` (Python) and `console.log()` / `console.error()` (JavaScript)

**Patterns:**
- Chinese-language log messages throughout Python scripts (e.g., `print("已加载 {len(existing_events)} 条现有事件")`)
- Chinese-language console output in JavaScript with emoji prefixes (e.g., `console.log('✅ 事件添加成功！')`)
- No structured logging or log levels

## Comments

**When to Comment:**
- Section headers in JavaScript: `// ==================== 配置区域 ====================` style block comments
- Chinese docstrings in Python functions using triple-quoted strings — see `deduplicate.py`, `tavily_search.py`
- JSDoc-style block comment in `add-event.js:1-8` for script usage instructions

**JSDoc/TSDoc:**
- Not used. Python uses plain string docstrings instead.

## Function Design

**Size:** Functions are typically short (10-30 lines), single-purpose.

**Parameters:** Default parameter values used in Python (e.g., `data_path: str = "data/events.json"` in `tavily_search.py:18`).

**Return Values:**
- Python: return dicts or lists directly; `find_duplicates()` returns `dict` of `{key: [ids]}`
- JavaScript: `validateEvent()` returns `{ valid: bool, error?: string }` result object pattern

## Module Design

**Exports:**
- JavaScript: `module.exports = { main, validateEvent, isDuplicate }` in `add-event.js:203`
- Python: No `__init__.py`, no package structure. Scripts are standalone with `if __name__ == "__main__"` guards.

**Barrel Files:**
- Not applicable. No module system beyond individual scripts.

---

*Convention analysis: 2026-04-03*
