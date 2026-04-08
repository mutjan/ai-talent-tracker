# Phase 1: 脚本整合 - Research

**Researched:** 2026-04-08
**Domain:** Python script consolidation, Tavily API integration, configuration-driven search pipeline
**Confidence:** HIGH

## Summary

This phase merges two Python search scripts (`talent_search.py` at 162 lines and `tavily_search.py` at 261 lines) into a single `scripts/search.py`. The two scripts share ~70% identical code: both import `TavilyClient`, both have `load_events()`/`save_events()` functions, both iterate over hardcoded query lists calling `client.search()`, both deduplicate by URL within-session, and both output candidate events to `.temp/`. The key differences are: (1) `talent_search.py` uses `include_domains` with 9 English tech media sites while `tavily_search.py` uses `time_range="day"` and no domain restriction; (2) candidate output fields differ (`_candidate`/`_source_content` in talent_search vs `_needs_review`/`_mentioned_companies` in tavily_search); (3) `tavily_search.py` has richer helper functions (`parse_date_from_text`, `extract_person_and_companies`, `is_duplicate`) that `talent_search.py` lacks.

The consolidation is straightforward because it's a pure refactor -- no new features, no schema changes to `events.json`, and no changes to `deduplicate.py` or `add-event.js`. The main design work is creating the configuration structure (queries dict + domain groups dict) and deciding the internal function organization.

**Primary recommendation:** Create `scripts/search.py` with a top-level `SEARCH_CONFIG` dict containing queries and domain groups, reuse all helper functions from `tavily_search.py`, and adopt tavily_search.py's candidate output format as the canonical one (augmented with `_source_content` from talent_search).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** 合并后的脚本命名为 `scripts/search.py`，放在现有 `scripts/` 目录下
- **D-02:** 合并完成后删除 `scripts/talent_search.py` 和旧的 `scripts/tavily_search.py`
- **D-03:** 搜索查询定义为顶层 Python dict，按查询类别分组（如 `english_broad`、`english_specific`），每个 key 的值是查询字符串列表
- **D-04:** 查询定义与搜索逻辑解耦 -- 修改查询只需改配置 dict，不碰函数体
- **D-05:** 域名按类型分组成命名 dict（`english_tech` / `chinese_tech` / `social`），支持按组启用/停用
- **D-06:** Phase 1 只启用 `english_tech` 组（9 个现有英文科技媒体域名），中文组和社交组预留但不激活
- **D-07:** 候选事件格式以 tavily_search.py 的字段为基础：包含 `id`、`person_name`、`event_type`、`date_event`（自动解析）、`from_company`、`to_company`、`role`、`source_url`、`date_discovered`、`summary`、`tags`、`_needs_review`、`_source_title`、`_mentioned_companies`、`_source_content`（500 字符预览，从 talent_search 补充）
- **D-08:** 去重逻辑复用 tavily_search.py 的 URL 去重方式（within-session），跨批次 URL 去重留给 Phase 2

### Claude's Discretion
- 具体函数划分和内部模块组织
- 日志消息的中英文措辞
- 错误重试的具体实现细节

### Deferred Ideas (OUT OF SCOPE)
- 中文搜索查询（COVR-01） -- Phase 3
- Tavily topic="news"、country="cn"、exact_match 参数优化 -- Phase 3
- 跨批次 URL 去重（seen_urls.json） -- Phase 2
- 动态查询生成（从 events.json 自动提取） -- Phase 4
- GitHub Actions 每日执行 -- Phase 5
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CONS-01 | 合并 talent_search.py 和 tavily_search.py 为单一搜索脚本，消除 70% 重复代码 | Detailed diff analysis below -- shared functions identified, merge strategy defined |
| CONS-02 | 搜索查询定义外部化为配置（Python dict），不再硬编码在函数体中 | Config structure designed, queries from both scripts cataloged |
| CONS-03 | 域名集合抽象为命名组（english_tech / chinese_tech / social），支持按组启用 | 9 existing domains from talent_search.py mapped to `english_tech` group |
| CONS-04 | 统一候选事件输出格式，消除两个脚本间的字段命名差异 | Field-level diff below, unified format based on D-07 decision |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tavily-python | latest (0.5.x+) | Tavily API client | Only allowed search API per project constraints |
| Python 3 stdlib | system | json, sys, re, datetime, pathlib, argparse, uuid | Already used by both scripts |

