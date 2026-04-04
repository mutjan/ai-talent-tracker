# Testing Patterns

**Analysis Date:** 2026-04-03

## Test Framework

**Runner:**
- None. No test framework (pytest, jest, vitest, mocha, etc.) is configured in this project.

**Assertion Library:**
- None detected.

**Run Commands:**
```bash
# No test commands exist. The closest equivalent:
python3 scripts/deduplicate.py          # Data quality check (deduplication)
node add-event.js                       # Manual event validation (requires editing file first)
```

## Test File Organization

**Location:**
- No test files exist anywhere in the project. No `*.test.*`, `*.spec.*`, or `tests/` directory found.

**Naming:**
- Not applicable.

**Structure:**
- Not applicable.

## Test Structure

**Suite Organization:**
- No test suites. Quality assurance is done through runtime validation and pre-commit hooks instead.

## Quality Assurance Mechanisms

Since no formal tests exist, the project relies on several informal quality gates:

### 1. Pre-commit Hook

**Location:** `/Users/lzw/Documents/LobsterAI/lzw/ai-talent-tracker/pre-commit`

**What it does:**
- Runs `python3 scripts/deduplicate.py` if `data/events.json` is staged for commit (line 16)
- Validates JSON format for all staged `.json` files using `python3 -c "import json; json.load(...)"` (line 43)
- Blocks commit if dedup modifies the file, requiring user to re-stage (lines 24-29)

**Limitations:**
- Hook must be manually installed (copied to `.git/hooks/pre-commit`)
- Only triggers when `data/events.json` is in the staged changeset

### 2. Manual Validation in `add-event.js`

**Location:** `/Users/lzw/Documents/LobsterAI/lzw/ai-talent-tracker/add-event.js`

**`validateEvent()` function (lines 110-125):**
```javascript
function validateEvent(event) {
  const required = ['person_name', 'event_type', 'date_event', 'source_url', 'summary'];
  const missing = required.filter(field => !event[field] || event[field] === '姓名' || event[field] === '');
  if (missing.length > 0) {
    return { valid: false, error: `缺少必填字段: ${missing.join(', ')}` };
  }
  const datePattern = /^\d{4}-\d{2}-\d{2}$/;
  if (!datePattern.test(event.date_event)) {
    return { valid: false, error: '日期格式错误，应为 YYYY-MM-DD' };
  }
  return { valid: true };
}
```

**Checks:**
- Required fields present and non-empty (person_name, event_type, date_event, source_url, summary)
- Rejects placeholder value `"姓名"` (Chinese for "name")
- Date format must match `YYYY-MM-DD` regex

### 3. Duplicate Detection

**JavaScript:** `isDuplicate()` in `add-event.js` (lines 87-105)
- Composite key: `person_name + from_company + to_company + date_event`
- Handles both old schema (`person`, `from`, `to`, `date`) and new schema field names
- Case-insensitive comparison with `.toLowerCase().trim()`

**Python:** `is_duplicate()` in `scripts/tavily_search.py` (lines 39-53)
- Same composite key logic as JavaScript version
- Used during Tavily search to filter already-known events

**Python:** `find_duplicates()` in `scripts/deduplicate.py`
- Finds all duplicate groups within the full event dataset
- Merges duplicates by keeping the event with the highest "completeness score"
- Run as a pre-commit hook and manually via `python3 scripts/deduplicate.py`

### 4. XSS Prevention

**Location:** `/Users/lzw/Documents/LobsterAI/lzw/ai-talent-tracker/index.html` (lines 995-1000)

```javascript
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
```

Used when rendering user-supplied event data into the DOM.

## Mocking

**Framework:** None.

**Patterns:** Not applicable.

## Fixtures and Factories

**Test Data:**
- No test fixtures. The primary data source is `data/events.json` which contains real production data.

**Location:**
- `data/events.json` — production event data (serves as both data and implicit test fixture)
- `.temp/` — temporary directory for candidate events from search scripts (gitignored)

## Coverage

**Requirements:** None enforced. No coverage tooling configured.

**View Coverage:**
- Not applicable.

## Test Types

**Unit Tests:**
- None.

**Integration Tests:**
- None.

**E2E Tests:**
- None. Frontend is manually tested in browser.

## Common Patterns

**Async Testing:**
- Not applicable. No async test patterns used.

**Error Testing:**
- Not applicable. No error test patterns used.

---

*Testing analysis: 2026-04-03*
