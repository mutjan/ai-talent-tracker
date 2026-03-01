#!/usr/bin/env python3
"""
Tavily MCP Search wrapper for AI Talent Tracker.
Uses Tavily MCP server for high-quality search results.
"""

import json
import sys
import os
import subprocess
from datetime import datetime

TAVILY_API_KEY = "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"
MCP_URL = f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"


def search_tavily(query: str, max_results: int = 10, include_domains: list = None, exclude_domains: list = None) -> dict:
    """
    Search using Tavily MCP server via HTTP API.

    Args:
        query: Search query string
        max_results: Maximum number of results (default 10)
        include_domains: List of domains to include (e.g., ["x.com", "twitter.com"])
        exclude_domains: List of domains to exclude

    Returns:
        dict: Search results with 'results' key containing list of result objects
    """
    import urllib.request
    import urllib.error

    url = "https://api.tavily.com/search"

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "include_answer": True,
        "include_raw_content": False
    }

    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains

    headers = {
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
            return result

    except urllib.error.HTTPError as e:
        return {"error": f"HTTP Error {e.code}: {e.reason}", "results": []}
    except urllib.error.URLError as e:
        return {"error": f"URL Error: {e.reason}", "results": []}
    except Exception as e:
        return {"error": f"Error: {str(e)}", "results": []}


def search_x_twitter(query: str, max_results: int = 10) -> dict:
    """
    Search specifically on X/Twitter using Tavily.

    Args:
        query: Search query (will be appended with site:x.com)
        max_results: Maximum results

    Returns:
        dict: Search results
    """
    # Ensure query targets X/Twitter
    if "site:x.com" not in query and "site:twitter.com" not in query:
        query = f"site:x.com {query}"

    return search_tavily(query, max_results, include_domains=["x.com", "twitter.com"])


def search_ai_talent(company: str = None, event_type: str = None, days: int = 30) -> dict:
    """
    Specialized search for AI talent movements.

    Args:
        company: Company name (e.g., "OpenAI", "Anthropic")
        event_type: "join", "leave", or None for both
        days: Number of days back to search

    Returns:
        dict: Search results
    """
    base_query = "AI executive hire departure joined left leaving"

    if company:
        base_query += f" {company}"

    if event_type == "join":
        base_query += " joined hired new role"
    elif event_type == "leave":
        base_query += " leaving left departed departure"

    # Add time constraint to query
    year = datetime.now().year
    base_query += f" {year}"

    return search_tavily(base_query, max_results=15)


def format_results(results: dict) -> str:
    """Format search results as markdown."""
    if "error" in results:
        return f"# Search Error\n\n{results['error']}"

    output = []
    output.append(f"# Search Results\n")

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
        print("Usage: python3 tavily_search.py <query> [max_results] [x_only]")
        print("       python3 tavily_search.py x <query> [max_results]")
        print("")
        print("Examples:")
        print('  python3 tavily_search.py "OpenAI executive departure 2025" 10')
        print('  python3 tavily_search.py x "Mira Murati new role" 5')
        print('  python3 tavily_search.py talent OpenAI leave')
        sys.exit(1)

    # Check for special modes
    if sys.argv[1] == "x":
        # X/Twitter search mode
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        results = search_x_twitter(query, max_results)

    elif sys.argv[1] == "talent":
        # AI talent search mode
        company = sys.argv[2] if len(sys.argv) > 2 else None
        event_type = sys.argv[3] if len(sys.argv) > 3 else None
        results = search_ai_talent(company, event_type)

    else:
        # Regular search
        query = sys.argv[1]
        max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        x_only = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False

        if x_only:
            results = search_x_twitter(query, max_results)
        else:
            results = search_tavily(query, max_results)

    # Output formatted results
    print(format_results(results))

    # Also save raw results to file for processing
    output_dir = "/tmp/ai-talent-tracker"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{output_dir}/tavily_search_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n\n[Raw results saved to: {output_file}]")


if __name__ == "__main__":
    main()
