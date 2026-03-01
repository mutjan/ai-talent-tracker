#!/usr/bin/env python3
"""
Exa Search wrapper for AI Talent Tracker.
Uses Exa API for high-quality web search with $10 free credit.
"""

import json
import sys
import os
from datetime import datetime, date
from pathlib import Path

EXA_API_KEY = "f5816694-9756-410a-bd47-3c38f770a02a"

# Usage tracking
usage_file = "/tmp/ai-talent-tracker/exa_usage.json"


def load_usage() -> dict:
    """Load usage data."""
    if os.path.exists(usage_file):
        with open(usage_file, 'r') as f:
            return json.load(f)
    return {"date": date.today().isoformat(), "count": 0}


def save_usage(usage: dict):
    """Save usage data."""
    os.makedirs(os.path.dirname(usage_file), exist_ok=True)
    with open(usage_file, 'w') as f:
        json.dump(usage, f, indent=2)


def increment_usage():
    """Increment usage counter."""
    usage = load_usage()
    today = date.today().isoformat()
    if usage.get("date") != today:
        usage = {"date": today, "count": 0}
    usage["count"] = usage.get("count", 0) + 1
    save_usage(usage)


def search_exa(query: str, num_results: int = 10, category: str = None,
               include_domains: list = None, exclude_domains: list = None) -> dict:
    """
    Search using Exa API.

    Args:
        query: Search query
        num_results: Number of results (default 10)
        category: Filter by category (news, tweet, people, company, research paper)
        include_domains: List of domains to include
        exclude_domains: List of domains to exclude
    """
    import urllib.request
    import urllib.error

    url = "https://api.exa.ai/search"

    payload = {
        "query": query,
        "type": "auto",
        "num_results": num_results,
        "contents": {
            "highlights": {
                "max_characters": 4000
            }
        }
    }

    if category:
        payload["category"] = category
    if include_domains:
        payload["includeDomains"] = include_domains
    if exclude_domains:
        payload["excludeDomains"] = exclude_domains

    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            increment_usage()
            return result

    except urllib.error.HTTPError as e:
        return {"error": f"HTTP Error {e.code}: {e.reason}", "results": []}
    except Exception as e:
        return {"error": f"Error: {str(e)}", "results": []}


def search_news(query: str, num_results: int = 10) -> dict:
    """Search news articles."""
    return search_exa(query, num_results, category="news")


def search_tweets(query: str, num_results: int = 10) -> dict:
    """Search tweets/X posts."""
    return search_exa(query, num_results, category="tweet")


def search_people(query: str, num_results: int = 10) -> dict:
    """Search for people."""
    return search_exa(query, num_results, category="people")


def search_companies(query: str, num_results: int = 10) -> dict:
    """Search for companies."""
    return search_exa(query, num_results, category="company")


def search_ai_talent(company: str = None, event_type: str = None) -> dict:
    """Specialized search for AI talent movements."""
    base_query = "AI executive hire departure joined left"

    if company:
        base_query += f" {company}"
    if event_type:
        if event_type == "join":
            base_query += " joined hired new role"
        elif event_type == "leave":
            base_query += " leaving departed resignation"

    # Use news category for talent movements
    return search_exa(base_query, num_results=15, category="news")


def batch_search(queries: list, num_results: int = 10) -> dict:
    """Execute multiple searches and combine results."""
    all_results = []

    for query in queries:
        result = search_exa(query, num_results)
        for item in result.get("results", []):
            # Deduplicate by URL
            if not any(r.get("url") == item.get("url") for r in all_results):
                all_results.append(item)

    return {
        "results": all_results,
        "total_queries": len(queries),
        "unique_results": len(all_results)
    }


def format_results(results: dict) -> str:
    """Format search results as markdown."""
    if "error" in results:
        return f"# Search Error\n\n{results['error']}"

    output = []
    output.append("# Search Results\n")
    output.append(f"**Results:** {len(results.get('results', []))}\n")
    output.append("---\n")

    for i, result in enumerate(results.get('results', []), 1):
        title = result.get('title', 'No title')
        url = result.get('url', '')

        # Get highlights or text content
        content = ""
        if 'highlights' in result and result['highlights']:
            content = result['highlights'][0] if isinstance(result['highlights'], list) else result['highlights']
        elif 'text' in result:
            content = result['text'][:500] + "..." if len(result['text']) > 500 else result['text']

        output.append(f"## {title}")
        output.append(f"")
        output.append(f"**URL:** [{url}]({url})")
        output.append(f"")
        output.append(f"{content}")
        output.append(f"")
        output.append("---")
        output.append(f"")

    return "\n".join(output)


def get_usage_status() -> dict:
    """Get current usage status."""
    usage = load_usage()
    return {
        "free_credit": "$10",
        "today_used": usage.get("count", 0),
        "date": usage.get("date")
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 exa_search.py <command> [args]")
        print("")
        print("Commands:")
        print('  search "query" [num_results]     - General search')
        print('  news "query" [num_results]       - News search')
        print('  tweets "query" [num_results]     - Tweet/X search')
        print('  people "query" [num_results]     - People search')
        print('  companies "query" [num_results]  - Company search')
        print('  talent [company] [event_type]    - AI talent search')
        print('  status                           - Show usage status')
        sys.exit(1)

    command = sys.argv[1]

    if command == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        num_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        result = search_exa(query, num_results)
        print(format_results(result))

    elif command == "news":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        num_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        result = search_news(query, num_results)
        print(format_results(result))

    elif command == "tweets":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        num_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        result = search_tweets(query, num_results)
        print(format_results(result))

    elif command == "people":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        num_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        result = search_people(query, num_results)
        print(format_results(result))

    elif command == "companies":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        num_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        result = search_companies(query, num_results)
        print(format_results(result))

    elif command == "talent":
        company = sys.argv[2] if len(sys.argv) > 2 else None
        event_type = sys.argv[3] if len(sys.argv) > 3 else None
        result = search_ai_talent(company, event_type)
        print(format_results(result))

    elif command == "status":
        status = get_usage_status()
        print(json.dumps(status, indent=2))

    else:
        # Default: search
        query = command
        num_results = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        result = search_exa(query, num_results)
        print(format_results(result))


if __name__ == "__main__":
    main()
