# Architecture Patterns — Search Optimization

**Domain:** AI talent tracking search pipeline
**Researched:** 2026-04-03
**Confidence:** HIGH (based on codebase analysis and PROJECT.md requirements)

## Current Architecture Problems

The system has two parallel search scripts (`talent_search.py` and `tavily_search.py`) with overlapping but inconsistent behavior:

| Aspect | talent_search.py | tavily_search.py |
|--------|-----------------|-----------------|
| Domain restriction | 9 English tech media | None (all domains) |
| Query count | 4 fixed | 6 fixed |
| Chinese support | None | None |
| Duplicate check | Against events.json | Against events.json |
| Cross-batch dedup | No | No |
| Output format | Candidate with `_candidate` flag | Candidate with `_needs_review` flag |

Key gaps identified from PROJECT.md:
1. No Chinese search terms
2. No dynamic query generation from existing data
3. No Chinese media source domains
4. No X/Twitter domain targeting
5. No cross-batch URL dedup (same news re-found on consecutive days)
6. Weekly GitHub Actions vs desired daily frequency

## Recommended Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Search Pipeline                         │
│                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐ │
│  │  Query    │──▶│  Search  │──▶│ Candidate│──▶│  Human  │ │
│  │ Generator │   │ Executor │   │ Processor│   │  Review │ │
│  └──────────┘   └──────────┘   └──────────┘   └────┬────┘ │
│       ▲                                             │       │
│       │                                             ▼       │
│  ┌──────────┐                                  ┌─────────┐ │
│  │  events   │◀────────────────────────────────│  Merge  │ │
│  │  .json    │                                 │         │ │
│  └──────────┘                                  └─────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Component Boundaries

#### 1. Query Generator
**Responsibility:** Produce search queries from multiple strategies
**Input:** `data/events.json` (for dynamic term extraction)
**Output:** List of query strings
**Contains:** Static query templates + dynamic term extraction logic

**Sub-components:**
- **Static queries** -- Hardcoded English and Chinese query templates covering core talent movement patterns
- **Dynamic term extractor** -- Reads events.json, extracts top N person names and company names, generates supplementary queries like `"张三 加入 OpenAI"` or `"XXX leaves Google for"`

**Query strategies:**
1. English talent movement queries (existing, expanded to ~8-10)
2. Chinese talent movement queries (new, ~6-8, e.g., "AI 人才 加入 离职", "首席科学家 离开")
3. Dynamic person-focused queries (from high-frequency names in events.json)
4. Dynamic company-focused queries (from company names in events.json)

#### 2. Search Executor
**Responsibility:** Execute Tavily API calls with domain-specific configurations
**Input:** Query list from Query Generator
**Output:** Raw search results with metadata
**Location:** Replaces both `talent_search.py` and `tavily_search.py` search logic

**Domain configurations:**

| Domain Set | Domains | Purpose |
|-----------|---------|---------|
| English tech media | techcrunch.com, bloomberg.com, reuters.com, businessinsider.com, venturebeat.com, theinformation.com | English-language talent news |
| Chinese tech media | 36kr.com, jiemian.com, thepaper.cn, zhihu.com | Chinese-language talent news |
| Social platforms | x.com, linkedin.com | X/Twitter posts, LinkedIn updates |
| No restriction | (none) | General catch-all for queries 3-4 |

Each query should target a specific domain set. One query can span multiple domain sets by making separate API calls per domain set. This avoids the Tavily API `include_domains` limit noise.

**API call pattern:**
```
For each query:
  For each domain_set:
    call Tavily.search(query, include_domains=domain_set, search_depth="advanced", time_range="day")
```

#### 3. Candidate Processor
**Responsibility:** Deduplicate, classify, and format search results
**Input:** Raw search results from Search Executor
**Output:** `.temp/candidates_*.json` file

**Processing steps:**
1. **URL dedup** -- Remove results whose URL already exists in events.json source_url fields, OR in a persistent "seen URLs" file (`.temp/seen_urls.json`)
2. **Within-batch dedup** -- Same URL appearing from multiple queries (existing behavior)
3. **AI company detection** -- Scan content for known company names to pre-populate `from_company`/`to_company` guesses
4. **Date extraction** -- Parse event dates from content (existing logic, improved)
5. **Schema normalization** -- Output in new schema only (no dual-schema issue)

**Cross-batch dedup design:**

Maintain `.temp/seen_urls.json` containing all URLs that have ever been returned by searches (both accepted and rejected). Before writing candidates, filter out any result whose URL appears in this file. After human review, update seen_urls with all URLs from the batch (both accepted and rejected).

