# Requirements: AI Talent Tracker — 搜索优化

**Defined:** 2026-04-04
**Core Value:** 尽可能全面、及时地发现AI人才流动消息

## v1 Requirements

### Consolidate (脚本整合)

- [ ] **CONS-01**: 合并 talent_search.py 和 tavily_search.py 为单一搜索脚本，消除 70% 重复代码
- [ ] **CONS-02**: 搜索查询定义外部化为配置（Python dict），不再硬编码在函数体中
- [ ] **CONS-03**: 域名集合抽象为命名组（english_tech / chinese_tech / social），支持按组启用
- [ ] **CONS-04**: 统一候选事件输出格式，消除两个脚本间的字段命名差异

### Dedup (去重增强)

- [ ] **DEDU-01**: 实现跨批次 URL 去重——持久化 seen_urls.json，避免同一新闻每天重复出现
- [ ] **DEDU-02**: seen_urls.json 支持 90 天自动清理，防止文件无限增长
- [ ] **DEDU-03**: 去重前备份 events.json，防止去重操作误删数据

### Coverage (覆盖扩展)

- [ ] **COVR-01**: 添加中文搜索查询——覆盖中文 AI 人才动态关键词（如 "AI 人才 离职 加入"、"首席科学家 离开"）
- [ ] **COVR-02**: 扩展搜索域名——加入中国科技媒体（36kr.com、qbitai.com、jiqizhixin.com）和 X/Twitter
- [ ] **COVR-03**: 利用 Tavily 未使用的参数优化搜索——topic="news"、country="cn"、exact_match=True
- [ ] **COVR-04**: 中文人名/公司名提取——支持从中文搜索结果中识别人才事件基本信息

### Dynamic (动态查询)

- [ ] **DYNA-01**: 从 events.json 提取高频人名和公司名，自动生成补充搜索查询
- [ ] **DYNA-02**: 动态查询数量有上限（可配置，默认 20），防止 API 配额耗尽
- [ ] **DYNA-03**: 搜索结果按 freshness + relevance 排序，降低人工审核负担

### Automation (自动化)

- [ ] **AUTO-01**: GitHub Actions 从每周执行改为每天执行，实现当天发现消息
- [ ] **AUTO-02**: 支持 workflow_dispatch 手动触发，作为定时任务的备用方案

## v2 Requirements

### Advanced Coverage (高级覆盖)

- **COVR-05**: TikHub SDK 集成——直接搜索微博、知乎等封闭中文社交平台（需要账号和测试验证）
- **COVR-06**: Hacker News 集成——通过 hn.algolia.com 免费 API 搜索 HN 上的 AI 人才讨论
- **COVR-07**: 公司专属查询模板——为 Top 30 AI 实验室生成专门的搜索词

### Intelligence (智能分析)

- **DYNA-04**: 时序聚类检测——同一公司在短期内多次人事变动时发出预警
- **DYNA-05**: 搜索结果去噪评分——基于关键词匹配度和来源可信度过滤低质量结果

## Out of Scope

| Feature | Reason |
|---------|--------|
| 额外搜索 API（百度、搜狗、Google）| PROJECT.md 约束：只用 Tavily，简化依赖 |
| 实时推送通知 | 当天发现即可，不需要实时 |
| LLM 自动解析新闻为结构化事件 | 保持人工审核流程 |
| 直接订阅社交媒体账号 | 通过搜索引擎间接覆盖 |
| 全文搜索 events.json | 150 条数据，客户端过滤够用 |
| ML 相关性评分 | 数据集太小，简单关键词匹配够用 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONS-01 | Phase 1 | Pending |
| CONS-02 | Phase 1 | Pending |
| CONS-03 | Phase 1 | Pending |
| CONS-04 | Phase 1 | Pending |
| DEDU-01 | Phase 2 | Pending |
| DEDU-02 | Phase 2 | Pending |
| DEDU-03 | Phase 2 | Pending |
| COVR-01 | Phase 3 | Pending |
| COVR-02 | Phase 3 | Pending |
| COVR-03 | Phase 3 | Pending |
| COVR-04 | Phase 3 | Pending |
| DYNA-01 | Phase 4 | Pending |
| DYNA-02 | Phase 4 | Pending |
| DYNA-03 | Phase 4 | Pending |
| AUTO-01 | Phase 5 | Pending |
| AUTO-02 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 16 total
- Mapped to phases: 16
- Unmapped: 0

---
*Requirements defined: 2026-04-04*
*Last updated: 2026-04-04 after initial definition*