# Domain Pitfalls: AI Talent Tracker Search Optimization

**Domain:** AI talent/news tracking search system
**Researched:** 2026-04-03
**Confidence:** HIGH (based on codebase analysis)

## Critical Pitfalls

### Pitfall 1: Name Variant Explosion in Deduplication

**What goes wrong:** The current dedup key (`person_name|from_company|to_company|date_event`) breaks when expanding to Chinese sources because the same person appears under different name variants: "Ilya Sutskever" (English), "Ilya Sutskever离开OpenAI" (mixed), "苏茨克维" (Chinese transliteration), "Илья Суцкевер" (Cyrillic). Company name variants compound this: "Google", "Google DeepMind", "DeepMind", "Alphabet" all refer to the same entity in different contexts.

**Why it happens:** The dedup script in `scripts/deduplicate.py` (line 35-40) does exact string matching after `.lower()`. This works for English-only, fixed-domain search but shatters when the same event is reported across languages and outlets with different name spellings.

**Consequences:** Duplicate events accumulate silently. At 150 events this is manageable; at 1000+ with multi-language coverage, the dataset becomes unreliable and user trust erodes.

**Prevention:** Build a canonical name mapping table (person aliases, company aliases) and normalize before dedup matching. Fuzzy matching alone is insufficient because "Ilya" and "苏茨克维" have zero string similarity.

**Detection:** Periodically query events.json for the same `source_url` appearing under different `person_name` values. Count events where `from_company` or `to_company` match known aliases.

**Phase:** Address during search expansion phase (when Chinese queries are added), not after.

---

### Pitfall 2: Silent API Quota Exhaustion

**What goes wrong:** Adding Chinese media domains, X/Twitter, and dynamic query generation multiplies API calls. Current architecture runs 4-6 queries per script. With dynamic queries from high-frequency names in events.json, this could easily reach 20-50 queries per run. `search_depth="advanced"` (used in both scripts) costs more per request. There is no rate limiting, retry logic, or quota tracking anywhere in the codebase.

**Why it happens:** Both `talent_search.py` and `tavily_search.py` iterate through queries in a flat loop with no backoff, no exponential retry, and no awareness of remaining quota. A failed query (line 70-71 in talent_search.py, line 143-145 in tavily_search.py) silently continues with no retry.

**Consequences:** Mid-run failures leave partial results. No alert that coverage was degraded. Failed runs produce empty `.temp/candidates_*.json` files that look like "no news today" rather than "search broke".

**Prevention:**
1. Track query count before execution and cap at a configurable limit
2. Add exponential backoff on API errors (especially 429 rate limit)
3. Log quota consumption to a `.temp/search_quota.log` file
4. Fail loudly (non-zero exit code) when quota is exhausted mid-run, rather than silently continuing

**Detection:** After each run, compare query count vs. results count. If results/query ratio drops below a threshold, quota may be exhausted.

**Phase:** Must be implemented before increasing search frequency from weekly to daily.

---

### Pitfall 3: Cross-Batch URL Dedup Gap

**What goes wrong:** `talent_search.py` deduplicates URLs within a single search batch (line 74-82), but does NOT check against previously saved URLs from prior runs. `tavily_search.py` checks against existing events (line 191) but not against previously seen-but-rejected URLs. When search frequency increases to daily, the same article (especially from Chinese media, which may re-aggregate news for days) appears repeatedly as a "new" candidate.

**Why it happens:** No persistent search state exists. The only dedup target is `events.json` (accepted events), not a history of all seen URLs.

**Consequences:** Human reviewer sees the same article 3-5 times across different days. Review fatigue sets in, leading to either skipped reviews or careless acceptance of duplicates.

**Prevention:** Maintain a `.temp/seen_urls.json` file that records every URL ever returned by search, regardless of whether it was accepted as an event. Before adding a candidate to the output, check against this file.

**Detection:** Count unique URLs across a week of candidate files. If the same URL appears in 3+ files, cross-batch dedup is failing.

**Phase:** Implement in the first search expansion phase.

---