### Supporting
None -- this phase uses no additional dependencies beyond what the scripts already import.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Single `SEARCH_CONFIG` dict in search.py | Separate `config.py` file | Not needed for ~20 lines of config; single file keeps it simple per project's zero-framework philosophy |
| Python dict for config | YAML/TOML config file | Adds a dependency (PyYAML/tomllib); overkill for this scale |

**Installation:**
```bash
pip install tavily-python
```

**Version verification:** The project already has `tavily-python` as its sole Python dependency. No new packages needed.

## Architecture Patterns

### Recommended Project Structure (post-consolidation)
```
scripts/
├── search.py           # NEW: unified search script (replaces both)
├── deduplicate.py      # UNCHANGED: pre-commit deduplication
├── talent_search.py    # DELETED
└── tavily_search.py    # DELETED
```

### Pattern 1: Configuration Dict at Module Level
**What:** Define `SEARCH_CONFIG` as a module-level dict containing all queries and domain groups. Search logic iterates over this dict, never over hardcoded lists.
**When to use:** Whenever the script needs to know "what to search" -- this is the single source of truth.
**Example:**
```python
# Source: designed from CONTEXT.md decisions D-03, D-04, D-05, D-06
SEARCH_CONFIG = {
    "queries": {
        "english_broad": [
            "AI researcher joins leaves OpenAI Google DeepMind Anthropic",
            "AI talent move chief scientist leaves joins startup",
            "top AI engineer researcher joins new company",
            "AI lab researcher departure hiring",
        ],
        "english_specific": [
            "vice president AI leaves joins",
            "co-founder AI startup leaves",
            "AI researcher joins leaves OpenAI Google DeepMind Anthropic Meta",
        ],
        "chinese_broad": [],        # Phase 3 -- 预留
        "chinese_specific": [],     # Phase 3 -- 预留
    },
    "domain_groups": {
        "english_tech": {
            "enabled": True,
            "domains": [
                "techcrunch.com",
                "theinformation.com",
                "bloomberg.com",
                "reuters.com",
                "businessinsider.com",
                "venturebeat.com",
                "x.com",
                "linkedin.com",
                "subsight.com",
            ],
        },
        "chinese_tech": {
            "enabled": False,  # Phase 3 -- 预留
            "domains": [],
        },
        "social": {
            "enabled": False,  # Phase 3 -- 预留
            "domains": [],
        },
    },
}
```

### Pattern 2: Unified Search Pipeline
**What:** A single `run_search()` function that iterates over enabled query groups, collects all Tavily results, deduplicates by URL, and converts to the unified candidate format.
**When to use:** This is the main entry point called by `main()`.
**Example:**
```python
def run_search(client: TavilyClient, days_back: int = 1) -> list[dict]:
    """Execute all enabled search queries and return deduplicated raw results."""
    all_results = []
    enabled_domains = _get_enabled_domains()

    for group_name, queries in SEARCH_CONFIG["queries"].items():
        if not queries:  # Skip empty groups (e.g., chinese_* reserved for Phase 3)
            continue
        for query in queries:
            try:
                print(f"搜索 [{group_name}]: {query}")
                kwargs = {
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": 10,
                }
                if enabled_domains:
                    kwargs["include_domains"] = enabled_domains
                if days_back <= 1:
                    kwargs["time_range"] = "day"
                response = client.search(**kwargs)
                all_results.extend(response.get("results", []))
            except Exception as e:
                print(f"搜索失败 '{query}': {e}")
                continue

    # Within-session URL dedup
    return _dedup_by_url(all_results)
```

