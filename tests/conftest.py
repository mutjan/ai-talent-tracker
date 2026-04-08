"""共享 fixtures - 为所有搜索相关测试提供样本数据"""

import json
import os
import sys
import pytest
from pathlib import Path


# 将 scripts 目录加入 path
SCRIPTS_DIR = str(Path(__file__).parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


@pytest.fixture
def config_path():
    """返回默认配置文件路径"""
    return str(Path(__file__).parent.parent / "scripts" / "search_config.json")


@pytest.fixture
def sample_events():
    """返回样本事件数据"""
    return [
        {
            "id": "evt-001",
            "person_name": "John Doe",
            "event_type": "join",
            "date_event": "2026-04-01",
            "from_company": "OpenAI",
            "to_company": "Anthropic",
            "role": "Research Scientist",
            "source_url": "https://example.com/news1",
            "date_discovered": "2026-04-01",
            "summary": "John Doe joined Anthropic from OpenAI",
            "tags": ["AI", "research"],
        },
        {
            "id": "evt-002",
            "person_name": "Jane Smith",
            "event_type": "leave",
            "date_event": "2026-04-02",
            "from_company": "Google DeepMind",
            "to_company": "",
            "role": "VP of AI",
            "source_url": "https://example.com/news2",
            "date_discovered": "2026-04-02",
            "summary": "Jane Smith left Google DeepMind",
            "tags": ["AI", "leadership"],
        },
    ]


@pytest.fixture
def mock_tavily_response():
    """返回模拟的 Tavily API 响应"""
    return {
        "results": [
            {
                "title": "AI Researcher Joins Anthropic",
                "url": "https://example.com/article1",
                "content": "A leading AI researcher has joined Anthropic from OpenAI.",
                "score": 0.95,
                "published_date": "2026-04-01",
            },
            {
                "title": "VP Leaves Google for Startup",
                "url": "https://example.com/article2",
                "content": "A vice president of AI has left Google to join a new startup.",
                "score": 0.88,
                "published_date": "2026-04-02",
            },
        ]
    }


@pytest.fixture
def tmp_config(tmp_path):
    """创建临时配置文件用于测试"""
    config = {
        "queries": {
            "english_broad": ["AI researcher joins leaves OpenAI"],
            "english_specific": ["VP AI leaves joins"],
            "chinese_broad": [],
            "chinese_specific": [],
        },
        "domain_groups": {
            "english_tech": {"enabled": True, "domains": ["techcrunch.com"]},
            "chinese_tech": {"enabled": False, "domains": []},
            "social": {"enabled": False, "domains": []},
        },
        "search_params": {
            "search_depth": "advanced",
            "max_results": 10,
        },
    }
    config_file = tmp_path / "test_config.json"
    config_file.write_text(json.dumps(config, ensure_ascii=False))
    return str(config_file)
