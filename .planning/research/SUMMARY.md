# Project Research Summary

**Project:** AI Talent Tracker — Search Optimization
**Domain:** AI talent intelligence / search monitoring
**Researched:** 2026-04-04
**Confidence:** MEDIUM-HIGH

## Executive Summary

This is a brownfield batch-search system that monitors news and social media for AI talent movements (hires, departures, promotions). The current system runs 4-6 hardcoded English queries via Tavily API against a fixed list of Western tech media domains. It misses approximately 40% of the tracked talent pool because Chinese companies (DeepSeek, Moonshot, Zhipu, Baichuan, etc.) are covered almost exclusively in Chinese-language sources that are never queried. The core problem is coverage breadth and query timeliness, not search technology.

The research converges on a clear recommendation: consolidate the two diverged search scripts into one config-driven pipeline, then expand coverage in a controlled sequence. Tavily remains the primary search provider (already integrated, free tier sufficient, supports Chinese queries and domain filtering). Adding Chinese query strings and media domains costs zero in new dependencies and immediately doubles coverage. A dedicated Chinese social media API (TikHub) and Hacker News integration are deferred to Phase 2 once the core pipeline is clean.

The dominant risk is operational: expanding search without fixing dedup and quota management first will flood the human reviewer with duplicates and silent failures. The architecture research and pitfalls research independently identified the same dependency order -- consolidate first, then expand -- which strongly validates the recommended phasing.

## Key Findings

### Recommended Stack

Core technologies with rationale. See [STACK.md](./STACK.md) for full details.

- **Tavily (keep and expand):** Already integrated, supports Chinese queries via `include_domains` and `country="cn"`, free tier covers expanded usage (~720 credits/month without raw content, ~1440 with). Use underutilized params: `topic="news"`, `exact_match=True`, `include_raw_content="markdown"`.
- **TikHub SDK (deferred):** Python SDK (v1.13.0, 611 GitHub stars) covers Weibo, Zhihu, Douyin, Xiaohongshu. Needed because search engines poorly index mobile-only and login-walled Chinese social content. Add in Phase 2.
- **HN Algolia API (deferred):** Free, no auth, real-time. Simple `requests` call to `hn.algolia.com/api/v1/search`. Good for catching AI talent discussions on Hacker News.
- **No additional search APIs needed:** SerpApi ($50/mo minimum), Exa (semantic, overkill), and direct Weibo/Zhihu scraping (fragile, legal risk) were all evaluated and rejected.

### Expected Features

See [FEATURES.md](./FEATURES.md) for full details.

**Must have (table stakes):**
- Chinese-language search queries — ~9 of 25 tracked companies are Chinese; English-only queries cannot find Chinese coverage
- Expanded domain coverage — Chinese tech media (36kr.com, jiqizhixin.com), X/Twitter, LinkedIn
- Cross-batch URL dedup — persist seen URLs across runs to prevent daily duplicates
- Merge two search scripts — single code path is prerequisite for all other work
- Consistent candidate output format — scripts currently diverge in field naming

**Should have (differentiators):**
- Dynamic query generation from events.json — system self-improves as dataset grows
- X/Twitter focused queries — catches self-announcements of job changes
- Company-specific query templates — per-company queries catch stories generic queries miss
- Search result freshness scoring — sort by Tavily `score * recency` to reduce review burden
- Bilingual summary extraction — regex-based Chinese name/company extraction

**Defer (v2+):**
- Temporal clustering detection — needs larger dataset (>500 events)
- LinkedIn deep coverage — LinkedIn blocks crawlers aggressively; Tavily passive indexing is sufficient
- Full-text search over events.json — client-side filtering is adequate at current scale (~150 events)

### Architecture Approach

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full details.

Single pipeline: Query Generator -> Search Executor -> Candidate Processor -> Human Review -> Merge. Key architectural decisions:

- **Config-driven queries** (not hardcoded in function bodies) — query definitions as Python dicts, easy to add Chinese/dynamic queries without touching logic
- **Domain set abstraction** — named domain groups (english_tech, chinese_tech, social) instead of inline lists
- **Cross-batch dedup via seen_urls.json** — persistent file tracking all URLs ever returned, pruned at 90 days
- **Schema migration** — unify the dual old/new schema in events.json before expanding

