#!/usr/bin/env python3
"""
Tavily MCP Search wrapper for AI Talent Tracker.
Uses Tavily MCP server for high-quality search results.
Includes usage tracking and fallback to web-search when quota exceeded.
"""

import json
import sys
import os
from datetime import datetime, date
from pathlib import Path

TAVILY_API_KEY = "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"
MCP_URL = f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"

# Monthly quota limit
MONTHLY_QUOTA = 1000
DAILY_LIMIT = 30  # Max 30 searches per day


def get_usage_file() -> str:
    """Get path to usage tracking file."""
    return "/tmp/ai-talent-tracker/tavily_usage.json"


def load_usage() -> dict:
    """Load current month's usage data."""
    usage_file = get_usage_file()
    if os.path.exists(usage_file):
        with open(usage_file, 'r') as f:
            return json.load(f)
    return {"month": date.today().strftime("%Y-%m"), "count": 0, "daily": {}}


def save_usage(usage: dict):
    """Save usage data."""
    usage_file = get_usage_file()
    os.makedirs(os.path.dirname(usage_file), exist_ok=True)
    with open(usage_file, 'w') as f:
        json.dump(usage, f, indent=2)


def check_quota() -> tuple:
    """
    Check if quota is available.
    Returns: (can_use_tavily: bool, remaining: int, reason: str)
    """
    usage = load_usage()
    today = date.today().strftime("%Y-%m-%d")
    current_month = date.today().strftime("%Y-%m")

    # Reset if new month
    if usage.get("month") != current_month:
        usage = {"month": current_month, "count": 0, "daily": {}}
        save_usage(usage)

    # Check monthly quota
    if usage.get("count", 0) >= MONTHLY_QUOTA:
        return False, 0, f"Monthly quota exceeded ({MONTHLY_QUOTA})"

    # Check daily limit
    daily_count = usage.get("daily", {}).get(today, 0)
    if daily_count >= DAILY_LIMIT:
        return False, 0, f"Daily limit exceeded ({DAILY_LIMIT})"

    remaining = min(MONTHLY_QUOTA - usage["count"], DAILY_LIMIT - daily_count)
    return True, remaining, "OK"


def increment_usage():
    """Increment usage counter."""
    usage = load_usage()
    today = date.today().strftime("%Y-%m-%d")
    current_month = date.today().strftime("%Y-%m")

    if usage.get("month") != current_month:
        usage = {"month": current_month, "count": 0, "daily": {}}

    usage["count"] = usage.get("count", 0) + 1
    if "daily" not in usage:
        usage["daily"] = {}
    usage["daily"][today] = usage["daily"].get(today, 0) + 1

    save_usage(usage)


def search_tavily(query: str, max_results: int = 10, include_domains: list = None, exclude_domains: list = None) -> dict:
    """
    Search using Tavily MCP server via HTTP API.
    """
    import urllib.request
    import urllib.error

    # Check quota first
    can_use, remaining, reason = check_quota()
    if not can_use:
        return {
            "error": f"Tavily quota exceeded: {reason}. Use fallback search.",
            "quota_exceeded": True,
            "results": []
        }

    url = "https://api.tavily.com/search"

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",  # Use basic to save quota
        "include_answer": False,   # Disable to save quota
        "include_raw_content": False
    }

    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains

    headers = {"Content-Type": "application/json"}

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            increment_usage()  # Count successful request
            return result

    except urllib.error.HTTPError as e:
        if e.code == 429:
            return {"error": "Rate limit exceeded", "quota_exceeded": True, "results": []}
        return {"error": f"HTTP Error {e.code}: {e.reason}", "results": []}
    except urllib.error.URLError as e:
        return {"error": f"URL Error: {e.reason}", "results": []}
    except Exception as e:
        return {"error": f"Error: {str(e)}", "results": []}


