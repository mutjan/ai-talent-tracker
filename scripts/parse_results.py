#!/usr/bin/env python3
"""
Parse web search results and merge new AI talent movement events into events.json.
Can be called by the scheduled task or manually.

Usage:
  python3 parse_results.py <results_dir_or_file> <events_json_path>
  python3 parse_results.py --text "raw text to parse" <events_json_path>
"""

import json
import os
import re
import sys
import hashlib
from datetime import datetime
from pathlib import Path


# Major AI companies to track
AI_COMPANIES = [
    "OpenAI", "Anthropic", "Google DeepMind", "DeepMind", "xAI", "Meta AI", "Meta",
    "Mistral AI", "Mistral", "Cohere", "Stability AI", "Midjourney", "Perplexity",
    "Inflection", "Character AI", "Character.AI", "Databricks", "NVIDIA",
    "Apple", "Microsoft", "Amazon", "Google Brain", "Google AI",
    "百度", "Baidu", "字节跳动", "ByteDance", "商汤", "SenseTime",
    "智谱", "Zhipu", "月之暗面", "Moonshot", "MiniMax", "零一万物", "01.AI",
    "阶跃星辰", "StepFun", "百川智能", "Baichuan", "DeepSeek",
    "SSI", "Safe Superintelligence", "Adept AI", "Adept", "Cohere",
    "Hugging Face", "Scale AI", "Runway", "Pika", "Suno",
    "Together AI", "Anyscale", "Cerebras", "Groq", "SambaNova",
    "Thinking Machines Lab"
]

# Keywords indicating talent movements
JOIN_KEYWORDS = [
    "joined", "joining", "hired", "hiring", "appointed", "new role",
    "excited to join", "thrilled to join", "happy to announce",
    "started at", "new chapter", "moved to", "moving to",
    "加入", "入职", "任命", "就任", "担任"
]

LEAVE_KEYWORDS = [
    "left", "leaving", "departed", "departing", "stepped down", "stepping down",
    "resigned", "last day", "moving on", "no longer at", "exited",
    "离职", "离开", "辞职", "卸任", "退出"
]


def generate_event_id(person_name: str, company: str, event_type: str) -> str:
    """Generate a deterministic ID for deduplication."""
    key = f"{person_name.lower().strip()}|{company.lower().strip()}|{event_type.lower().strip()}"
    return "evt-" + hashlib.md5(key.encode()).hexdigest()[:8]


def extract_events_from_text(text: str) -> list:
    """
    Extract potential talent movement events from search result text.
    Returns a list of event dicts.
    """
    events = []

    # Split by search result blocks (marked by ## or ---)
    blocks = re.split(r'(?:^---$|^## )', text, flags=re.MULTILINE)

    for block in blocks:
        block = block.strip()
        if len(block) < 20:
            continue

        # Check if this block mentions any AI company
        mentioned_companies = []
        for company in AI_COMPANIES:
            if company.lower() in block.lower():
                mentioned_companies.append(company)

        if not mentioned_companies:
            continue

        # Check for talent movement keywords
        is_join = any(kw.lower() in block.lower() for kw in JOIN_KEYWORDS)
        is_leave = any(kw.lower() in block.lower() for kw in LEAVE_KEYWORDS)

        if not (is_join or is_leave):
            continue

        # Extract URL if present
        url_match = re.search(r'https?://[^\s\])"]+', block)
        source_url = url_match.group(0) if url_match else ""

        # Extract title (first line or **URL:** line)
        lines = block.split('\n')
        title = lines[0].strip().strip('#').strip() if lines else ""

        # Build a summary from the block
        summary = ' '.join(block.split()[:50])  # First 50 words
        if len(summary) > 300:
            summary = summary[:300] + "..."

        event_type = "leave" if is_leave else "join"

        event = {
            "id": "",  # Will be filled later
            "person_name": "",  # Needs manual review or LLM extraction
            "from_company": mentioned_companies[0] if is_leave and mentioned_companies else "",
            "to_company": mentioned_companies[0] if is_join and mentioned_companies else "",
            "role": "",
            "event_type": event_type,
            "source_url": source_url,
            "date_discovered": datetime.now().strftime("%Y-%m-%d"),
            "date_event": datetime.now().strftime("%Y-%m-%d"),
            "summary": summary,
            "_raw_title": title,
            "_raw_block": block[:500],
            "_mentioned_companies": mentioned_companies,
            "_needs_review": True
        }

        events.append(event)

    return events


