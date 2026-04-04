# Feature Landscape: AI Talent Tracker — Search Optimization

**Domain:** AI talent intelligence / search monitoring
**Researched:** 2026-04-04
**Confidence:** MEDIUM (WebSearch unavailable; based on codebase analysis, Tavily API knowledge, and project requirements)

## Executive Summary

The current system runs 4-6 hardcoded English queries against Tavily with a fixed domain whitelist. This misses a large fraction of AI talent news — particularly Chinese-language coverage and X/Twitter discussions. The feature landscape below categorizes what to build into three tiers, with clear dependencies and complexity ratings.

---

## Table Stakes

Missing any of these means the system **silently misses talent events** — the core value proposition fails.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Chinese-language search queries** | ~40% of tracked companies (DeepSeek, Moonshot, Zhipu, Baichuan, Lingyi, SenseTime, iFlytek, Baidu, Alibaba, Tencent) are Chinese. Current English-only queries cannot find Chinese-source coverage. | Low | Add Chinese query strings like "AI 人才 离职 加入", "首席科学家 离开", etc. to the existing `queries` list. |
| **Dynamic query generation from events.json** | Fixed queries become stale as new companies and people enter the ecosystem. The system should self-improve by extracting high-frequency person names and company names from existing events and generating supplementary queries. | Medium | Parse events.json, compute frequency, generate queries like `"person_name" joins leaves` and `company_name talent`. Need a cap (e.g., 20 dynamic queries) to stay within API budget. |
| **Cross-batch URL dedup** | Current dedup works within a single script run but not across runs. Running daily means the same story appears multiple times on different days (Tavily's `time_range="day"` may return yesterday's story). | Low | Persist seen URLs to a file (e.g., `.temp/seen_urls.json`) and skip them before generating candidates. The existing `is_duplicate()` checks event fields but not raw URLs. |
| **Correct `time_range` parameter usage** | `tavily_search.py` already uses `time_range="day"` but `talent_search.py` uses `date_from` computation manually. The two scripts diverge in behavior. Unify to always use `time_range`. | Low | Standardize across the single merged script. |
| **Expanded domain coverage** | Current whitelist (techcrunch, bloomberg, reuters, etc.) misses: Chinese tech media (36kr.com, qbitai.com, jiqizhixin.com), LinkedIn posts, and X/Twitter threads where talent news often breaks first. | Low | Add `include_domains` entries. Tavily can search x.com and some Chinese sites. |
| **Consistent candidate output format** | `talent_search.py` and `tavily_search.py` produce slightly different candidate schemas (e.g., `_source_title` vs `_source_content` field names, `_candidate` flag vs `_needs_review` flag). Merging them is error-prone. | Low | Merge scripts into one. Already flagged in CONCERNS.md. |

### Dependencies

```
Dynamic query generation → requires cleaned events.json (fix schema inconsistency first)
Cross-batch URL dedup → requires a persistent state file path convention
Expanded domains → no dependencies, can do immediately
Merge two scripts → prerequisite for all other table stakes features (single code path)
```

---

## Differentiators

Features that give **broader coverage than a naive search system**. Each directly increases the chance of catching a talent event.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **X/Twitter focused queries** | AI talent news frequently breaks on X (e.g., people announcing their own moves). Tavily supports `include_domains: ["x.com", "twitter.com"]`. Current scripts do include x.com but only as one of 9 domains with generic queries. Dedicated queries like `"[person_name] excited to announce" site:x.com` catch self-announcements. | Medium | Requires dynamic query generation first (to plug in known person names). X content is low-quality for extraction — need higher `max_results` to compensate. |
| **Company-specific query templates** | Instead of generic "AI researcher joins leaves", generate per-company queries: `"left OpenAI"`, `"joined Anthropic"`, `"departed DeepMind"`. This catches stories that generic queries miss because the article may not use the word "AI" or "researcher". | Medium | Source company list from events.json + a curated high-priority list (top 30 AI labs). Generates ~30 additional queries. |
| **Temporal clustering detection** | When multiple events hit the same company within a short window, it likely signals a larger trend (team exodus, leadership change, new lab launch). Detecting clusters provides early warning. | High | Post-processing on events.json. Not a search feature per se, but an analysis layer. Defer to later phase. |
| **Bilingual summary extraction** | Chinese articles about talent moves are currently not parsed at all (no candidate extraction for Chinese text). Adding basic Chinese NLP to `extract_person_and_companies()` would surface Chinese-source events. | Medium | Can use simple regex for common patterns: "XXX 离职/加入/转投 XXX". Full NLP is overkill. |
| **Search result freshness scoring** | Not all results are equal. A Tavily result with `score` > 0.8 and published today is more valuable than a low-score result from 3 days ago. Sorting candidates by freshness + relevance reduces review burden. | Low | Tavily returns a `score` field per result. Sort candidates by `score * recency_weight`. |
| **LinkedIn coverage via Tavily** | LinkedIn posts about job changes are a rich signal. Tavily can index some LinkedIn content. Add `linkedin.com` to domain list with targeted queries like `"[name] new role at"`. | Low | Tavily's LinkedIn coverage is limited (LinkedIn blocks most crawlers). Expect low yield but high signal when it hits. |

### Dependencies

