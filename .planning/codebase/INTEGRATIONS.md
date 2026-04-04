# External Integrations

**Analysis Date:** 2026-04-03

## APIs & External Services

**Tavily Search API:**
- Purpose: Automated AI talent news discovery via web search
- SDK: `tavily-python` (pip package, not pinned to version)
- Auth: `TAVILY_API_KEY` environment variable
- Usage in `scripts/talent_search.py` (lines 48-62): searches with `search_depth="advanced"`, filtered to tech news domains
- Usage in `scripts/tavily_search.py` (lines 127-133): searches with `search_depth="advanced"`, `time_range="day"`
- Both scripts run 4-6 search queries per execution covering AI talent movements
- Output: candidate events saved to `.temp/candidates_*.json` for human review

**Tracked domains for Tavily search** (`scripts/talent_search.py` lines 51-61):
- techcrunch.com, theinformation.com, bloomberg.com, reuters.com
- businessinsider.com, venturebeat.com, x.com, linkedin.com, subsight.com

## Data Storage

**Databases:**
- None -- flat file storage only

**File Storage:**
- `data/events.json` -- primary data store (150 records, 1884 lines)
- `.temp/candidates_*.json` -- temporary search results (gitignored)
- No database, no cloud storage

**Caching:**
- None

## Authentication & Identity

**Auth Provider:**
- None -- no user authentication system
- The site is publicly accessible on GitHub Pages

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- Console output only (`print()` in Python, `console.log()` in JS)
- No structured logging

## CI/CD & Deployment

**Hosting:**
- GitHub Pages at `https://mutjan.github.io/ai-talent-tracker/`
- Deployed from `main` branch via `.github/workflows/pages.yml`
- Static files only: `index.html`, `detail.html`, `insights.html`, `README.md`, `data/events.json`

**CI Pipeline:**
- GitHub Actions (`.github/workflows/pages.yml`)
- Trigger: push to `main` or manual `workflow_dispatch`
- No tests, linting, or build step in CI -- just copy and deploy

## Environment Configuration

**Required env vars:**
- `TAVILY_API_KEY` -- Tavily API key for search scripts (only needed on machine running search scripts)

**Secrets location:**
- Environment variables only (`.env` files are gitignored)
- No secrets manager or vault detected

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

---

*Integration audit: 2026-04-03*