### Pitfall 4: Chinese Content Encoding and Normalization Traps

**What goes wrong:** Adding Chinese search queries and sources introduces several encoding pitfalls:
1. **Simplified vs Traditional Chinese:** "马斯克" (simplified) vs "馬斯克" (traditional) are different strings but the same person. Tavily may return either depending on the source.
2. **Mixed-language content:** Chinese tech articles frequently mix English terms ("OpenAI的前研究员Sam Altman..."). Person name extraction from mixed content is harder than pure English.
3. **JSON encoding:** `json.dump(..., ensure_ascii=False)` is correctly used in the codebase, but if any pipeline step re-serializes with default ASCII encoding, Chinese characters become `\uXXXX` escapes, breaking downstream matching.

**Why it happens:** The codebase has no Chinese text normalization. The dedup key uses raw strings. Any Unicode variation (full-width vs half-width punctuation, different dash characters in dates) breaks exact matching.

**Consequences:** Events from Chinese sources either duplicate English-source events or fail to match known persons/companies, creating data silos.

**Prevention:**
1. Normalize all text to NFKC Unicode form before dedup matching
2. Build a simplified-to-traditional Chinese mapping for key terms (company names, common surnames)
3. Never re-serialize JSON without `ensure_ascii=False`
4. Add a normalization step in the dedup pipeline that runs before key generation

**Detection:** Run a test suite of Chinese name variants through the dedup pipeline. If any variant produces a different dedup key than the canonical form, normalization is incomplete.

**Phase:** Must be addressed when adding Chinese queries and domains.

---

### Pitfall 5: Single API Provider Lock-In

**What goes wrong:** The entire search pipeline depends exclusively on Tavily API. PROJECT.md explicitly states "只用 Tavily API" as a constraint. If Tavily has an outage, pricing change, or deprecates a feature (e.g., `include_domains` support, Chinese content coverage quality), the entire system stops working.

**Why it happens:** Simplified architecture decision -- one API, one dependency. This is correct for the current phase but becomes a risk when expanding coverage.

**Consequences:** Complete coverage blackout during Tavily outages. No fallback, no degraded mode.

**Prevention:**
1. Abstract the search interface behind a common function (both scripts already have near-identical search functions -- extract to a shared module)
2. Design the candidate output format to be API-agnostic (it already mostly is)
3. Keep the abstraction ready so adding a second provider (e.g., direct RSS parsing, Google News RSS) is a one-script addition, not a rewrite

**Detection:** Monitor Tavily API response times and error rates. If error rate exceeds 10% on any run, investigate.

**Phase:** Architectural concern -- design the abstraction during the first search expansion phase, even if Tavily remains the only provider.

---

## Moderate Pitfalls

### Pitfall 6: Dynamic Query Explosion

**What goes wrong:** Extracting high-frequency person and company names from events.json to generate supplementary queries sounds straightforward but produces combinatorial explosion. With 50 unique persons and 20 unique companies in the dataset, naive generation creates hundreds of queries. Each query costs API quota.

**Prevention:** Cap dynamic queries at a fixed number (e.g., 10 per run). Prioritize by recency (persons in events from the last 30 days) rather than frequency. Combine multiple persons/companies into single queries rather than generating one query per person.

**Phase:** Implement during dynamic query generation phase.

---

### Pitfall 7: Diverged Script Logic Creates Inconsistent Behavior

**What goes wrong:** `talent_search.py` (162 lines) and `tavily_search.py` (261 lines) share ~70% identical logic but have diverged in: query construction, domain restrictions, output format, dedup approach. Adding search expansion features to both scripts doubles the work and guarantees they drift further apart.

**Prevention:** Extract shared functions (`load_events`, `save_events`, `search_with_tavily`, `is_duplicate`, `generate_event_id`) into a `scripts/lib/search_common.py` module. Both scripts import from it. This must happen before adding new search features.

**Phase:** First step of any search expansion work.

---

### Pitfall 8: No Backup Before Destructive Dedup

**What goes wrong:** `scripts/deduplicate.py` line 140 writes directly to `data/events.json`, overwriting the original. If the merge logic has a bug (e.g., incorrect completeness scoring, tag merging overwrites valuable data), events are permanently lost.

