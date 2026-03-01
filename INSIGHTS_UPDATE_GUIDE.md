# 关键洞察页面更新指南

## 何时更新

当每日更新添加了重要人事变动事件时，需要同步更新 `insights.html` 关键洞察页面。

## 更新步骤

### 1. 分析新事件

识别以下类型的重要变动：
- 高管/创始人离职或加入
- 安全团队成员变动
- 大规模人才流动（如 xAI 创始团队流失）
- 重磅挖角（如 Meta MSL 招募）
- 知名研究者创业
- 中国 AI 公司重要人事变动

### 2. 添加新洞察条目

在 `insights.html` 的 `insights-section` div 内，在现有条目之前添加新条目：

```html
<!-- Entry X -->
<div class="insight-entry [类型]">
  <div class="insight-date">YYYY-MM-DD · 分类</div>
  <div class="insight-card">
    <div class="insight-header">
      <span class="insight-tag tag-[类型]">标签</span>
      <span class="insight-title">标题</span>
    </div>
    <div class="insight-content">
      <p>分析内容...</p>
    </div>
    <div class="insight-people">
      <span class="person-chip">人名 <span class="company">公司</span></span>
    </div>
    <div class="insight-source">
      来源: <a href="..." target="_blank">来源名</a>
    </div>
  </div>
</div>
```

### 3. 条目类型样式

- `alert` (红色) + `tag-alert`: 人才流失警报
- `highlight` (橙色) + `tag-highlight`: 重磅挖角/重要动态
- `success` (绿色) + `tag-success`: 创业动态/新创公司
- `china` (紫色) + `tag-china`: 中国 AI 动态
- 默认 (蓝色) + `tag-trend`: 一般趋势/人才流入

### 4. 更新概览卡片

修改页面顶部的 `summary-box` 中的统计数字：
- 新增事件数
- 数据库总量
- 关键指标（如 xAI 剩余创始人数）

### 5. 提交更新

```bash
git add insights.html
git commit -m "Update insights: [简要描述更新内容]"
git push origin main
```

## 示例条目

参考现有的 8 个条目格式，保持风格一致。