def load_events(filepath: str) -> list:
    """Load existing events from JSON file."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_events(events: list, filepath: str):
    """Save events to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def get_existing_keys(events: list) -> set:
    """Get a set of dedup keys from existing events."""
    keys = set()
    for e in events:
        # Dedup by person + company + type
        person = e.get("person_name", "").lower().strip()
        company = (e.get("from_company", "") or e.get("to_company", "")).lower().strip()
        etype = e.get("event_type", "").lower().strip()
        if person and company:
            keys.add(f"{person}|{company}|{etype}")
        # Also dedup by source URL
        if e.get("source_url"):
            keys.add(e["source_url"])
    return keys


def merge_events(existing: list, new_events: list) -> tuple:
    """Merge new events into existing, skipping duplicates. Returns (merged, num_added)."""
    existing_keys = get_existing_keys(existing)
    added = 0

    for event in new_events:
        # Check URL dedup
        if event.get("source_url") and event["source_url"] in existing_keys:
            continue

        # Check person+company dedup
        person = event.get("person_name", "").lower().strip()
        company = (event.get("from_company", "") or event.get("to_company", "")).lower().strip()
        etype = event.get("event_type", "").lower().strip()

        if person and company:
            key = f"{person}|{company}|{etype}"
            if key in existing_keys:
                continue
            existing_keys.add(key)

        if event.get("source_url"):
            existing_keys.add(event["source_url"])

        # Generate ID
        if not event.get("id"):
            event["id"] = generate_event_id(
                event.get("person_name", "unknown"),
                company,
                etype
            )

        # Remove internal fields
        event.pop("_raw_title", None)
        event.pop("_raw_block", None)
        event.pop("_mentioned_companies", None)
        event.pop("_needs_review", None)

        existing.append(event)
        added += 1

    return existing, added


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 parse_results.py <results_dir_or_file> <events_json>")
        print("       python3 parse_results.py --text 'raw text' <events_json>")
        sys.exit(1)

    events_path = sys.argv[-1]

    # Load existing events
    existing_events = load_events(events_path)
    print(f"Loaded {len(existing_events)} existing events from {events_path}")

    # Collect raw text from sources
    raw_texts = []

    if sys.argv[1] == "--text":
        raw_texts.append(sys.argv[2])
    else:
        source = sys.argv[1]
        if os.path.isdir(source):
            for fname in sorted(os.listdir(source)):
                fpath = os.path.join(source, fname)
                if os.path.isfile(fpath):
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        raw_texts.append(f.read())
        elif os.path.isfile(source):
            with open(source, 'r', encoding='utf-8', errors='ignore') as f:
                raw_texts.append(f.read())
        else:
            print(f"Error: {source} is not a valid file or directory")
            sys.exit(1)

    # Extract events from all text
    all_new_events = []
    for text in raw_texts:
        events = extract_events_from_text(text)
        all_new_events.extend(events)

    print(f"Extracted {len(all_new_events)} potential events from search results")

    # Merge
    merged, num_added = merge_events(existing_events, all_new_events)

    # Sort by date (newest first)
    merged.sort(key=lambda e: e.get("date_event", ""), reverse=True)

    # Save
    save_events(merged, events_path)
    print(f"Added {num_added} new events. Total: {len(merged)} events.")
    print(f"Saved to {events_path}")


if __name__ == "__main__":
    main()