### Critical Pitfalls

See [PITFALLS.md](./PITFALLS.md) for full details.

1. **Name variant explosion in dedup** — same person appears as "Ilya Sutskever" (EN), "苏茨克维" (CN transliteration). Exact string matching breaks. Fix: canonical name mapping table, normalize before dedup.
2. **Silent API quota exhaustion** — expanding queries without rate limiting or quota tracking causes silent mid-run failures. Fix: track query count, add exponential backoff, fail loudly on exhaustion.
3. **Cross-batch URL dedup gap** — dedup only works within a single run; same article reappears daily. Fix: maintain `.temp/seen_urls.json` across all runs.
4. **Chinese encoding/normalization traps** — simplified vs traditional Chinese, mixed-language content, JSON re-serialization without `ensure_ascii=False`. Fix: NFKC normalization, simplified-to-traditional mapping for key terms.
5. **Diverged script logic** — `talent_search.py` and `tavily_search.py` share 70% identical code but have drifted. Adding features to both doubles work. Fix: merge first, expand second.

## Implications for Roadmap

Based on research, suggested 5-phase structure:

### Phase 1: Consolidate and Stabilize
**Rationale:** All research sources agree this must come first. Two diverged scripts with inconsistent schemas make every subsequent change twice as error-prone. Schema migration eliminates fallback logic in every consumer.
**Delivers:** Single unified search script, config-driven query definitions, domain set abstraction, schema migration to one format
**Addresses:** Table stakes: merge scripts, consistent output format, correct time_range usage
**Avoids:** Pitfall 7 (diverged scripts), Pitfall 12 (schema evolution without migration)
**Research flag:** LOW — well-documented refactoring patterns, no new APIs

### Phase 2: Cross-Batch Dedup
**Rationale:** Must exist before expanding query volume. Without this, daily runs with more queries generate overwhelming duplicate candidates, destroying operator trust.
**Delivers:** seen_urls.json persistence, URL filter in candidate processor, 90-day pruning, dedup backup before write
**Addresses:** Table stakes: cross-batch URL dedup
**Avoids:** Pitfall 3 (cross-batch dedup gap), Pitfall 8 (no backup before destructive dedup), Pitfall 11 (candidate file accumulation)
**Research flag:** LOW — straightforward file-based state management

### Phase 3: Expand Query Coverage
**Rationale:** Now safe to expand because dedup is in place. Chinese queries and domain expansion cost zero new dependencies and immediately double talent pool coverage.
**Delivers:** Chinese query templates, Chinese media domain targets, X/Twitter targeting, Tavily param optimization (`topic="news"`, `country="cn"`, `exact_match`)
**Addresses:** Table stakes: Chinese-language queries, expanded domain coverage
**Avoids:** Pitfall 1 (name variants — requires normalization layer), Pitfall 4 (encoding traps — requires NFKC normalization), Pitfall 9 (source quality — requires trust tiers)
**Research flag:** MEDIUM — Chinese query effectiveness needs validation; TikHub integration timing unclear

### Phase 4: Dynamic Query Generation
**Rationale:** Depends on stable pipeline (Phase 1) and dedup (Phase 2). Static queries become stale; dynamic queries from events.json keep the system self-improving.
**Delivers:** Term extraction from events.json, person/company supplementary queries, capped at configurable limit, company-specific query templates, freshness scoring
**Addresses:** Table stakes: dynamic query generation; Differentiators: X/Twitter focused queries, company-specific templates, freshness scoring
**Avoids:** Pitfall 6 (query explosion — cap and prioritize by recency), Pitfall 2 (quota exhaustion — track query count before execution)
**Research flag:** LOW — algorithm is straightforward frequency counting with caps

