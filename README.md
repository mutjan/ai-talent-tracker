# AI 人才追踪器

追踪全球顶级AI公司的人才流动趋势，每日自动更新。

## 📋 操作指南

### 1. 添加事件记录

#### 方式一：使用脚本添加
1. 修改 `add-event.js` 文件中的 `newEvent` 对象，填写事件详情：
```javascript
const newEvent = {
  id: Date.now().toString(), // 自动生成，无需修改
  person: "姓名",
  type: "join/leave", // join: 加入, leave: 离职
  date: "YYYY-MM-DD",
  from: "原公司",
  to: "新公司",
  role: "职位",
  source: "来源链接",
  summary: "事件描述",
  tags: ["标签1", "标签2"]
};
```

2. 运行脚本添加事件：
```bash
node add-event.js
```

#### 方式二：手动编辑数据文件
直接修改 `data/events.json` 文件，在数组末尾添加新的事件对象，保持格式与现有条目一致。

---

### 2. 修改/删除记录

1. 编辑 `data/events.json` 文件，找到对应事件进行修改或删除
2. 事件通过 `id` 字段唯一标识，请勿随意修改已有事件的ID
3. 修改完成后运行去重检查：
```bash
python3 scripts/deduplicate.py
```

---

### 3. 添加洞察分析

重要人事事件需要在洞察页面进行深度分析，更新步骤：

1. 编辑 `insights.html` 文件，找到 `insights-section` 部分
2. **在现有最上方条目之前**添加新的洞察条目，参考格式：
```html
<!-- Entry X (New YYYY-MM-DD) -->
<div class="insight-entry [类型]">
  <div class="insight-date">YYYY-MM-DD · 今日更新</div>
  <div class="insight-card">
    <div class="insight-header">
      <span class="insight-tag tag-[类型]">标签</span>
      <span class="insight-title">洞察标题</span>
    </div>
    <div class="insight-content">
      <p>深度分析内容...</p>
    </div>
    <div class="insight-stats">
      <span class="stat-pill">统计项: <strong>数值</strong></span>
    </div>
    <div class="insight-people">
      <span class="person-chip">人名 <span class="company">原公司 → 新公司</span></span>
    </div>
    <div class="insight-source">
      来源: <a href="链接" target="_blank">来源名称</a>
    </div>
  </div>
</div>
```

#### 条目类型与样式：
- `alert` (红色) + `tag-alert`: 人才流失警报
- `highlight` (橙色) + `tag-highlight`: 重磅挖角/重要动态
- `success` (绿色) + `tag-success`: 创业动态/新创公司
- `china` (紫色) + `tag-china`: 中国AI动态
- 默认 (蓝色) + `tag-trend`: 一般趋势/人才流入

---

### 4. 更新统计数据

编辑 `insights.html` 中的 `summary-box` 部分，更新顶部概览卡片：
```html
<div class="summary-box">
  <div class="summary-title">本期更新概览 · YYYY年MM月DD日</div>
  <div class="summary-grid">
    <div class="summary-item">
      <div class="summary-label">新增事件</div>
      <div class="summary-value up">+N</div> <!-- N为新增事件数量 -->
    </div>
    <div class="summary-item">
      <div class="summary-label">数据库总量</div>
      <div class="summary-value">XXX</div> <!-- 运行 `wc -l data/events.json` 查看总数 -->
    </div>
    <!-- 其他统计项按需更新 -->
  </div>
</div>
```

---

### 5. 提交与发布

```bash
# 检查变更
git status

# 添加文件
git add data/events.json insights.html add-event.js

# 提交变更
git commit -m "[操作类型]: [简要描述]"
# 示例：git commit -m "Add event: Awni Hannun joins Anthropic"
# 示例：git commit -m "Add insight: Meta recruits 4 top AI researchers"

# 推送到GitHub
git push origin main
```

#### 提交信息规范：
- 添加事件：`Add event: [人物] [事件]`
- 修改事件：`Update event: [人物] [事件]`
- 删除事件：`Delete event: [人物] [事件]`
- 添加洞察：`Add insight: [标题]`
- 更新统计：`Update stats: [更新内容]`

---

## 📁 项目结构

```
ai-talent-tracker/
├── data/
│   └── events.json          # 所有事件数据文件
├── scripts/
│   ├── deduplicate.py       # 去重脚本，pre-commit自动运行
│   ├── talent_search.py     # 人才搜索脚本
│   └── tavily_search.py     # 新闻搜索脚本
├── index.html               # 主页面
├── insights.html            # 关键洞察页面
├── detail.html              # 详情页面
├── add-event.js             # 添加事件脚本
├── pre-commit               # Git钩子配置
└── README.md                # 本文件
```

---

## ⚙️ 自动更新机制

项目配置了每日自动爬虫，通过Tavily搜索最新AI人才新闻，自动解析并添加到数据库中。人工审核后更新洞察页面。

## 🔗 在线访问

- [人才追踪器主页](https://mutjan.github.io/ai-talent-tracker/)
- [关键洞察页面](https://mutjan.github.io/ai-talent-tracker/insights.html)
