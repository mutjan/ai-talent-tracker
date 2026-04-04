# Technology Stack: Search Optimization

**Project:** AI Talent Tracker - Search Optimization
**Researched:** 2026-04-04
**Scope:** Search technologies for monitoring AI talent across Chinese and English social media/news

---

## Recommended Stack

### Core Search: Tavily (Keep & Expand)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| tavily-python | 0.7.23 | Primary web search API | Already integrated; supports domain filtering, news topic mode, Chinese queries; one API covers both EN and CN indexed content |

**Tavily capabilities discovered (verified from source code):**

- `search_depth`: `"basic"`, `"advanced"`, `"fast"`, `"ultra-fast"` -- current scripts use `"advanced"` which is correct for recall
- `topic`: `"general"`, `"news"`, `"finance"` -- **not currently used**, should add `topic="news"` for better news results
- `include_domains` / `exclude_domains`: Already used in `talent_search.py`, not used in `tavily_search.py`
- `time_range`: `"day"`, `"week"`, `"month"`, `"year"` -- already used in `tavily_search.py`
- `country`: Filter by country (e.g., `"cn"` for China results) -- **not currently used**
- `exact_match`: Exact phrase matching -- **not currently used**, useful for specific person names
- `include_raw_content`: Get full page content in `"markdown"` or `"text"` format -- **not currently used**
- `extract`: Standalone URL content extraction (up to 20 URLs per call)
- `crawl` / `map`: Website structure discovery (crawl is invite-only)
- `research`: Comprehensive research reports (new feature)
- Free tier: 1,000 credits/month

**Confidence: HIGH** -- verified directly from source code (tavily.py on GitHub).

**Key insight:** Tavily can search Chinese content. It indexes whatever its search engines find. The limitation is not language support but whether Chinese social media platforms (Weibo, Zhihu) are indexable by search engines. The answer: partially. Weibo posts indexed via Weibo's public pages, Zhihu answers are indexed, but 公众号 (WeChat articles) are poorly indexed by any web search engine.

---

### Chinese Social Media: Dedicated APIs Needed

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| TikHub SDK | 1.13.0 | Unified Chinese social media API | Covers Weibo, Zhihu, Douyin, Xiaohongshu, Bilibili via single paid API |
| justoneapi | latest | Alternative unified API | Similar coverage to TikHub, simpler pricing |

**Why add a dedicated Chinese API:** Tavily's `include_domains` can target `weibo.com` and `zhihu.com` but the results are limited because:
1. Weibo mobile-only content is not well indexed by search engines
2. Zhihu login-walled content is not indexed
3. 脉脉 (Maimai) has almost zero search engine indexation
4. 公众号 (WeChat articles) require WeChat's own ecosystem

**TikHub (recommended):**
- Python SDK available on PyPI (`tikhub` v1.13.0)
- Covers: Weibo, Zhihu, Douyin, Xiaohongshu, Kuaishou, Bilibili, Instagram, YouTube, Twitter/X
- Async Python SDK
- Paid service (per-request pricing)
- GitHub: `TikHub/TikHub-API-Python-SDK` (611 stars)

**Confidence: MEDIUM** -- TikHub is on PyPI and has decent GitHub traction, but have not verified pricing or reliability in production. Needs trial.

---

### English Social Media: Hybrid Approach

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Tavily (existing) | 0.7.23 | X/Twitter content via web search | X posts are indexed by search engines; Tavily can find them via `include_domains=["x.com"]` |
| HN Algolia API | REST (free) | Hacker News monitoring | Free, no auth needed, real-time, has `/api/v1/search` with `tags=story` |
| twscrape | latest (2323 stars) | X/Twitter direct scraping (fallback) | Only if Tavily X coverage is insufficient |

**X/Twitter approach:** The existing script already has `x.com` in `include_domains`. This works for public tweets that search engines index. Tavily's `topic="news"` mode should improve X coverage. Direct X API access is expensive ($100/mo minimum for Basic tier) and rate-limited. `twscrape` is an alternative but carries ToS risk.

**LinkedIn approach:** LinkedIn is extremely aggressive against scraping. The existing `linkedin.com` in `include_domains` works for public posts and articles. For deeper coverage, the only reliable path is LinkedIn's official API (requires app review, limited to own-company data). **Recommendation: do not invest in LinkedIn beyond what Tavily already indexes.**

