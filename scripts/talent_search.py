#!/usr/bin/env python3
"""
人才搜索脚本 - 使用 Tavily API 搜索AI人才新闻
"""

import os
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 需要安装: pip install tavily-python
from tavily import TavilyClient


def load_events(data_path: str = "data/events.json") -> list:
    """加载已有事件数据"""
    path = Path(data_path)
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_events(events: list, data_path: str = "data/events.json"):
    """保存事件数据"""
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def search_talent_news(client: TavilyClient, days: int = 1) -> list:
    """
    搜索AI人才相关新闻
    """
    date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    queries = [
        "AI talent move joins leaves OpenAI Google DeepMind Anthropic Meta",
        "AI researcher joins leaves startup",
        "chief scientist VP AI leaves joins",
        "top AI engineer joins new company"
    ]

    all_results = []

    for query in queries:
        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                include_domains=[
                    "techcrunch.com",
                    "theinformation.com",
                    "bloomberg.com",
                    "reuters.com",
                    "businessinsider.com",
                    "venturebeat.com",
                    "x.com",
                    "linkedin.com",
                    "subsight.com"
                ],
                max_results=10
            )

            for result in response.get('results', []):
                result['_query'] = query
                result['_search_date'] = datetime.now().isoformat()
                all_results.append(result)

        except Exception as e:
            print(f"搜索失败 '{query}': {e}")
            continue

    # 去重
    seen_urls = set()
    unique_results = []
    for r in all_results:
        url = r.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)

    return unique_results


def analyze_for_events(results: list) -> list:
    """
    分析搜索结果，提取可能的人才事件
    这是一个简化版本，实际应该用LLM分析
    """
    events = []

    for result in results:
        title = result.get('title', '')
        content = result.get('content', '')
        url = result.get('url', '')

        # 简单关键词匹配（实际应该用LLM）
        # 这里只返回候选，需要人工审核
        event = {
            '_candidate': True,
            '_source_title': title,
            '_source_content': content[:500],
            '_source_url': url,
            'person_name': '',  # 需要人工填写
            'event_type': 'move',  # join/leave/move
            'from_company': '',
            'to_company': '',
            'role': '',
            'source_url': url,
            'date_discovered': datetime.now().strftime('%Y-%m-%d'),
            'date_event': '',
            'summary': content[:200],
            'tags': []
        }

        events.append(event)

    return events


def main():
    """主函数"""
    # 获取API key
    api_key = os.environ.get('TAVILY_API_KEY')
    if not api_key:
        print("错误: 请设置 TAVILY_API_KEY 环境变量")
        print("示例: export TAVILY_API_KEY='your-key-here'")
        sys.exit(1)

    client = TavilyClient(api_key=api_key)

    # 搜索新闻
    print("开始搜索AI人才新闻...")
    results = search_talent_news(client, days=1)
    print(f"找到 {len(results)} 条相关新闻")

    if not results:
        print("没有发现新的人才动态")
        return

    # 分析为候选事件
    print("\n分析新闻内容...")
    candidate_events = analyze_for_events(results)

    # 保存候选事件到临时文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f".temp/candidates_{timestamp}.json"
    Path(".temp").mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(candidate_events, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 找到 {len(candidate_events)} 个候选事件")
    print(f"已保存到: {output_file}")
    print("\n请查看候选事件文件，人工确认后添加到 data/events.json")
    print("\n提示：运行 deduplicate.py 可在添加后去重")


if __name__ == "__main__":
    main()
