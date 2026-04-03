#!/usr/bin/env python3
"""
去重脚本 - 检查并清理 events.json 中的重复事件
基于 person_name + from_company + to_company + date_event 进行去重
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def load_events(data_path: str = "data/events.json") -> list:
    """加载事件数据"""
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_events(events: list, data_path: str = "data/events.json"):
    """保存事件数据"""
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    print(f"已保存 {len(events)} 条事件到 {data_path}")


def find_duplicates(events: list) -> dict:
    """
    查找重复事件
    返回: {duplicate_key: [event_ids]}
    """
    seen = defaultdict(list)

    for event in events:
        # 使用关键字段组合作为去重键
        key_parts = [
            event.get('person_name', '').strip().lower(),
            event.get('from_company', '').strip().lower(),
            event.get('to_company', '').strip().lower(),
            event.get('date_event', '')
        ]

        # 如果 event_type 是 leave，to_company 可能为空，使用特殊标记
        if event.get('event_type') == 'leave' and not key_parts[2]:
            key_parts[2] = '(left)'

        dup_key = '|'.join(key_parts)
        seen[dup_key].append(event.get('id'))

    # 只保留有重复的记录
    duplicates = {k: v for k, v in seen.items() if len(v) > 1}
    return duplicates


def merge_duplicate_events(events: list, duplicates: dict) -> list:
    """
    合并重复事件，保留信息最完整的一条
    """
    ids_to_remove = set()

    for dup_key, event_ids in duplicates.items():
        # 获取所有重复的事件
        duplicate_events = [e for e in events if e.get('id') in event_ids]

        if len(duplicate_events) <= 1:
            continue

        # 选择信息最完整的事件作为主记录
        def completeness_score(event):
            score = 0
            if event.get('summary'): score += 1
            if event.get('source_url'): score += 1
            if event.get('role'): score += 1
            if event.get('tags') and len(event.get('tags', [])) > 0: score += 1
            return score

        # 按完整性排序，保留第一条
        duplicate_events.sort(key=completeness_score, reverse=True)
        keep_event = duplicate_events[0]

        # 合并其他事件的信息（如果有额外信息）
        for other in duplicate_events[1:]:
            # 如果其他事件有更长的 summary，合并进来
            if len(other.get('summary', '')) > len(keep_event.get('summary', '')):
                keep_event['summary'] = other['summary']

            # 添加缺失的 tags
            existing_tags = set(keep_event.get('tags', []))
            new_tags = set(other.get('tags', []))
            keep_event['tags'] = list(existing_tags | new_tags)

            # 标记为删除
            ids_to_remove.add(other.get('id'))

        print(f"合并重复事件: {keep_event.get('person_name')} - 保留了 ID: {keep_event.get('id')}")

    # 过滤掉需要删除的事件
    cleaned_events = [e for e in events if e.get('id') not in ids_to_remove]

    return cleaned_events


def main():
    """主函数"""
    data_path = Path(__file__).parent.parent / "data" / "events.json"

    print(f"加载数据: {data_path}")

    try:
        events = load_events(str(data_path))
        print(f"共加载 {len(events)} 条事件")
    except FileNotFoundError:
        print(f"错误: 找不到文件 {data_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败 - {e}")
        sys.exit(1)

    # 查找重复
    print("\n查找重复事件...")
    duplicates = find_duplicates(events)

    if not duplicates:
        print("未发现重复事件，数据已是最新状态。")
        return

    print(f"\n发现 {len(duplicates)} 组重复事件:")
    for dup_key, event_ids in duplicates.items():
        parts = dup_key.split('|')
        print(f"  - {parts[0]}: {len(event_ids)} 个重复条目")

    # 合并重复
    print("\n开始合并重复事件...")
    cleaned_events = merge_duplicate_events(events, duplicates)

    removed_count = len(events) - len(cleaned_events)
    print(f"\n合并完成: 删除了 {removed_count} 条重复记录")
    print(f"清理后共 {len(cleaned_events)} 条事件")

    # 保存
    save_events(cleaned_events, str(data_path))
    print("\n数据已保存。")


if __name__ == "__main__":
    main()