**Prevention:** Always create a timestamped backup (`data/events.json.backup.20260403_140000`) before writing. Add a `--dry-run` flag that prints what would be merged without writing.

**Phase:** Immediate fix, before any automated pipeline changes.

---

### Pitfall 9: Domain Trust Without Source Quality Scoring

**What goes wrong:** Expanding `include_domains` to Chinese social media (Weibo, Zhihu, Maimai) introduces low-quality sources. Unlike tech journalism (TechCrunch, Bloomberg), social media posts may contain rumors, speculation, or fabricated talent moves. The current architecture treats all search results equally.

**Prevention:**
1. Assign a trust tier to each domain (Tier 1: Bloomberg/Reuters, Tier 2: TechCrunch/The Information, Tier 3: X/Twitter, Tier 4: social media)
2. Display trust tier in the candidate review UI so the human reviewer can weigh source credibility
3. Do not auto-accept results from Tier 3+ sources

**Phase:** When adding social media domains to search.

---

### Pitfall 10: GitHub Actions Schedule Mismatch with Search Frequency

**What goes wrong:** PROJECT.md states the goal is daily search, but the GitHub Actions workflow (`pages.yml`) currently only handles deployment, not search execution. There is no scheduled workflow for search. Increasing frequency to daily requires creating a new workflow with `schedule: cron`, but GitHub Actions cron has known issues: delays of 5-15 minutes, skipped runs during high-load periods, and no guarantee of exact timing.

**Prevention:**
1. Create a dedicated `.github/workflows/search.yml` with cron schedule
2. Add a `workflow_dispatch` trigger as manual fallback
3. Log execution timestamps to detect skipped runs
4. Consider an external cron service (e.g., GitHub Actions + scheduled dispatch) as backup

**Phase:** When increasing search frequency.

---

## Minor Pitfalls

### Pitfall 11: Candidate File Accumulation

**What goes wrong:** Search scripts write timestamped candidate files (`.temp/candidates_20260403_140000.json`). With daily execution, 30 files accumulate per month. The `.temp/` directory is not in `.gitignore` (needs verification) and contains unreviewed candidates that may never be processed.

**Prevention:** Add `.temp/` to `.gitignore`. Implement a cleanup script that removes candidate files older than N days. Or: use a single rolling candidate file instead of timestamped ones.

**Phase:** Minor -- address when setting up daily automation.

---

### Pitfall 12: Event Schema Evolution Without Migration

**What goes wrong:** CONCERNS.md already documents mixed schema versions in events.json. Expanding search may introduce new event types (e.g., `promotion`, `board_join`) or new fields (e.g., `source_language`, `confidence_score`). Without a schema version and migration mechanism, the next expansion will create a third schema variant.

**Prevention:** Define a JSON schema for events. Add a `schema_version` field. Write migration scripts for version upgrades. Enforce schema validation in `add-event.js` and search scripts.

**Phase:** Before adding new event types or fields.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Adding Chinese queries | Name variant explosion (Pitfall 1), encoding traps (Pitfall 4) | Build normalization layer first |
| Dynamic query generation | Query explosion (Pitfall 6) | Cap and prioritize queries |
| Increasing frequency to daily | Quota exhaustion (Pitfall 2), cross-batch dedup gap (Pitfall 3), candidate file accumulation (Pitfall 11) | Add quota tracking, seen-URL file, cleanup |
| Adding social media domains | Source quality noise (Pitfall 9) | Implement trust tiers |
| Multi-provider architecture | Provider lock-in (Pitfall 5) | Abstract search interface early |
| Any automation changes | Diverged scripts (Pitfall 7), no backup before dedup (Pitfall 8) | Refactor to shared module, add dry-run |

## Sources

- Codebase analysis: `scripts/talent_search.py`, `scripts/tavily_search.py`, `scripts/deduplicate.py`
- Existing concerns: `.planning/codebase/CONCERNS.md`
- Project context: `.planning/PROJECT.md`
