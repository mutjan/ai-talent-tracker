# Daily X/LinkedIn Search Strategy

## Objective

Find newly announced AI researcher departures, moves, and joins from X and LinkedIn every morning, update `data/events.json` only with high-confidence events, and push `main` so GitHub Pages deploys the new data.

## Success Criteria

- Search covers X and LinkedIn signals from the last 24-48 hours.
- New records match the existing `data/events.json` schema.
- Every inserted event has a concrete source URL and enough evidence for `person_name`, `event_type`, `date_event`, and at least one of `from_company` or `to_company`.
- Duplicate events are not added.
- Low-confidence or ambiguous items are saved as candidates instead of being published.
- Changes are committed and pushed to `origin/main`; the Pages workflow is triggered by the push.

## Decision Boundaries

Use three confidence levels:

- Publish: the source is first-party or otherwise explicit, names the person, and states a leave/join/move clearly.
- Candidate: the source is relevant but lacks one of the required fields, uses hearsay, or needs cross-checking.
- Reject: the item is recruiting content, generic company hiring news, non-AI roles, internship-only noise unless strategically notable, or already exists in the data.

For LinkedIn, prefer public posts, public profile updates, company announcements, or news pages surfaced by search. Do not rely on private-login-only pages as sole evidence.

For X, prefer posts from the person, destination company, former/current colleagues with direct context, or reputable reporters. Avoid quote-post speculation without a primary link.

## MECE Search Buckets

Run searches across these non-overlapping intent buckets:

- Leave signals: `left`, `leaving`, `last day`, `departure`, `resigned`, `stepping down`.
- Join signals: `joined`, `joining`, `starting`, `first day`, `thrilled to share`, `excited to share`.
- Move signals: `from X to Y`, `joins from`, `poached`, `hired`, `recruits`.
- Founder signals: `left to found`, `cofounding`, `launching`, `new AI lab`, `stealth startup`.
- Company-targeted signals: OpenAI, Anthropic, Google DeepMind, Meta, xAI, Microsoft AI, NVIDIA, Apple, Cohere, Mistral, DeepSeek, Qwen, Zhipu.

## Daily Workflow

1. Check repo state first:

   ```bash
   git status --short --branch
   git fetch origin main
   ```

2. Run configured Tavily search:

   ```bash
   python3 scripts/search.py --days 2 --output .temp/candidates_$(date +%Y%m%d).json
   ```

3. Review candidates against the confidence rules. For high-confidence items, add records to `data/events.json` using the existing schema:

   ```json
   {
     "id": "evt-xxxxxxxx",
     "person_name": "",
     "from_company": "",
     "to_company": "",
     "role": "",
     "event_type": "join|leave|move",
     "source_url": "",
     "date_discovered": "YYYY-MM-DD",
     "date_event": "YYYY-MM-DD",
     "summary": ""
   }
   ```

4. Run validation:

   ```bash
   python3 scripts/deduplicate.py
   python3 -m pytest
   git diff -- data/events.json scripts/search_config.json
   ```

5. Publish only if data changed and validation passed:

   ```bash
   git add data/events.json
   git commit -m "Add daily AI talent moves"
   git push origin main
   ```

6. Report:

   - Search result count
   - Candidate count
   - Published event count
   - Rejected/ambiguous count
   - Commit hash and whether push succeeded

## Failure Handling

- If `TAVILY_API_KEY` is missing, stop and report that search cannot run.
- If X/LinkedIn search is sparse, broaden to reputable tech/news domains but keep the same confidence rules.
- If the repo has unrelated dirty changes, do not overwrite them; either work around them or stop before publishing.
- If validation fails, do not push.
