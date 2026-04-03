#!/usr/bin/env python3
"""
Tavily新闻搜索脚本 - 使用 Tavily API 搜索AI相关新闻
主要用于日常自动更新，搜索AI人才动态新闻
"""

import os
import json
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path

# 需要安装: pip install tavily-python
from tavily import TavilyClient


def load_existing_events(data_path: str = "data/events.json") -> list:
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


def generate_event_id() -> str:
    """生成唯一事件ID"""
    import uuid
    return f"evt-{uuid.uuid4().hex[:8]}"


def is_duplicate(new_event: dict, existing_events: list) -> bool:
    """检查是否重复事件"""
    person = new_event.get('person_name', '').lower().strip()
    from_co = new_event.get('from_company', '').lower().strip()
    to_co = new_event.get('to_company', '').lower().strip()
    date = new_event.get('date_event', '')

    for existing in existing_events:
        if (existing.get('person_name', '').lower().strip() == person and
            existing.get('from_company', '').lower().strip() == from_co and
            existing.get('to_company', '').lower().strip() == to_co and
            existing.get('date_event', '') == date):
            return True

    return False


def parse_date_from_text(text: str) -> str:
    """从文本中解析日期"""
    # 尝试匹配 YYYY-MM-DD 格式
    pattern = r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b'
    match = re.search(pattern, text)
    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    # 尝试匹配 "today", "yesterday", "last week" 等相对时间
    today = datetime.now()

    if re.search(r'\btoday\b|\bjust announced\b|\bannounced today\b', text, re.I):
        return today.strftime('%Y-%m-%d')

    if re.search(r'\byesterday\b', text, re.I):
        return (today - timedelta(days=1)).strftime('%Y-%m-%d')

    return today.strftime('%Y-%m-%d')


def extract_person_and_companies(text: str, title: str) -> dict:
    """
    从文本中提取人物和公司信息
    简化版本 - 返回候选信息供人工审核
    """
    # 常见AI公司列表
    companies = [
        'OpenAI', 'Anthropic', 'DeepMind', 'Google', 'Google DeepMind',
        'Meta', 'Facebook', 'Microsoft', 'Amazon', 'Apple', 'Tesla',
        'xAI', 'Cohere', 'Adept', 'Character.AI', 'Inflection', 'Midjourney',
        'Stability AI', 'Hugging Face', 'Runway', 'ElevenLabs',
        'DeepSeek', 'Moonshot AI', '智谱AI', '百川智能', '零一万物',
        '商汤科技', '科大讯飞', '百度', '阿里巴巴', '腾讯'
    ]

    # 尝试识别提到的公司
    mentioned_companies = []
    text_upper = text.upper()
    for company in companies:
        if company.upper() in text_upper:
            mentioned_companies.append(company)

    return {
        'mentioned_companies': mentioned_companies,
        'needs_manual_review': True
    }


def search_news_with_tavily(client: TavilyClient, days_back: int = 1) -> list:
    """使用Tavily搜索新闻"""

    # 计算搜索日期范围
    today = datetime.now()
    date_from = (today - timedelta(days=days_back)).strftime('%Y-%m-%d')

    # 构建搜索查询
    queries = [
        "AI researcher joins leaves OpenAI Google DeepMind Anthropic",
        "AI talent move chief scientist leaves joins startup",
        "top AI engineer researcher joins new company",
        "AI lab researcher departure hiring",
        "vice president AI leaves joins",
        "co-founder AI startup leaves"
    ]

    all_results = []

    for query in queries:
        try:
            print(f"搜索: {query}")
            response = client.search(
                query=query,
                search_depth="advanced",
                time_range="day",  # 最近24小时
                include_answer=False,
                max_results=10
            )

            results = response.get('results', [])
            print(f"  找到 {len(results)} 条结果")

            for result in results:
                result['_search_query'] = query
                result['_search_time'] = today.isoformat()
                all_results.append(result)

        except Exception as e:
            print(f"搜索失败: {e}")
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


def convert_to_event_format(search_result: dict, existing_events: list) -> dict:
    """
    将搜索结果转换为事件格式
    返回候选事件（需要人工审核）
    """
    title = search_result.get('title', '')
    content = search_result.get('content', '')
    url = search_result.get('url', '')

    # 提取信息
    date = parse_date_from_text(f"{title} {content}")
    extracted = extract_person_and_companies(content, title)

    event = {
        'id': generate_event_id(),
        'person_name': '',  # 需要人工填写
        'event_type': 'move',  # 默认，需要人工确认
        'from_company': '',
        'to_company': '',
        'role': '',
        'source_url': url,
        'date_discovered': datetime.now().strftime('%Y-%m-%d'),
        'date_event': date,
        'summary': content[:300] + '...' if len(content) > 300 else content,
        'tags': [],
        # 人工审核标记
        '_needs_review': True,
        '_source_title': title,
        '_mentioned_companies': extracted.get('mentioned_companies', [])
    }

    # 检查是否重复
    if is_duplicate(event, existing_events):
        event['_is_duplicate'] = True

    return event


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Tavily AI人才新闻搜索')
    parser.add_argument('--days', type=int, default=1, help='搜索最近几天的内容')
    parser.add_argument('--output', type=str, default='.temp/candidates_tavily.json', help='输出文件')
    parser.add_argument('--auto-merge', action='store_true', help='自动合并到events.json（需要人工审核后）')

    args = parser.parse_args()

    # 检查API key
    api_key = os.environ.get('TAVILY_API_KEY')
    if not api_key:
        print("错误: 请设置 TAVILY_API_KEY 环境变量")
        print("示例: export TAVILY_API_KEY='your-key-here'")
        sys.exit(1)

    client = TavilyClient(api_key=api_key)

    # 加载已有事件
    data_path = Path(__file__).parent.parent / "data" / "events.json"
    existing_events = load_events(str(data_path))
    print(f"已加载 {len(existing_events)} 条现有事件")

    # 搜索新闻
    print(f"\n搜索最近 {args.days} 天的AI人才新闻...")
    results = search_news_with_tavily(client, args.days)
    print(f"共找到 {len(results)} 条独特新闻")

    if not results:
        print("没有发现新闻")
        return

    # 转换为事件格式
    print("\n转换为事件格式...")
    candidate_events = []
    for result in results:
        event = convert_to_event_format(result, existing_events)
        if not event.get('_is_duplicate'):
            candidate_events.append(event)

    print(f"生成 {len(candidate_events)} 个候选事件（已过滤重复）")

    # 保存候选事件
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(candidate_events, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 候选事件已保存到: {output_path}")
    print(f"\n请查看文件并人工确认后，再添加到 data/events.json")

    # 统计信息
    duplicates = sum(1 for r in results if convert_to_event_format(r, existing_events).get('_is_duplicate'))
    print(f"\n统计:")
    print(f"  - 搜索到新闻: {len(results)}")
    print(f"  - 重复事件: {duplicates}")
    print(f"  - 候选事件: {len(candidate_events)}")


if __name__ == "__main__":
    main()