### Pattern 3: Unified Candidate Event Output
**What:** `convert_to_event()` produces a single canonical format based on D-07.
**When to use:** For every raw search result converted to a candidate event.
**Example:**
```python
def convert_to_event(search_result: dict, existing_events: list) -> dict:
    """Convert a raw Tavily search result to a unified candidate event."""
    title = search_result.get("title", "")
    content = search_result.get("content", "")
    url = search_result.get("url", "")

    date = parse_date_from_text(f"{title} {content}")
    extracted = extract_person_and_companies(content, title)

    event = {
        "id": generate_event_id(),
        "person_name": "",
        "event_type": "move",
        "date_event": date,
        "from_company": "",
        "to_company": "",
        "role": "",
        "source_url": url,
        "date_discovered": datetime.now().strftime("%Y-%m-%d"),
        "summary": content[:300] + "..." if len(content) > 300 else content,
        "tags": [],
        # Review metadata
        "_needs_review": True,
        "_source_title": title,
        "_mentioned_companies": extracted.get("mentioned_companies", []),
        "_source_content": content[:500],  # From talent_search -- 500 char preview
    }

    if is_duplicate(event, existing_events):
        event["_is_duplicate"] = True

    return event
```

### Anti-Patterns to Avoid
- **Hardcoding queries in function bodies:** The whole point of CONS-02 is to externalize queries. Even a single hardcoded query string inside a function violates the decision.
- **Creating domain group logic that is "clever":** Simple dict with `enabled` boolean is enough. No need for regex patterns, wildcard matching, or complex enable/disable rules.
- **Merging `deduplicate.py` into `search.py`:** These serve different purposes (dedup is a git hook for committed data, search dedup is for candidate filtering). Keep them separate.
- **Adding `time_range` parameter when `days_back > 1`:** Tavily's `time_range` only supports `"day"`, `"week"`, `"month"`, `"year"`. For `days_back > 1`, the script should not set `time_range` at all and let Tavily's relevance ranking handle recency. Or use `"week"` when `days_back <= 7`, `"month"` when `days_back <= 30`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| UUID generation | Custom random ID | `uuid.uuid4().hex[:8]` | Already used in tavily_search.py via stdlib |
| URL dedup | Custom set tracking | Python `set` with URL as key | Both scripts already do this; it's trivial |
| Date parsing from text | Complex regex chains | Current `parse_date_from_text()` | Already handles YYYY-MM-DD and relative dates; good enough for Phase 1 |
| CLI argument parsing | Manual `sys.argv` | `argparse.ArgumentParser` | Already used in tavily_search.py; standard library |

**Key insight:** This is a consolidation phase, not a feature phase. Every function already exists in one of the two scripts. The task is selecting the best implementation of each and wiring them together with the config dict.

## Common Pitfalls

### Pitfall 1: Losing talent_search.py's `include_domains` Behavior
**What goes wrong:** The new `search.py` omits domain filtering, so results come from any domain (like tavily_search.py does), losing the focused English tech media coverage that talent_search.py provides.
**Why it happens:** tavily_search.py doesn't use `include_domains`, so a naive merge might drop it.
**How to avoid:** The `SEARCH_CONFIG` domain groups must be wired into the Tavily call. When `english_tech` is enabled, pass its domains as `include_domains`.
**Warning signs:** Search results include random blogs, forums, or non-tech sites that were never in the original talent_search.py results.

### Pitfall 2: Candidate Format Incompatibility with add-event.js
**What goes wrong:** The new unified format doesn't match what `add-event.js`'s `validateEvent()` expects (required fields: `person_name`, `event_type`, `date_event`, `source_url`, `summary`).
**Why it happens:** Changing field names or dropping fields during consolidation.
**How to avoid:** The D-07 unified format already includes all fields that `validateEvent()` requires. Verify explicitly in testing.
**Warning signs:** `validateEvent()` returns `{ valid: false }` for candidate events.

### Pitfall 3: Deleting Old Scripts Before Verifying Parity
**What goes wrong:** Old scripts are deleted, then a subtle behavior difference is discovered (e.g., talent_search.py output had `_candidate: True` which downstream tooling checks for).
**Why it happens:** Eager cleanup before verification.
**How to avoid:** Keep old scripts until the new script produces equivalent output. Test with the same queries and compare candidate event fields.

