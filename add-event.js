#!/usr/bin/env node
/**
 * 添加事件脚本 - 向 events.json 添加新的人才流动事件
 *
 * 使用方法:
 * 1. 修改下方的 newEvent 对象，填写事件详情
 * 2. 运行: node add-event.js
 */

const fs = require('fs');
const path = require('path');

// ==================== 配置区域 ====================
// 在这里填写新事件的信息
const newEvent = {
  // 自动生成ID，无需修改
  id: Date.now().toString(),

  // 人物姓名（必填）
  person_name: "姓名",

  // 事件类型: join(加入) / leave(离职) / move(跳槽)
  event_type: "move",

  // 日期: YYYY-MM-DD 格式
  date_event: "2026-04-03",

  // 原公司（leave类型可不填）
  from_company: "原公司",

  // 新公司（leave类型可不填）
  to_company: "新公司",

  // 职位/头衔
  role: "职位",

  // 来源链接
  source_url: "https://example.com/news",

  // 发现日期（自动生成）
  date_discovered: new Date().toISOString().split('T')[0],

  // 事件摘要
  summary: "事件描述...",

  // 标签
  tags: ["标签1", "标签2"]
};
// ==================== 配置区域结束 ====================

// 文件路径
const DATA_FILE = path.join(__dirname, 'data', 'events.json');

/**
 * 加载现有事件
 */
function loadEvents() {
  try {
    if (!fs.existsSync(DATA_FILE)) {
      console.error(`错误: 找不到文件 ${DATA_FILE}`);
      process.exit(1);
    }
    const data = fs.readFileSync(DATA_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error(`读取文件失败: ${error.message}`);
    process.exit(1);
  }
}

/**
 * 保存事件
 */
function saveEvents(events) {
  try {
    fs.writeFileSync(DATA_FILE, JSON.stringify(events, null, 2), 'utf8');
    return true;
  } catch (error) {
    console.error(`保存文件失败: ${error.message}`);
    return false;
  }
}

/**
 * 检查重复事件
 */
function isDuplicate(newEvent, existingEvents) {
  const person = newEvent.person_name.toLowerCase().trim();
  const fromCo = newEvent.from_company.toLowerCase().trim();
  const toCo = newEvent.to_company.toLowerCase().trim();
  const date = newEvent.date_event;

  return existingEvents.some(event => {
    return event.person_name.toLowerCase().trim() === person &&
           event.from_company.toLowerCase().trim() === fromCo &&
           event.to_company.toLowerCase().trim() === toCo &&
           event.date_event === date;
  });
}

/**
 * 验证事件数据
 */
function validateEvent(event) {
  const required = ['person_name', 'event_type', 'date_event', 'source_url', 'summary'];
  const missing = required.filter(field => !event[field] || event[field] === '姓名' || event[field] === '');

  if (missing.length > 0) {
    return { valid: false, error: `缺少必填字段: ${missing.join(', ')}` };
  }

  // 验证日期格式
  const datePattern = /^\d{4}-\d{2}-\d{2}$/;
  if (!datePattern.test(event.date_event)) {
    return { valid: false, error: '日期格式错误，应为 YYYY-MM-DD' };
  }

  return { valid: true };
}

/**
 * 显示事件信息
 */
function displayEvent(event) {
  console.log('\n========== 事件信息 ==========');
  console.log(`ID:           ${event.id}`);
  console.log(`人物:         ${event.person_name}`);
  console.log(`类型:         ${event.event_type}`);
  console.log(`日期:         ${event.date_event}`);
  console.log(`原公司:       ${event.from_company || '(无)'}`);
  console.log(`新公司:       ${event.to_company || '(无)'}`);
  console.log(`职位:         ${event.role || '(无)'}`);
  console.log(`来源:         ${event.source_url}`);
  console.log(`摘要:         ${event.summary.substring(0, 100)}...`);
  console.log(`标签:         ${event.tags ? event.tags.join(', ') : '(无)'}`);
  console.log('===============================\n');
}

/**
 * 主函数
 */
function main() {
  console.log('=== AI Talent Tracker - 添加事件 ===\n');

  // 检查是否修改了模板
  if (newEvent.person_name === '姓名') {
    console.error('❌ 错误: 请先修改 newEvent 对象中的事件信息！');
    console.error('请编辑 add-event.js 文件，填写实际的事件数据。');
    process.exit(1);
  }

  // 验证事件数据
  const validation = validateEvent(newEvent);
  if (!validation.valid) {
    console.error(`❌ 验证失败: ${validation.error}`);
    process.exit(1);
  }

  // 显示事件信息
  displayEvent(newEvent);

  // 加载现有事件
  const events = loadEvents();
  console.log(`当前数据库共有 ${events.length} 条事件\n`);

  // 检查重复
  if (isDuplicate(newEvent, events)) {
    console.error('❌ 错误: 发现重复事件！');
    console.error(`已存在相同的人物、公司、日期组合: ${newEvent.person_name} | ${newEvent.date_event}`);
    process.exit(1);
  }

  // 添加事件
  events.push(newEvent);

  // 保存
  if (saveEvents(events)) {
    console.log('✅ 事件添加成功！');
    console.log(`\n数据库现在共有 ${events.length} 条事件`);
    console.log('\n建议运行以下命令去重检查:');
    console.log('  python3 scripts/deduplicate.py');
    console.log('\n然后提交变更:');
    console.log('  git add data/events.json');
    console.log('  git commit -m "Add event: [人物] [事件]"');
    console.log('  git push origin main');
  } else {
    console.error('❌ 保存失败！');
    process.exit(1);
  }
}

// 运行主函数
if (require.main === module) {
  main();
}

module.exports = { main, validateEvent, isDuplicate };
