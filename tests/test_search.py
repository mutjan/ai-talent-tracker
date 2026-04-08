"""搜索配置测试 - CONS-02 和 CONS-03 验证"""

import json
import pytest
from pathlib import Path
from config_loader import (
    DEFAULT_CONFIG,
    load_config,
    get_enabled_domains,
    get_all_queries,
    get_search_params,
    _merge_defaults,
    _validate_config,
)


class TestQueryConfigStructure:
    """CONS-02: 搜索查询定义外部化为配置"""

    def test_query_config_structure(self, config_path):
        """配置文件包含正确的查询组结构"""
        config = load_config(config_path)

        assert "queries" in config
        assert "english_broad" in config["queries"]
        assert "english_specific" in config["queries"]
        assert "chinese_broad" in config["queries"]
        assert "chinese_specific" in config["queries"]

    def test_queries_are_strings(self, config_path):
        """所有查询都是非空字符串"""
        config = load_config(config_path)

        for group_name, queries in config["queries"].items():
            for query in queries:
                assert isinstance(query, str), f"查询组 '{group_name}' 中的查询不是字符串"
                assert query.strip(), f"查询组 '{group_name}' 中有空查询"

    def test_english_queries_populated(self, config_path):
        """英文查询组有实际内容"""
        config = load_config(config_path)

        assert len(config["queries"]["english_broad"]) > 0
        assert len(config["queries"]["english_specific"]) > 0

    def test_chinese_queries_placeholder(self, config_path):
        """中文查询组存在但为空（Phase 3 预留）"""
        config = load_config(config_path)

        assert config["queries"]["chinese_broad"] == []
        assert config["queries"]["chinese_specific"] == []

    def test_get_all_queries_returns_tuples(self, config_path):
        """get_all_queries 返回 (group_name, query) 元组"""
        config = load_config(config_path)
        queries = get_all_queries(config)

        assert len(queries) > 0
        for item in queries:
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], str)

    def test_get_all_queries_excludes_empty_groups(self, config_path):
        """空查询组不出现在结果中"""
        config = load_config(config_path)
        queries = get_all_queries(config)

        group_names = [q[0] for q in queries]
        assert "chinese_broad" not in group_names
        assert "chinese_specific" not in group_names

    def test_load_config_missing_file_raises(self):
        """加载不存在的配置文件抛出 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.json")

    def test_load_config_invalid_json_raises(self, tmp_path):
        """加载无效 JSON 抛出 json.JSONDecodeError"""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_config(str(bad_file))

    def test_search_params_present(self, config_path):
        """搜索参数存在且有默认值"""
        config = load_config(config_path)
        params = get_search_params(config)

        assert params["search_depth"] == "advanced"
        assert params["max_results"] == 10


class TestDomainGroups:
    """CONS-03: 域名集合抽象为命名组"""

    def test_domain_groups_structure(self, config_path):
        """配置包含正确的域名组结构"""
        config = load_config(config_path)

        assert "domain_groups" in config
        assert "english_tech" in config["domain_groups"]
        assert "chinese_tech" in config["domain_groups"]
        assert "social" in config["domain_groups"]

    def test_domain_group_has_enabled_flag(self, config_path):
        """每个域名组都有 enabled 标志"""
        config = load_config(config_path)

        for group_name, group_config in config["domain_groups"].items():
            assert "enabled" in group_config, f"域名组 '{group_name}' 缺少 'enabled'"
            assert isinstance(group_config["enabled"], bool)

    def test_domain_group_has_domains_list(self, config_path):
        """每个域名组都有 domains 列表"""
        config = load_config(config_path)

        for group_name, group_config in config["domain_groups"].items():
            assert "domains" in group_config, f"域名组 '{group_name}' 缺少 'domains'"
            assert isinstance(group_config["domains"], list)

    def test_english_tech_enabled(self, config_path):
        """英文科技媒体组已启用"""
        config = load_config(config_path)

        assert config["domain_groups"]["english_tech"]["enabled"] is True
        assert len(config["domain_groups"]["english_tech"]["domains"]) > 0

    def test_chinese_tech_disabled(self, config_path):
        """中文科技媒体组已禁用（Phase 3 预留）"""
        config = load_config(config_path)

        assert config["domain_groups"]["chinese_tech"]["enabled"] is False

    def test_social_disabled(self, config_path):
        """社交媒体组已禁用"""
        config = load_config(config_path)

        assert config["domain_groups"]["social"]["enabled"] is False

    def test_get_enabled_domains_filters(self, config_path):
        """get_enabled_domains 只返回已启用组的域名"""
        config = load_config(config_path)
        domains = get_enabled_domains(config)

        assert len(domains) > 0
        assert "techcrunch.com" in domains
        assert "x.com" in domains

    def test_get_enabled_domains_excludes_disabled(self, config_path):
        """禁用组的域名不出现在结果中"""
        config = load_config(config_path)
        domains = get_enabled_domains(config)

        # chinese_tech 和 social 是空的且禁用的，所以不会有影响
        # 但如果给 chinese_tech 加了域名但保持 disabled，也不应该出现
        modified_config = dict(config)
        modified_config["domain_groups"]["chinese_tech"] = {
            "enabled": False,
            "domains": ["36kr.com", "qbitai.com"],
        }
        domains = get_enabled_domains(modified_config)

        assert "36kr.com" not in domains
        assert "qbitai.com" not in domains

    def test_all_english_tech_domains_present(self, config_path):
        """英文科技媒体包含预期的域名"""
        config = load_config(config_path)
        domains = config["domain_groups"]["english_tech"]["domains"]

        expected = [
            "techcrunch.com", "theinformation.com", "bloomberg.com",
            "reuters.com", "businessinsider.com", "venturebeat.com",
            "x.com", "linkedin.com", "subsight.com",
        ]
        for domain in expected:
            assert domain in domains, f"缺少域名: {domain}"


class TestConfigValidation:
    """配置验证逻辑"""

    def test_missing_queries_raises(self):
        """缺少 queries 字段抛出 ValueError"""
        config = {"domain_groups": {}, "search_params": {}}
        with pytest.raises(ValueError, match="queries"):
            _validate_config(config)

    def test_missing_domain_groups_raises(self):
        """缺少 domain_groups 字段抛出 ValueError"""
        config = {
            "queries": {
                "english_broad": [], "english_specific": [],
                "chinese_broad": [], "chinese_specific": [],
            },
            "search_params": {},
        }
        with pytest.raises(ValueError, match="domain_groups"):
            _validate_config(config)

    def test_missing_query_group_raises(self):
        """缺少必需的查询组抛出 ValueError"""
        config = {
            "queries": {"english_broad": []},
            "domain_groups": {
                "english_tech": {"enabled": True, "domains": []},
                "chinese_tech": {"enabled": False, "domains": []},
                "social": {"enabled": False, "domains": []},
            },
            "search_params": {},
        }
        with pytest.raises(ValueError, match="查询组"):
            _validate_config(config)

    def test_empty_query_in_list_raises(self):
        """查询列表中包含空字符串抛出 ValueError"""
        config = {
            "queries": {
                "english_broad": [""],
                "english_specific": [],
                "chinese_broad": [],
                "chinese_specific": [],
            },
            "domain_groups": {
                "english_tech": {"enabled": True, "domains": []},
                "chinese_tech": {"enabled": False, "domains": []},
                "social": {"enabled": False, "domains": []},
            },
            "search_params": {},
        }
        with pytest.raises(ValueError, match="不能为空"):
            _validate_config(config)

    def test_merge_defaults_fills_missing(self):
        """默认值合并正确填充缺失字段"""
        user = {"queries": {"english_broad": ["test"]}}
        merged = _merge_defaults(DEFAULT_CONFIG, user)

        assert merged["queries"]["english_broad"] == ["test"]
        assert merged["queries"]["english_specific"] == []
        assert merged["domain_groups"]["english_tech"]["enabled"] is True

    def test_user_overrides_defaults(self):
        """用户配置覆盖默认值"""
        user = {
            "search_params": {"max_results": 5},
        }
        merged = _merge_defaults(DEFAULT_CONFIG, user)

        assert merged["search_params"]["max_results"] == 5
        assert merged["search_params"]["search_depth"] == "advanced"