```
seen_urls.json structure:
{
  "urls": {
    "https://example.com/article1": "2026-04-01",
    "https://example.com/article2": "2026-04-02"
  },
  "last_updated": "2026-04-03T10:00:00"
}
```

Pruning: Remove entries older than 90 days to prevent unbounded growth.

#### 4. Human Review
**Responsibility:** Operator reviews candidate file, fills in missing fields
**Input:** `.temp/candidates_*.json`
**Output:** Validated events ready for merge

Stays manual per PROJECT.md constraints. Improved by better pre-population of fields (company detection, date extraction) to reduce manual effort.

#### 5. Merge
**Responsibility:** Append validated events to events.json, update seen_urls
**Input:** Reviewed candidates
**Output:** Updated `data/events.json` + `.temp/seen_urls.json`

Can be automated with a merge script (extension of `--auto-merge` flag in tavily_search.py) or remain manual.

### Data Flow

```
events.json ──────────────────────┐
    │                              │
    ▼                              │
┌──────────────┐                   │
│ Query        │ extracts top      │
│ Generator    │ persons/companies │
└──────┬───────┘                   │
       │ queries                   │
       ▼                           │
┌──────────────┐                   │
│ Search       │ calls Tavily API  │
│ Executor     │ per query+domain  │
└──────┬───────┘                   │
       │ raw results               │
       ▼                           │
┌──────────────┐  seen_urls.json   │
│ Candidate    │◄──────────────────┤
│ Processor    │                   │
└──────┬───────┘                   │
       │ candidates                │
       ▼                           │
┌──────────────┐                   │
│ Human Review │                   │
└──────┬───────┘                   │
       │ validated events          │
       ▼                           │
┌──────────────┐                   │
│ Merge        │───────────────────┘
│              │──► events.json
│              │──► seen_urls.json
└──────────────┘
       │
       ▼  git push
  GitHub Pages deploy
```

### Dynamic Search Term Generation

**Strategy:** Extract high-frequency entities from events.json to generate supplementary queries.

**Algorithm:**
1. Load all events from events.json
2. Count frequency of each `person_name` (normalize to lowercase)
3. Count frequency of each `from_company` and `to_company` (normalize)
4. Take top 20 persons and top 10 companies by frequency
5. For each top person: generate `"person_name 加入"` and `"person_name joins leaves"`
6. For each top company: generate `"company 人才"` and `"company AI talent joins leaves"`
7. Merge with static queries, deduplicate query list

**Why top persons matter:** A person who has appeared multiple times (e.g., moved between companies) is likely a high-profile figure whose future movements are newsworthy.

**Why top companies matter:** Companies with many departures/hires in the dataset (OpenAI, Meta, Google) are high-activity zones for talent movement.

### Build Order (Dependencies)

```
Phase 1: Consolidate search scripts
  └─ Create scripts/search_pipeline.py
  └─ Merge logic from talent_search.py and tavily_search.py
  └─ Output: single unified search script with config-driven queries

Phase 2: Add cross-batch dedup
  └─ Implement seen_urls.json tracking
  └─ Modify candidate processor to filter against seen URLs
  └─ Output: no more duplicate discovery across days

Phase 3: Expand query coverage
  └─ Add Chinese query templates
  └─ Add Chinese media domains (36kr.com, jiemian.com, etc.)
  └─ Add X/Twitter domain targeting
  └─ Output: broader coverage across languages and platforms

Phase 4: Dynamic query generation
  └─ Implement term extraction from events.json
  └─ Generate supplementary person/company queries
  └─ Output: queries adapt as dataset grows

Phase 5: Automate scheduling
  └─ Add GitHub Actions workflow for daily search execution
  └─ Commit results to a branch or create issue with candidates
  └─ Output: daily automated discovery
```

**Rationale for this order:**
- Phase 1 first: must consolidate before extending. Two scripts with divergent behavior will create bugs during expansion.
- Phase 2 before Phase 3: expanding query coverage without cross-batch dedup will flood the operator with duplicates, making the system unusable.
- Phase 3 before Phase 4: Chinese/static queries are stable and testable. Dynamic queries depend on a populated events.json and are harder to debug initially.
- Phase 5 last: automation is only valuable when the pipeline produces clean output. Automating too early amplifies noise.

### Schema Unification

Current system has dual schema (old first event uses `person`/`type`/`from`/`to`/`date`/`source`; rest use `person_name`/`event_type`/`from_company`/`to_company`/`date_event`/`source_url`).

