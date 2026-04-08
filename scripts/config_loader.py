#!/usr/bin/env python3
"""
搜索配置加载器 - 从外部 JSON 文件加载搜索配置
支持配置验证、默认值合并和域名组过滤
"""

import json
from pathlib import Path


DEFAULT_CONFIG = {
    "queries": {
        "english_broad": [],
        "english_specific": [],
        "chinese_broad": [],
        "chinese_specific": [],
    },
    "domain_groups": {
        "english_tech": {"enabled": True, "domains": []},
        "chinese_tech": {"enabled": False, "domains": []},
        "social": {"enabled": False, "domains": []},
    },
    "search_params": {
        "search_depth": "advanced",
        "max_results": 10,
    },
}


def load_config(config_path: str = None) -> dict:
    """
    从 JSON 文件加载搜索配置，合并默认值

    Args:
        config_path: 配置文件路径，默认为 scripts/search_config.json

    Returns:
        完整的搜索配置字典

    Raises:
        FileNotFoundError: 配置文件不存在
        json.JSONDecodeError: 配置文件 JSON 格式错误
        ValueError: 配置验证失败
    """
    if config_path is None:
        config_path = str(Path(__file__).parent / "search_config.json")

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(path, 'r', encoding='utf-8') as f:
        user_config = json.load(f)

    config = _merge_defaults(DEFAULT_CONFIG, user_config)
    _validate_config(config)

    return config


def get_enabled_domains(config: dict) -> list:
    """
    从配置中获取所有已启用的域名组域名

    Args:
        config: 搜索配置字典

    Returns:
        已启用域名组的域名列表
    """
    enabled_domains = []
    for group_name, group_config in config.get("domain_groups", {}).items():
        if group_config.get("enabled", False):
            enabled_domains.extend(group_config.get("domains", []))
    return enabled_domains


def get_all_queries(config: dict) -> list:
    """
    从配置中获取所有非空查询

    Args:
        config: 搜索配置字典

    Returns:
        包含 (group_name, query) 元组的列表
    """
    all_queries = []
    for group_name, queries in config.get("queries", {}).items():
        if queries:
            for query in queries:
                all_queries.append((group_name, query))
    return all_queries


def get_search_params(config: dict) -> dict:
    """
    获取搜索参数

    Args:
        config: 搜索配置字典

    Returns:
        搜索参数字典
    """
    return config.get("search_params", DEFAULT_CONFIG["search_params"])


def _merge_defaults(defaults: dict, user: dict) -> dict:
    """递归合并用户配置到默认配置"""
    result = dict(defaults)
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_defaults(result[key], value)
        else:
            result[key] = value
    return result


def _validate_config(config: dict):
    """验证配置结构完整性"""
    # 验证 queries
    if "queries" not in config:
        raise ValueError("配置缺少 'queries' 字段")

    expected_query_groups = {"english_broad", "english_specific", "chinese_broad", "chinese_specific"}
    actual_query_groups = set(config["queries"].keys())
    missing_groups = expected_query_groups - actual_query_groups
    if missing_groups:
        raise ValueError(f"配置缺少查询组: {missing_groups}")

    for group_name, queries in config["queries"].items():
        if not isinstance(queries, list):
            raise ValueError(f"查询组 '{group_name}' 必须是列表")
        for i, query in enumerate(queries):
            if not isinstance(query, str) or not query.strip():
                raise ValueError(f"查询组 '{group_name}' 第 {i} 个查询不能为空")

    # 验证 domain_groups
    if "domain_groups" not in config:
        raise ValueError("配置缺少 'domain_groups' 字段")

    expected_domain_groups = {"english_tech", "chinese_tech", "social"}
    actual_domain_groups = set(config["domain_groups"].keys())
    missing_domain_groups = expected_domain_groups - actual_domain_groups
    if missing_domain_groups:
        raise ValueError(f"配置缺少域名组: {missing_domain_groups}")

    for group_name, group_config in config["domain_groups"].items():
        if not isinstance(group_config, dict):
            raise ValueError(f"域名组 '{group_name}' 必须是字典")
        if "enabled" not in group_config:
            raise ValueError(f"域名组 '{group_name}' 缺少 'enabled' 字段")
        if "domains" not in group_config:
            raise ValueError(f"域名组 '{group_name}' 缺少 'domains' 字段")
        if not isinstance(group_config["domains"], list):
            raise ValueError(f"域名组 '{group_name}' 的 'domains' 必须是列表")

    # 验证 search_params
    if "search_params" not in config:
        raise ValueError("配置缺少 'search_params' 字段")