### Pitfall 4: Double-Counting Duplicate Queries
**What goes wrong:** Both scripts had overlapping queries (e.g., "AI researcher joins leaves OpenAI Google DeepMind Anthropic" appears in both). Naively concatenating query lists doubles API calls for the same content.
**Why it happens:** Copying queries from both scripts without deduplication.
**How to avoid:** Deduplicate the query list across both scripts when building `SEARCH_CONFIG`. The current two scripts have 10 unique queries total (6 from tavily_search + 4 from talent_search, with 1-2 overlaps).

## Code Examples

### Query Inventory (Before Consolidation)

**tavily_search.py queries (6):**
1. `"AI researcher joins leaves OpenAI Google DeepMind Anthropic"`
2. `"AI talent move chief scientist leaves joins startup"`
3. `"top AI engineer researcher joins new company"`
4. `"AI lab researcher departure hiring"`
5. `"vice president AI leaves joins"`
6. `"co-founder AI startup leaves"`

**talent_search.py queries (4):**
1. `"AI talent move joins leaves OpenAI Google DeepMind Anthropic Meta"` (overlaps with tavily #1)
2. `"AI researcher joins leaves startup"` (overlaps with tavily #2)
3. `"chief scientist VP AI leaves joins"` (overlaps with tavily #5)
4. `"top AI engineer joins new company"` (overlaps with tavily #3)

**Conclusion:** talent_search.py's queries are mostly subsets of tavily_search.py's queries. After deduplication, there are approximately 6-7 unique queries. The config dict should contain the unique set, logically grouped.

### Domain Inventory (from talent_search.py)

```python
# 9 domains currently used by talent_search.py's include_domains
"techcrunch.com", "theinformation.com", "bloomberg.com",
"reuters.com", "businessinsider.com", "venturebeat.com",
"x.com", "linkedin.com", "subsight.com"
```

### Candidate Event Field Diff (the format problem CONS-04 solves)

| Field | tavily_search.py | talent_search.py | Unified (D-07) |
|-------|-----------------|------------------|----------------|
| `id` | `evt-{uuid8}` | absent | `evt-{uuid8}` |
| `person_name` | `""` | `""` | `""` |
| `event_type` | `"move"` | `"move"` | `"move"` |
| `date_event` | auto-parsed | `""` | auto-parsed |
| `from_company` | `""` | `""` | `""` |
| `to_company` | `""` | `""` | `""` |
| `role` | `""` | `""` | `""` |
| `source_url` | url | url | url |
| `date_discovered` | today | today | today |
| `summary` | content[:300] | content[:200] | content[:300] |
| `tags` | `[]` | `[]` | `[]` |
| `_needs_review` | `True` | absent | `True` |
| `_source_title` | title | title | title |
| `_mentioned_companies` | extracted list | absent | extracted list |
| `_source_content` | absent | content[:500] | content[:500] |
| `_candidate` | absent | `True` | **dropped** |
| `_source_url` | absent | url | **dropped** (use `source_url`) |
| `_query` | absent | query | **dropped** |
| `_search_date` | absent | iso timestamp | **dropped** |
| `_search_query` | query | absent | **dropped** |
| `_search_time` | iso timestamp | absent | **dropped** |

### Reusable Functions from tavily_search.py (HIGH confidence -- read from source)

```python
# All verified from tavily_search.py source (261 lines)
load_existing_events(data_path) -> list   # line 18-24 -- identical to talent_search's load_events
save_events(events, data_path)            # line 27-30 -- identical
generate_event_id() -> str                # line 33-36 -- uuid-based
is_duplicate(new_event, existing_events) -> bool  # line 39-53 -- 4-field dedup
parse_date_from_text(text) -> str         # line 56-74 -- YYYY-MM-DD + relative dates
extract_person_and_companies(text, title) -> dict  # line 77-102 -- 30+ company list
```

### Reusable Functions from talent_search.py (HIGH confidence -- read from source)

```python
# All verified from talent_search.py source (162 lines)
load_events(data_path) -> list   # line 16-22 -- same as tavily's load_existing_events
save_events(events, data_path)   # line 25-28 -- identical
# No unique functions -- all logic is inline in search_talent_news() and analyze_for_events()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded queries in function body | Config dict at module level | This phase | Easier to add/modify queries without touching logic |
| Two separate scripts with overlapping code | Single unified script | This phase | One source of truth, easier to maintain |
| Inconsistent candidate event fields | Unified format per D-07 | This phase | Downstream tools (add-event.js, manual review) see consistent data |

**Not applicable for this phase:** No deprecated libraries or patterns to address. Both scripts use current `tavily-python` patterns.

## Open Questions

1. **Should `save_events()` remain in the new `search.py`?**
   - What we know: Both old scripts have `save_events()` but neither actually writes to `events.json` during search (candidates go to `.temp/`). The `save_events()` function exists but is unused in the search flow.
   - What's unclear: Whether to keep it for future use (Phase 2 may need it for auto-merge) or remove dead code.
   - Recommendation: Keep it. It's 3 lines and Phase 2 might use it.

2. **Should `--auto-merge` flag be preserved?**
   - What we know: tavily_search.py has `--auto-merge` argparse flag but no implementation (it's defined but never used in `main()`).
   - What's unclear: Whether to carry forward this vestigial flag.
   - Recommendation: Drop it. It's dead code. If Phase 5 needs auto-merge, add it then.

## Environment Availability

Step 2.6: SKIPPED (no external dependencies beyond what the project already uses -- tavily-python and Python 3 stdlib).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (none installed yet) |
| Config file | none -- see Wave 0 |
| Quick run command | `python3 scripts/search.py --days 1` |
| Full suite command | Wave 0 -- no tests exist yet |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CONS-01 | Single search.py produces same results as running both old scripts | integration | `python3 -m pytest tests/test_search.py::test_search_produces_results -x` | Wave 0 |
| CONS-02 | Queries defined in config dict, not in function bodies | unit | `python3 -m pytest tests/test_search.py::test_queries_in_config -x` | Wave 0 |
| CONS-03 | Domain groups have english_tech enabled, others disabled | unit | `python3 -m pytest tests/test_search.py::test_domain_groups -x` | Wave 0 |
| CONS-04 | Candidate events have all unified fields | unit | `python3 -m pytest tests/test_search.py::test_candidate_format -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** Run `python3 scripts/search.py --days 1 --output .temp/test_candidates.json` to verify the script executes without errors
- **Per wave merge:** Manual review that candidate output format matches D-07 specification
- **Phase gate:** Script runs successfully, old scripts deleted, `deduplicate.py` pre-commit hook still works

### Wave 0 Gaps
- [ ] `tests/test_search.py` -- unit tests for config structure, candidate format, dedup behavior
- [ ] `tests/conftest.py` -- shared fixtures (sample events, mock TavilyClient)
- [ ] `pytest` installation: `pip install pytest` -- no test framework detected
- [ ] `tests/__init__.py` -- test package init

## Sources

### Primary (HIGH confidence)
- `scripts/tavily_search.py` (261 lines) -- read in full, all functions cataloged
- `scripts/talent_search.py` (162 lines) -- read in full, all functions cataloged
- `scripts/deduplicate.py` (146 lines) -- read in full, confirmed no overlap with search scripts
- `add-event.js` (204 lines) -- read in full, validated candidate format compatibility
- `data/events.json` -- schema analysis: 172 new-schema events, 1 old-schema event
- `.planning/phases/01-脚本整合/01-CONTEXT.md` -- all locked decisions D-01 through D-08

### Secondary (MEDIUM confidence)
- Tavily API parameters (topic, country, exact_match, include_domains, search_depth, time_range, max_results) -- verified from training data, official docs URL blocked by firewall

### Tertiary (LOW confidence)
- None for this phase -- all findings are from direct source code reading

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- only tavily-python + stdlib, already in use
- Architecture: HIGH -- designed from reading both scripts' full source code
- Pitfalls: HIGH -- identified by comparing the two scripts' behavioral differences line-by-line

**Research date:** 2026-04-08
**Valid until:** 90 days (stable domain -- pure refactoring of existing code, no external API changes expected)