**Recommendation:** Migrate all events to new schema in Phase 1. The `deduplicate.py` and `add-event.js` already handle both via fallback. Normalizing to one schema simplifies all downstream logic.

Migration script needed:
```
for event in events.json:
  if event has 'person' but not 'person_name':
    rename person -> person_name
    rename type -> event_type
    rename from -> from_company
    rename to -> to_company
    rename date -> date_event
    rename source -> source_url
```

## Patterns to Follow

### Pattern 1: Config-Driven Query Definitions
**What:** Define all search queries in a configuration structure (Python dict or JSON file), not hardcoded in function bodies.
**When:** All query-related code
**Why:** Makes it trivial to add/remove/tune queries without modifying logic code.
```python
QUERY_CONFIGS = [
    {
        "name": "english_talent_moves",
        "queries": ["AI researcher joins leaves ...", ...],
        "domain_sets": ["english_tech", "social"],
        "search_depth": "advanced",
        "time_range": "day"
    },
    {
        "name": "chinese_talent_moves",
        "queries": ["AI 人才 加入 离职", ...],
        "domain_sets": ["chinese_tech"],
        "search_depth": "advanced",
        "time_range": "day"
    },
]
```

### Pattern 2: Domain Set Abstraction
**What:** Define domain groups as named constants, not inline lists.
**When:** Any code that calls Tavily with `include_domains`
**Why:** Domains will be added/removed frequently. Central definition prevents drift between queries.
```python
DOMAIN_SETS = {
    "english_tech": ["techcrunch.com", "bloomberg.com", ...],
    "chinese_tech": ["36kr.com", "jiemian.com", ...],
    "social": ["x.com", "linkedin.com"],
    "general": None  # no restriction
}
```

### Pattern 3: Seen-URL Filter Before Output
**What:** Always filter results against the seen_urls file before writing candidates.
**When:** After collecting all raw results, before writing to .temp/
**Why:** Prevents operator fatigue from reviewing already-seen results.
```python
def filter_seen_urls(results, seen_urls_path):
    seen = load_seen_urls(seen_urls_path)
    return [r for r in results if r['url'] not in seen]
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Parallel Script Divergence
**What:** Maintaining two separate search scripts with different behaviors.
**Why bad:** Confusing which to run, inconsistent results, double maintenance.
**Instead:** Single script with configuration.

### Anti-Pattern 2: No Persistent Search History
**What:** Only checking duplicates against events.json (accepted events), not tracking rejected/searched URLs.
**Why bad:** Same news articles appear every day, wasting operator time.
**Instead:** Maintain seen_urls.json across all search runs.

### Anti-Pattern 3: Hardcoded Query Lists in Function Bodies
**What:** Writing query strings directly inside the search function.
**Why bad:** Adding Chinese queries or dynamic queries requires modifying the same function that handles API calls.
**Instead:** Separate query generation from API execution.

### Anti-Pattern 4: Schema Inconsistency
**What:** Allowing old and new field names to coexist indefinitely.
**Why bad:** Every consumer (scripts, add-event.js, deduplicate.py) needs fallback logic. Bugs hide in edge cases.
**Instead:** Migrate to single schema early.

## Scalability Considerations

| Concern | At 150 events (current) | At 500 events | At 2000 events |
|---------|------------------------|---------------|----------------|
| Query count | 4-6 static | ~30 (static + dynamic) | ~50+ (heavily dynamic) |
| API calls per run | 4-6 | ~60 (queries x domains) | ~100+ |
| Tavily API cost | ~$0.05/run | ~$0.60/run | ~$1.00/run |
| Candidate volume | 20-50/day | 100-200/day | 300+/day |
| Operator review time | 5-10 min | 20-40 min | 60+ min |
| seen_urls.json size | ~1KB | ~50KB | ~200KB |

**Key insight:** As dataset grows, operator review time is the bottleneck, not API cost. The architecture should optimize for reducing candidate noise (better dedup, better pre-filling) rather than just increasing search breadth.

## Sources

- Codebase analysis of `/scripts/tavily_search.py`, `/scripts/talent_search.py`, `/scripts/deduplicate.py`, `/add-event.js`
- PROJECT.md requirements for search optimization
- Tavily API parameters observed in existing code: `search_depth`, `time_range`, `include_domains`, `max_results`
- GitHub Actions workflow at `.github/workflows/pages.yml`
- events.json schema analysis (dual schema: old vs new field naming)

---

*Architecture analysis for search optimization: 2026-04-03*
