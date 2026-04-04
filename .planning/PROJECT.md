# AI Talent Tracker — 搜索策略优化

## What This Is

追踪全球顶级AI公司人才流动的项目，当前已有 150 条事件数据。本次优化聚焦于**扩大搜索覆盖范围**——从固定的 4-6 个英文查询 + 少数科技媒体，扩展到覆盖中英文社交媒体（微博、知乎、脉脉、X/Twitter、LinkedIn、HN 等），确保当天内发现新的人才动态。

## Core Value

尽可能全面、及时地发现AI人才流动消息，让用户不漏掉重要的人事变动。

## Requirements

### Validated

- ✓ 事件数据存储在 data/events.json（150 条，结构化 JSON）—— existing
- ✓ Tavily API 搜索英文科技新闻 —— existing
- ✓ 去重机制（person_name + from_company + to_company + date_event）—— existing
- ✓ 人工审核流程（搜索结果存到 .temp/candidates_*.json，人工确认后合并）—— existing
- ✓ Pre-commit hook 自动去重 —— existing
- ✓ 静态页面展示（GitHub Pages：主页 + 洞察 + 详情）—— existing

### Active

- [ ] 扩大搜索查询覆盖面：从 4-6 个固定英文查询扩展到覆盖中文人才动态的搜索词
- [ ] 动态搜索词生成：从 events.json 中提取高频人名和公司名，自动生成补充查询
- [ ] 扩大搜索域名覆盖：加入中文媒体源（知乎、微博等可通过 Tavily 搜到的源）
- [ ] 增加 X/Twitter 内容搜索：利用 Tavily 的 include_domains 搜 X 上的 AI 人才动态
- [ ] 搜索结果去重优化：跨批次去重（避免重复搜索已处理过的新闻）
- [ ] 搜索频率提升：从每周一次提升到每天执行

### Out of Scope

- 不接入额外的中文搜索 API（百度、搜狗等）—— 暂时只用 Tavily，后续按需扩展
- 不做实时监控/推送通知 —— 当天发现即可
- 不做 LLM 自动解析新闻成结构化事件 —— 保持人工审核流程
- 不做社交媒体账号直接关注/订阅 —— 通过搜索引擎间接覆盖

## Context

- **现有搜索架构**：两个 Python 脚本（talent_search.py、tavily_search.py），都用 Tavily API，各自跑 4-6 个固定查询
- **搜索词现状**：都是英文，如 "AI researcher joins leaves OpenAI Google DeepMind Anthropic"
- **域名限制**：talent_search.py 限定了 9 个科技媒体域名（techcrunch、bloomberg 等），tavily_search.py 不限定域名
- **执行频率**：README 描述为「每日自动更新」，但 GitHub Actions 实际配置为每周一执行
- **输出格式**：候选事件存到 .temp/candidates_*.json，需要人工审核后手动合并到 events.json
- **已知问题**：两条 schema 版本共存（旧格式 person/type/from/to vs 新格式 person_name/event_type/from_company）

## Constraints

- **API**: 只用 Tavily API，不引入额外搜索服务
- **时效性**: 当天发现即可，不需要实时
- **人工审核**: 搜索结果必须经过人工确认才能入库
- **兼容性**: 新搜索策略必须兼容现有的 events.json 数据结构和去重逻辑

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 继续用 Tavily 作为唯一搜索源 | 简化依赖，Tavily 已能搜中英文和 X 内容 | — Pending |
| 混合搜索词策略 | 固定查询保底 + 动态热门词补充，平衡覆盖面和噪音 | — Pending |
| 当天发现即可 | 不追求实时，降低系统复杂度 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone:**
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-04 after initialization