### Phase 5: Automation and Scheduling
**Rationale:** Last because automation amplifies both signal and noise. Only valuable when pipeline produces clean, deduplicated output with manageable candidate volume.
**Delivers:** GitHub Actions daily cron workflow, workflow_dispatch manual fallback, execution logging, candidate file cleanup
**Addresses:** Timeliness requirement (same-day discovery)
**Avoids:** Pitfall 10 (GitHub Actions schedule mismatch), Pitfall 2 (quota exhaustion at higher frequency)
**Research flag:** LOW — GitHub Actions cron is well-documented

### Phase Ordering Rationale

- Phase 1 first because all research sources independently concluded that extending two diverged scripts creates compounding bugs. The 70% code overlap means every feature is implemented twice.
- Phase 2 before Phase 3 because expanding coverage without dedup floods the reviewer. Architecture research: "expanding query coverage without cross-batch dedup will flood the operator with duplicates, making the system unusable."
- Phase 3 before Phase 4 because static Chinese queries are testable and stable; dynamic queries depend on a populated events.json and introduce variables harder to debug.
- Phase 5 last because pitfalls research notes: "automating too early amplifies noise." GitHub Actions cron reliability issues (5-15 min delays, skipped runs) need the pipeline to be fault-tolerant first.
- TikHub and HN Algolia integration can be introduced during Phase 3 or as a Phase 3b once Tavily-only Chinese coverage is validated and gaps are identified.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3:** Chinese query effectiveness validation — need to run test queries and measure recall before committing to specific query templates. TikHub integration timing decision (is Tavily alone sufficient?).
- **Phase 4:** Dynamic query cap tuning — what cap keeps API costs within budget while maximizing recall?

Phases with standard patterns (skip research-phase):
- **Phase 1:** Standard refactoring/merge — well-documented patterns
- **Phase 2:** Simple file-based persistence — no new technology
- **Phase 5:** GitHub Actions cron — extensively documented

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Tavily capabilities verified from source code. TikHub on PyPI with decent traction. HN API is free and well-documented. |
| Features | HIGH | Table stakes directly derived from PROJECT.md requirements and codebase analysis. Chinese coverage gap is quantifiable (9 of 25 companies). |
| Architecture | HIGH | Based on direct codebase analysis. Component boundaries and data flow are clear. Schema duality confirmed. |
| Pitfalls | HIGH | All 12 pitfalls traced to specific code locations (file + line number). Phase-specific warnings match architecture build order. |

**Overall confidence:** HIGH — all four research sources converge on the same conclusions from independent analysis. The recommended phase structure is validated by multiple independent dependency analyses.

### Gaps to Address

- **TikHub pricing and reliability:** Needs a trial account to validate before committing to integration. Handle during Phase 3 planning.
- **Chinese query recall rate:** Unknown what percentage of Chinese talent news Tavily can find vs. what requires TikHub. Run a benchmark during Phase 3.
- **Operator review time scaling:** At current 150 events, review takes 5-10 min. At 500+ with Chinese coverage, may reach 20-40 min. Consider freshness scoring (low complexity differentiator) as a quick win during Phase 3.
- **Events.json schema inconsistency:** The dual schema (old: `person`/`type`/`from`/`to`; new: `person_name`/`event_type`/`from_company`/`to_company`) must be migrated in Phase 1. Migration script is simple but needs a backup before execution (Pitfall 8).

## Sources

### Primary (HIGH confidence)
- Codebase: `scripts/tavily_search.py`, `scripts/talent_search.py`, `scripts/deduplicate.py` — direct analysis
- Tavily source: `github.com/tavily-ai/tavily-python` — API parameter verification
- Project scope: `.planning/PROJECT.md` — constraints and requirements

### Secondary (MEDIUM confidence)
- TikHub: `pypi.org/project/tikhub` v1.13.0 — existence and API surface verified, pricing/reliability unknown
- HN Algolia API: `hn.algolia.com/api` — free, public, well-documented
- twscrape: `github.com/vladkens/twscrape` (2323 stars) — X/Twitter scraping alternative, carries ToS risk

### Tertiary (LOW confidence)
- Tavily Chinese content coverage quality — inference from API capabilities, not benchmarked
- GitHub Actions cron reliability — based on known issues documentation, not observed in this project

---
*Research completed: 2026-04-04*
*Ready for roadmap: yes*