```
X/Twitter focused queries → needs dynamic query generation + merged script
Company-specific query templates → needs dynamic query generation
Bilingual summary extraction → needs merged script (single code path to modify)
Search result freshness scoring → no dependencies, can add to existing pipeline
Temporal clustering detection → needs a stable event dataset, defer
```

---

## Anti-Features

Things to **deliberately NOT build**. Each adds complexity without proportional value or violates project constraints.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Real-time push notifications / webhooks** | PROJECT.md explicitly scopes out real-time monitoring ("当天发现即可"). Building push infrastructure (webhooks, Slack integration, email alerts) adds massive operational complexity for marginal value — checking once daily is sufficient. | Keep the daily batch model. If users want notifications, they can check the GitHub Pages site. |
| **Additional search APIs (Baidu, Sogou, Google)** | PROJECT.md constrains to Tavily only. Adding multiple search providers means managing multiple API keys, rate limits, result formats, and dedup across providers. | Maximize Tavily coverage first (Chinese queries, more domains). Only reconsider if Tavily coverage is proven insufficient after optimization. |
| **LLM auto-parsing of news into structured events** | PROJECT.md explicitly keeps human review. Auto-extraction is unreliable for this domain (people names are ambiguous, company names vary, event types are nuanced). False positives erode trust. | Keep human review workflow. Improve it instead: better candidate presentation, pre-filled fields where confidence is high. |
| **Social media account following / subscription** | Directly monitoring specific X accounts or LinkedIn profiles requires OAuth, API access (X API is expensive), and rate limit management. | Use Tavily as a proxy — it indexes social media content. The "X/Twitter focused queries" differentiator achieves the same goal without account-level access. |
| **Full-text search over events.json** | At 150-500 events, client-side filtering is perfectly adequate. Building a search index or adding Elasticsearch is overengineering. | Browser Ctrl+F or simple JS filter. If events exceed 2000+, reconsider. |
| **Machine learning for relevance scoring** | Training a classifier to predict which search results are talent events is premature. The dataset is too small (~150 confirmed events) and the signal-to-noise ratio of Tavily results is already high. | Simple keyword + company matching is sufficient at this scale. |
| **Multi-language translation pipeline** | Translating Chinese articles to English for a unified view adds latency and complexity. The audience can read Chinese (project uses Chinese for UI and docs). | Keep Chinese content in Chinese. Extract structured data (person, company, role) which is language-agnostic. |

---

## Feature Dependencies (Full Graph)

```
Merge two scripts (prerequisite for everything)
  │
  ├─ Chinese-language queries
  ├─ Expanded domain coverage
  ├─ Correct time_range usage
  │
  └─ Dynamic query generation from events.json
       │
       ├─ X/Twitter focused queries
       ├─ Company-specific query templates
       └─ Cross-batch URL dedup (needs stable query set first)

Bilingual summary extraction ──→ merged script
Search result freshness scoring ──→ no dependencies (add anytime)
Temporal clustering detection ──→ stable event dataset (defer)
```

---

## MVP Recommendation

Prioritize in this order:

1. **Merge the two scripts** — Single code path. Everything else is harder with two divergent scripts. (Table stakes, Low complexity)
2. **Add Chinese-language queries** — Immediately doubles coverage of the talent pool. (Table stakes, Low complexity)
3. **Expanded domain coverage** — Add Chinese tech media + social. (Table stakes, Low complexity)
4. **Cross-batch URL dedup** — Prevents daily runs from generating duplicate candidates. (Table stakes, Low complexity)
5. **Dynamic query generation from events.json** — Self-improving system. (Table stakes, Medium complexity)
6. **Search result freshness scoring** — Reduces human review burden. (Differentiator, Low complexity)
7. **X/Twitter focused queries** — Catches self-announcements. (Differentiator, Medium complexity)

Defer:
- **Temporal clustering detection** — Interesting but not essential until dataset is larger.
- **Company-specific query templates** — Wait until dynamic queries are proven stable.

---

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Table stakes features | HIGH | Directly derived from PROJECT.md requirements and codebase analysis |
| Chinese query necessity | HIGH | 9 of ~25 tracked companies are Chinese; current queries cannot find Chinese coverage |
| Tavily API capabilities | MEDIUM | Based on training data knowledge; WebSearch/WebFetch unavailable for verification |
| Differentiator ranking | MEDIUM | Without market research data, ranking is based on signal-to-noise estimation |
| Anti-features | HIGH | Directly backed by PROJECT.md scope constraints |

## Sources

- `/Users/lzw/Documents/LobsterAI/lzw/ai-talent-tracker/.planning/PROJECT.md` — Project scope and constraints
- `/Users/lzw/Documents/LobsterAI/lzw/ai-talent-tracker/.planning/codebase/CONCERNS.md` — Known issues (script duplication, schema inconsistency)
- `/Users/lzw/Documents/LobsterAI/lzw/ai-talent-tracker/scripts/tavily_search.py` — Current search implementation (6 fixed English queries, no Chinese)
- `/Users/lzw/Documents/LobsterAI/lzw/ai-talent-tracker/scripts/talent_search.py` — Alternative search (4 fixed English queries, domain whitelist)
- `/Users/lzw/Documents/LobsterAI/lzw/ai-talent-tracker/scripts/deduplicate.py` — Current dedup logic (field-based only, no URL persistence)
- Tavily API documentation (training data, MEDIUM confidence) — `search_depth`, `time_range`, `include_domains` parameter knowledge
