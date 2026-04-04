# Phase 01: 脚本整合 - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

将 `talent_search.py` 和 `tavily_search.py` 合并为单一配置驱动的搜索脚本。消除两个脚本间的重复代码（70%+），统一查询定义、域名管理、输出格式。Phase 1 只做整合，不新增中文查询、不引入外部 API。
</domain>

<decisions>
## Implementation Decisions

### 脚本命名与位置
- **D-01:** 合并后的脚本命名为 `scripts/search.py`，放在现有 `scripts/` 目录下
- **D-02:** 合并完成后删除 `scripts/talent_search.py` 和旧的 `scripts/tavily_search.py`

### 查询配置结构
- **D-03:** 搜索查询定义为顶层 Python dict，按查询类别分组（如 `english_broad`、`english_specific`），每个 key 的值是查询字符串列表
- **D-04:** 查询定义与搜索逻辑解耦——修改查询只需改配置 dict，不碰函数体

### 域名组设计
- **D-05:** 域名按类型分组成命名 dict（`english_tech` / `chinese_tech` / `social`），支持按组启用/停用
- **D-06:** Phase 1 只启用 `english_tech` 组（9 个现有英文科技媒体域名），中文组和社交组预留但不激活

### 输出格式统一
- **D-07:** 候选事件格式以 tavily_search.py 的字段为基础：包含 `id`、`person_name`、`event_type`、`date_event`（自动解析）、`from_company`、`to_company`、`role`、`source_url`、`date_discovered`、`summary`、`tags`、`_needs_review`、`_source_title`、`_mentioned_companies`、`_source_content`（500 字符预览，从 talent_search 补充）
- **D-08:** 去重逻辑复用 tavily_search.py 的 URL 去重方式（within-session），跨批次 URL 去重留给 Phase 2

### Claude's Discretion
- 具体函数划分和内部模块组织
- 日志消息的中英文措辞
- 错误重试的具体实现细节
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Script consolidation requirements
- `.planning/REQUIREMENTS.md` — CONS-01 到 CONS-04 的详细要求
- `.planning/ROADMAP.md` — Phase 1 目标与成功标准
- `scripts/tavily_search.py` — 现有较完整的搜索脚本实现（261 行）
- `scripts/talent_search.py` — 现有较简单的搜索脚本实现（162 行）
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `load_events()` / `save_events()`: 两个脚本都有相同实现，直接复用到新脚本
- `parse_date_from_text()`: tavily_search.py 的日期解析逻辑，可从标题和摘要中解析日期
- `extract_person_and_companies()`: tavily_search.py 的公司名提取，内置 30+ 中外 AI 公司列表
- `is_duplicate()`: tavily_search.py 的四字段去重逻辑（person + from + to + date）
- `scripts/deduplicate.py`: 独立去重脚本，pre-commit hook 调用，Phase 1 无需改动

### Established Patterns
- Python snake_case 命名，4 空格缩进，中文 docstring
- `if __name__ == "__main__"` 入口守卫
- `TAVILY_API_KEY` 环境变量，缺失时 `sys.exit(1)`
- 中文日志输出（如 `print("已加载 ... 条现有事件")`）
- 候选事件输出到 `.temp/candidates_*.json`
- 错误处理：`except Exception as e` + `print()` + `continue`

### Integration Points
- `data/events.json`: 读取已有事件用于去重，不写入（写入由人工审核流程完成）
- `.temp/` 目录: 保存候选事件供人工审核
- 预提交 hook: 调用 `scripts/deduplicate.py`，与 Phase 1 无直接交集
- `add-event.js`: 手动添加事件的 Node.js 脚本，候选事件格式需与之兼容
</code_context>

<specifics>
## Specific Ideas

- 用户选择了推荐方案，倾向于简洁实用的设计
- 当前有 150 条事件数据，1884 行 JSON
- 两个脚本的查询都是英文的——Phase 1 保持英文，Phase 3 加中文
</specifics>

<deferred>
## Deferred Ideas

- 中文搜索查询（COVR-01）— Phase 3
- Tavily topic="news"、country="cn"、exact_match 参数优化 — Phase 3
- 跨批次 URL 去重（seen_urls.json）— Phase 2
- 动态查询生成（从 events.json 自动提取）— Phase 4
- GitHub Actions 每日执行 — Phase 5

None — discussion stayed within phase scope
</deferred>

---

*Phase: 01-脚本整合*
*Context gathered: 2026-04-04*