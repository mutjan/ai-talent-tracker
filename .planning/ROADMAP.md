# Roadmap: AI Talent Tracker — 搜索优化

## Overview

从两个分散的英文搜索脚本，扩展为一个统一的、覆盖中英文社交媒体的智能搜索系统。分 5 个阶段执行：先整合脚本消除重复代码，再建立跨批次去重防止数据泛滥，然后扩展搜索覆盖范围（中文 + X/Twitter），接着实现动态查询生成让系统自我进化，最后自动化每日执行实现当天发现。

## Phases

- [ ] **Phase 1: 脚本整合** — 合并两个搜索脚本为统一的配置驱动管道
- [ ] **Phase 2: 跨批次去重** — 实现 seen_urls.json 持久化，防止每天重复
- [ ] **Phase 3: 扩展覆盖** — 添加中文查询、扩展域名、优化 Tavily 参数
- [ ] **Phase 4: 动态查询** — 从 events.json 自动生成补充搜索词
- [ ] **Phase 5: 自动化调度** — GitHub Actions 每日执行

## Phase Details

### Phase 1: 脚本整合
**Goal**: 将 talent_search.py 和 tavily_search.py 合并为单一配置驱动的搜索脚本
**Depends on**: Nothing
**Requirements**: CONS-01, CONS-02, CONS-03, CONS-04
**Success Criteria** (what must be TRUE):
  1. 只有一个搜索脚本，talent_search.py 和 tavily_search.py 的功能都在里面
  2. 搜索查询定义在配置字典中，修改查询不需要改代码逻辑
  3. 域名集合按命名组组织（english_tech / chinese_tech / social）
  4. 候选事件输出格式统一，两个旧脚本的字段差异已消除
**Plans**: 3 plans

Plans:
- [ ] 01-01: 合并两个脚本的搜索逻辑到一个文件
- [ ] 01-02: 将查询定义和域名列表外部化为配置
- [ ] 01-03: 统一输出格式并验证兼容性

### Phase 2: 跨批次去重
**Goal**: 实现持久化的 URL 去重，防止同一新闻在不同日期重复出现
**Depends on**: Phase 1
**Requirements**: DEDU-01, DEDU-02, DEDU-03
**Success Criteria** (what must be TRUE):
  1. 连续两天运行搜索，第二天不会出现第一天已返回的 URL
  2. seen_urls.json 自动清理 90 天前的记录
  3. 去重操作前自动备份 events.json
**Plans**: 2 plans

Plans:
- [ ] 02-01: 实现 seen_urls.json 读写和 URL 过滤逻辑
- [ ] 02-02: 添加 90 天清理和备份机制

### Phase 3: 扩展覆盖
**Goal**: 添加中文搜索查询和域名覆盖，利用 Tavily 未使用的参数
**Depends on**: Phase 2
**Requirements**: COVR-01, COVR-02, COVR-03, COVR-04
**Success Criteria** (what must be TRUE):
  1. 搜索查询包含至少 10 个中文关键词组合
  2. 域名列表包含 3 个以上中国科技媒体
  3. 搜索参数使用 topic="news" 和 country="cn"
  4. 中文搜索结果能提取出人名和公司名基本信息
**Plans**: 3 plans

Plans:
- [ ] 03-01: 添加中文搜索查询和中国科技媒体域名
- [ ] 03-02: 优化 Tavily 参数（topic、country、exact_match）
- [ ] 03-03: 实现中文人名/公司名基础提取

### Phase 4: 动态查询
**Goal**: 从 events.json 自动提取高频人名和公司名，生成补充搜索查询
**Depends on**: Phase 3
**Requirements**: DYNA-01, DYNA-02, DYNA-03
**Success Criteria** (what must be TRUE):
  1. 每次搜索自动从 events.json 生成最多 20 个动态查询
  2. 查询数量有上限，不会导致 API 配额耗尽
  3. 搜索结果按相关性和新鲜度排序展示
**Plans**: 2 plans

Plans:
- [ ] 04-01: 实现人名/公司名频率提取和查询生成
- [ ] 04-02: 添加搜索结果 freshness 排序

### Phase 5: 自动化调度
**Goal**: GitHub Actions 每天自动执行搜索，实现当天发现消息
**Depends on**: Phase 4
**Requirements**: AUTO-01, AUTO-02
**Success Criteria** (what must be TRUE):
  1. GitHub Actions 每天 UTC 时间 01:00 自动执行搜索
  2. 支持 workflow_dispatch 手动触发
  3. 候选事件自动保存到 .temp/ 目录供人工审核
**Plans**: 1 plan

Plans:
- [ ] 05-01: 配置 GitHub Actions 每日定时任务

---
*Roadmap created: 2026-04-04*
*Requirements: 16 total, all mapped ✓*