def search_fallback(query: str, max_results: int = 10) -> dict:
    """
    Fallback search using web-search skill when Tavily quota exceeded.
    """
    import subprocess

    skills_root = os.environ.get("SKILLS_ROOT", "/Users/lzw/Library/Application Support/LobsterAI/SKILLs")
    search_script = f"{skills_root}/web-search/scripts/search.sh"

    try:
        result = subprocess.run(
            ["bash", search_script, query, str(max_results)],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Parse markdown output to structured format
        output = result.stdout

        # Simple parsing - extract results
        results = []
        lines = output.split('\n')
        current_result = {}

        for line in lines:
            line = line.strip()
            if line.startswith('## '):
                if current_result and 'title' in current_result:
                    results.append(current_result)
                current_result = {"title": line[3:], "url": "", "content": "", "score": 0.5}
            elif line.startswith('**URL:**'):
                url_start = line.find('[')
                url_end = line.find(']')
                if url_start > 0 and url_end > url_start:
                    current_result["url"] = line[url_start+1:url_end]
            elif line and not line.startswith('*') and not line.startswith('---'):
                if 'content' in current_result:
                    current_result["content"] += line + " "

        if current_result and 'title' in current_result:
            results.append(current_result)

        return {
            "results": results[:max_results],
            "fallback": True,
            "source": "web-search"
        }

    except Exception as e:
        return {"error": f"Fallback search failed: {str(e)}", "results": []}


def smart_search(query: str, max_results: int = 10, use_fallback_on_quota: bool = True) -> dict:
    """
    Smart search: Try Tavily first, fallback to web-search if quota exceeded.
    """
    # Check quota status
    can_use, remaining, _ = check_quota()

    if can_use:
        result = search_tavily(query, max_results)
        if not result.get("quota_exceeded") and not result.get("error"):
            return result

    # Use fallback if allowed
    if use_fallback_on_quota:
        print(f"[Tavily quota exceeded or error, using fallback search...]", file=sys.stderr)
        return search_fallback(query, max_results)

    return {"error": "Tavily quota exceeded and fallback disabled", "results": []}


def batch_search(queries: list, max_results: int = 10) -> dict:
    """
    Execute multiple searches efficiently, tracking quota.
    Returns combined results.
    """
    all_results = []
    used_fallback = False

    for query in queries:
        result = smart_search(query, max_results, use_fallback_on_quota=True)

        if result.get("fallback"):
            used_fallback = True

        for item in result.get("results", []):
            # Deduplicate by URL
            if not any(r.get("url") == item.get("url") for r in all_results):
                all_results.append(item)

    return {
        "results": all_results,
        "fallback_used": used_fallback,
        "total_queries": len(queries),
        "unique_results": len(all_results)
    }


def search_ai_talent_batch(companies: list = None, event_types: list = None) -> dict:
    """
    Optimized batch search for AI talent movements.
    Uses combined company + action keyword queries for maximum coverage with minimal quota usage.
    Covers both "leaving from" and "joining to" perspectives.
    """
    queries = []

    # Strategy 1: International companies - Combined query with action keywords (高效覆盖)
    # 格式: (公司1 OR 公司2 OR ...) AND (动作1 OR 动作2 OR ...) + 时间
    intl_companies = ['"OpenAI"', '"Anthropic"', '"Google DeepMind"', '"xAI"', '"Meta AI"',
                      '"Mistral"', '"Cohere"', '"Stability AI"']
    intl_str = " OR ".join(intl_companies)
    action_keywords = "join OR leave OR \"step down\" OR departure OR resign OR hired OR appointed OR leaving OR departed"
    queries.append(f"({intl_str}) {action_keywords} 2025 2026")

    # Strategy 2: International - Cross-company movements (谁加入了X)
    queries.append(f"joined ({intl_str}) from 2025 2026")

    # Strategy 3: Chinese companies - Combined query
    cn_companies = ['"字节跳动"', '"ByteDance"', '"阿里巴巴"', '"Alibaba"', '"百度"', '"Baidu"',
                    '"腾讯"', '"Tencent"', '"月之暗面"', '"Moonshot"', '"智谱"', '"Zhipu"',
                    '"百川"', '"Baichuan"', '"DeepSeek"', '"MiniMax"', '"阶跃星辰"', '"StepFun"']
    cn_str = " OR ".join(cn_companies)
    cn_actions = "离职 OR 入职 OR 加入 OR 离开 OR 高管 OR 负责人"
    queries.append(f"({cn_str}) {cn_actions} 2025 2026")

    # Strategy 4: Specific high-value cross-company patterns (if quota allows)
    can_use, remaining, _ = check_quota()
    if remaining > 10:
        queries.append(f"joined OpenAI from Google OR Meta OR DeepMind researcher 2025")
        queries.append(f"joined Anthropic from OpenAI OR Google researcher 2025")
        queries.append(f"joined DeepMind from OpenAI OR Meta OR xAI researcher 2025")
    if remaining > 15:
        queries.append(f"昆仑万维 OR 面壁智能 OR 商汤科技 AI高管 离职 加入 2025 2026")

    return batch_search(queries, max_results=15)


def search_unknown_destinations(people: list) -> dict:
    """
    Search for unknown destinations of departed employees.
    Optimized to use minimal queries.
    """
    if not people:
        return {"results": []}

    # Batch people into combined queries (max 3 people per query)
    queries = []
    for i in range(0, len(people), 3):
        batch = people[i:i+3]
        names = " OR ".join([f'"{p}"' for p in batch])
        queries.append(f"({names}) new role joined startup founded company 2025 2026")

    return batch_search(queries, max_results=8)


def get_usage_status() -> dict:
    """Get current usage status for reporting."""
    usage = load_usage()
    today = date.today().strftime("%Y-%m-%d")
    monthly_used = usage.get("count", 0)
    daily_used = usage.get("daily", {}).get(today, 0)

    return {
        "monthly_quota": MONTHLY_QUOTA,
        "monthly_used": monthly_used,
        "monthly_remaining": MONTHLY_QUOTA - monthly_used,
        "daily_limit": DAILY_LIMIT,
        "daily_used": daily_used,
        "daily_remaining": DAILY_LIMIT - daily_used,
        "month": usage.get("month")
    }


def format_results(results: dict) -> str:
    """Format search results as markdown."""
    if "error" in results and not results.get("results"):
        return f"# Search Error\n\n{results['error']}"

    output = []
    output.append("# Search Results\n")

    if results.get("fallback_used"):
        output.append("*Using fallback search (Tavily quota exceeded)*\n")

    if "answer" in results and results["answer"]:
        output.append(f"**AI Summary:** {results['answer']}\n")

    output.append(f"**Results:** {len(results.get('results', []))}\n")
    output.append("---\n")

    for i, result in enumerate(results.get('results', []), 1):
        title = result.get('title', 'No title')
        url = result.get('url', '')
        content = result.get('content', 'No content')
        score = result.get('score', 0)

        output.append(f"## {title}")
        output.append(f"")
        output.append(f"**URL:** [{url}]({url})")
        output.append(f"")
        output.append(f"{content}")
        output.append(f"")
        output.append(f"*Relevance: {score:.2f}*")
        output.append(f"")
        output.append("---")
        output.append(f"")

    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tavily_search.py <command> [args]")
        print("")
        print("Commands:")
        print('  search "query" [max_results]     - Single search')
        print('  batch "query1" "query2" ...      - Batch search')
        print('  talent                           - AI talent batch search')
        print('  destinations "name1" "name2"...  - Search unknown destinations')
        print('  status                           - Show usage status')
        print('  quota                            - Check quota')
        sys.exit(1)

    command = sys.argv[1]

    if command == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        result = smart_search(query, max_results)
        print(format_results(result))

    elif command == "batch":
        queries = sys.argv[2:]
        result = batch_search(queries, max_results=10)
        print(format_results(result))

    elif command == "talent":
        result = search_ai_talent_batch()
        print(format_results(result))

    elif command == "destinations":
        people = sys.argv[2:]
        result = search_unknown_destinations(people)
        print(format_results(result))

    elif command == "status":
        status = get_usage_status()
        print(json.dumps(status, indent=2))

    elif command == "quota":
        can_use, remaining, reason = check_quota()
        print(f"Can use Tavily: {can_use}")
        print(f"Remaining today: {remaining}")
        print(f"Reason: {reason}")

    else:
        # Default: single search
        query = command
        max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        result = smart_search(query, max_results)
        print(format_results(result))


if __name__ == "__main__":
    main()