**Hacker News:** The Algolia HN Search API (`hn.algolia.com/api/v1/search`) is free, requires no auth, and returns JSON. Very good for catching AI talent discussions. Query example: `https://hn.algolia.com/api/v1/search?query=AI+researcher+joins&tags=story`.

**Confidence: HIGH** for HN API (free, well-documented); **MEDIUM** for Tavily X coverage (depends on search engine indexation).

---

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tavily-python | 0.7.23 | Core search | Always -- primary search engine |
| tikhub | 1.13.0 | Chinese social media | When Tavily Chinese coverage is insufficient |
| requests | latest | HTTP client | HN API, any REST API calls |
| schedule or APScheduler | latest | Job scheduling | If moving beyond GitHub Actions cron |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Web Search | Tavily | SerpApi | SerpApi is Google SERP scraping; Tavily is purpose-built for AI/LLM use cases with better content extraction. SerpApi is $50/mo minimum vs Tavily free tier. |
| Web Search | Tavily | Exa (exa-py) | Exa excels at semantic search but is more expensive and not needed for keyword-based talent tracking. Tavily's `include_domains` is sufficient. |
| Chinese Social | TikHub | Direct Weibo/Zhihu scraping | Fragile, requires anti-captcha, IP rotation, legal risk. TikHub handles this for a fee. |
| Chinese Social | TikHub | Baidu/Sogou Search API | Baidu API is expensive, enterprise-oriented, and no better than Tavily for this use case. |
| X/Twitter | Tavily + twscrape | X API ($100/mo) | Too expensive for the marginal coverage gain over Tavily's search. |
| LinkedIn | Tavily (passive) | LinkedIn API | Requires company page ownership; can't monitor arbitrary people's movements. |
| Scheduling | GitHub Actions | Self-hosted cron / APScheduler | GitHub Actions is free and already working; switch only if need more than 6-hour frequency. |

---

## Recommended Configuration Changes

### Immediate (No New Dependencies)

1. **Add `topic="news"`** to all Tavily search calls -- better news filtering
2. **Add `country="cn"`** parameter for Chinese queries -- improves Chinese content ranking
3. **Add Chinese search queries** (no API change needed):
   - "AI 人才 加入 离职 OpenAI Google DeepMind Anthropic"
   - "AI 科学家 离职 创业"
   - "大模型 人才 变动"
   - "首席科学家 副总裁 AI 离职 加入"
4. **Add Chinese domain targets** to `include_domains`:
   - `weibo.com`, `zhihu.com`, `36kr.com`, `jiqizhixin.com`, `pingwest.com`
5. **Add `include_raw_content="markdown"`** for deeper content extraction (2 credits per result vs 1)
6. **Use `exact_match=True`** for person-name queries to reduce noise

### Phase 2 (New Dependency)

7. **Integrate TikHub SDK** for Weibo/Zhihu direct content access
8. **Add HN Algolia API** integration (free, no SDK needed -- just `requests`)

---

## API Credit Budget Estimate

Current usage: ~24-36 Tavily credits/day (4-6 queries x 4-6 results each)

With expansion:
- 6 English queries + 6 Chinese queries = 12 queries/day
- Each with `search_depth="advanced"` = 2 credits per query
- Total: ~24 credits/day = ~720/month (within free 1,000 tier)
- With `include_raw_content`: double to ~1,440/month (need paid tier ~$0.005/credit = ~$2.20/month extra)

**Verdict:** Current Tavily free tier is sufficient even with Chinese queries. Adding raw content extraction may push to paid tier, but cost is negligible.

---

## Installation

```bash
# Existing (no change needed)
pip install tavily-python

# Phase 2 additions
pip install tikhub        # Chinese social media API
pip install requests      # HN API (usually already available)
```

---

## Sources

- tavily-python source code: `github.com/tavily-ai/tavily-python` (verified 2026-04-04)
- TikHub PyPI: `pypi.org/project/tikhub` v1.13.0 (verified 2026-04-04)
- twscrape GitHub: `github.com/vladkens/twscrape` 2323 stars (verified 2026-04-04)
- HN Algolia API: `hn.algolia.com/api` (free, public)
- Existing scripts: `scripts/talent_search.py`, `scripts/tavily_search.py` (read 2026-04-04)
