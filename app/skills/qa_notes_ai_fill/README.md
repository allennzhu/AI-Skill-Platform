# qa_notes_ai_fill — 「总结与关注事项」AI 回填 Skill

面向 统计-测试数据看板 →「总结与关注事项」板块的 AI 分析功能：前端点击「AI分析」按钮 →
**前端装配完整 context**（页面已加载的看板数据 + 少量补充请求）→ 经业务后端薄代理调本 skill →
返回与前端表单结构一一对应的 JSON → 前端直接回填（进入编辑草稿态，由 QA 确认后保存）。

> 调用模式与 `qa_board_analysis` 示例一致：**skill 只收已聚合好的 context，不负责查数**。
> 采用「前端装配」而非「后端按筛选参数重查」的理由：看板 4 个只读接口前端本就已请求
> （kpi/bug/publish/current_summary 就在页面内存里），AI 分析的数据与用户屏幕所见严格同源；
> 后端零聚合代码。数据虽来自客户端，但产物仅为草稿、人工确认后才落库，可信风险可接受。

---

## 一、前端装配 context 规则

### 调用链路（对齐 qa_board_analysis 已上线的前端直连先例）

```
前端「AI分析」按钮
  → 装配 context（见下表）
  → executeSkill({ intent: 'qa_notes_ai_fill', slots: { context, sections? } })
      // boardAnalysisApi.js 既有方法：POST {VUE_APP_AGENT_API}/v1/execute
  → 拿 result.notes 回填草稿态
```

- 前端复用 `statistic/bug/components/overview/boardAnalysisApi.js` 的 `executeSkill`
  （qa_board_analysis 已在用：env `VUE_APP_AGENT_API` 直连 Agent 平台，需 CORS 放行页面地址）。
- 超时 ≥120s；按钮 loading 提示「AI 分析中，约需 1 分钟」；失败 toast 不回填
  （网络错误提示参考既有实现：「无法连接 AI 服务，请确认 Agent 已启动且 CORS 允许当前页面地址」）。
- **只生成不落库**：notes 回填草稿态，QA 确认后走既有 add/update/delete_qa_stat_summary_item 保存。
- 后续若需收权，可在业务后端加薄代理（仅鉴权+转发）替换 env 直连，skill 与前端装配逻辑不变。

### context 字段与前端取数来源（全部为既有接口，无需后端改动）

| context 字段 | 前端来源 | 说明 |
|---|---|---|
| `period` | 筛选条 | `{ period_type, period_key }`（buildQaStatParams 同款） |
| `filters` | 筛选条 | `{ dept_id, assigned_to, tester, pm_id }`，全 0 可省略 |
| `kpi` | 页面已有（`get_qa_stat_kpi` 响应） | 完整 `summary` + `targets` + `is_default_target` |
| `bug` | 页面已有（`get_qa_stat_bug` 响应) | 完整响应（overview / 各分布 / 各 TOP 堆积） |
| `publish` | 页面已有（`get_qa_stat_publish` 响应） | 完整响应 |
| `delay_detail` | `publish.delay_list` 直接取用 | skill 内截前 10 条 |
| `over_tb_detail` | **补充请求** `getOverTbFilteredList`（chart_key=over_tb，前端口径修正剔除延期条目） | 超时递交逐条明细（前端截 15 条；超时无审批，原因字段可能缺失） |
| `bug_samples` | **补充请求** `get_qa_stat_detail_list` | 见下方抽样规则 |
| `prev_summary` | **补充请求** `get_qa_stat_summary`（上期 key） | 仅取 `process_improve` + `key_matters`；上期 key 用 `periodUtils.prevPeriodOf` 现成推导 |
| `current_summary` | 页面已有（QaNotesSection 已加载 items） | 当前人工内容，AI 补充而非重复/冲突 |

补充请求仅 2~4 个，点击按钮后 `Promise.all` 并行拉取即可；某项失败可降级省略
（validator 只要求 kpi/bug/publish 至少一项存在）。

**bug_samples 抽样规则**（控制 token，同时保证代表性）：

1. 按 `chart_key=bug_level, option_id=4`（致命）拉 `limit=15`；
2. 再按 `option_id=3`（严重）拉 `limit=15`；
3. 再取 `bug.bug_type_distribution` 中 count 最高的类型，`chart_key=bug_type` 拉 `limit=10`；
4. 三批合并按 bug id 去重，只保留字段：`bug_type_name / bug_level_name / bug_status_name /
   project_name / assigned_to_name / content / remark / program_repair_time / scene_repair_time`。

**筛选生效范围与看板一致**：`kpi / bug / publish / bug_samples` 带全部四项筛选；
`prev_summary / current_summary` 仅按 `period_type + period_key`（总结按周期独立，不受人筛影响）。

**周期粒度**：period_type 取 week / month / quarter / half / year（含「周」，
period_key 如 '2026-W27' ISO 周——看板既有 API 文档的周期键表漏列 week，以前端筛选条为准）。

### 调用 skill

```jsonc
POST /v1/execute
{
  "intent": "qa_notes_ai_fill",
  "slots": {
    "context": { /* 上表装配结果 */ },
    "sections": ["bug_summary"]   // 可选：只重新生成部分板块，默认全部
  }
}
```

---

## 二、输出数据结构（与前端 QaNotesSection 表单契约一一对应）

`result.notes`（前端可直接塞进编辑草稿 `draft`）：

```jsonc
{
  "role_reviews": [                       // → 各角色问题总结与改进建议（2~5 条）
    { "role": "PM", "problem": "…", "suggestion": "…" }
  ],
  "bug_summary": "…",                     // → BUG 总结分析（150~400 字连贯段落）
  "bug_suggestions": {                    // → BUG 改进建议三块
    "art": "…", "program": "…", "qa": "…"
  },
  "focus_items": [                        // → 重点关注事项（1~6 条，按重要度排序）
    { "title": "…", "duty_role": "研发、QA", "conclusion": "…" }
  ],
  "process_items": [                      // → 测试流程改进与工具落地（0~4 条，无依据则空）
    { "title": "…", "progress": "…" }
  ]
}
```

- `role` / `duty_role` 岗位白名单：`PM / QA / 程序 / 美术 / 场景 / 策划 / 研发`；
  `duty_role` 顿号分隔（与前端 `tags ↔ duty_role` 的转换约定一致，前端保存时 `split('、')` 回 tags）。
- 字段名即前端 data 键名（`problem/suggestion/title/duty_role/conclusion/progress`），零映射回填。
- 前端保存仍走既有 add/update/delete 总结条目接口（AI 结果先进草稿态，人工确认后落库）。
- `sections` 传子集时，未请求的板块返回空值（数组 `[]` / 字符串 `""`），前端只回填请求的板块。

---

## 三、内容质量规则（已固化进 system prompt + 代码双重保障）

### Prompt 层（约束 LLM）

1. **禁止编造**：所有数字/百分比/排名必须来自 context 或其简单加减；不可比（prev 为 null）不写环比。
2. **角色有据**：role_reviews 只为数据确实暴露问题的岗位写条目，problem 必须点出数据依据。
3. **总结覆盖面**：bug_summary 必须覆盖 总量与环比 / 致命严重占比与目标达成 / 类型 TOP /
   未自检占比 / 高发部门项目 点名。
4. **建议贴侧**：art/program/qa 三条各自贴合本侧数据、互不重复；某侧无突出问题时给客观结论，不硬凑。
5. **关注事项来源受限**：延期超时项目根因 / 致命严重集中点 / 临时递交异常 / 目标未达成 /
   上期 key_matters 闭环跟踪 —— 五类之外不生成。
6. **流程推进不虚构**：process_items 仅在上期有推进项（写延续）或本期数据明确指向（如自检率低）时输出，
   否则空数组；禁止编造「工具已上线」类进展。
7. **局部视角守则**：filters 带非 0 筛选时不下全中心级结论。
8. **与人工内容互补**：current_summary 已覆盖的观点不重复。

### 代码层（sanitize 兜底，LLM 违规也不会污染前端）

- 严格 JSON 提取（平衡括号扫描）+ 解析失败**一次修复重试**，仍失败返回 502。
- 结构强对齐：多余键丢弃、缺失键补空；role 白名单过滤 + 去重，超 5 条截断；
  focus_items ≤6、process_items ≤4；duty_role 拆分→白名单过滤→顿号重组。
- 文本长度截断（正文 ≤800 字、bug_summary ≤1200 字、标题 ≤60 字）。
- 清洗后全空视为失败（502），避免前端回填一板空内容。

---

## 文件结构（与平台 skill 规范一致）

| 文件 | 职责 |
|---|---|
| `manifest.yaml` | name/intent/description + slots 声明（required: context；optional: sections） |
| `validator.py` | context 必须含 period 且至少一类统计数据；sections 枚举校验 |
| `normalizer.py` | 字段裁剪 + 16k 字符预算分级降级（砍样本→砍长列表→只留 overview） |
| `executor.py` | system prompt + LLM 调用 + JSON 提取修复 + 字段级 sanitize |
| `response.py` | 包装 `result.notes`；`reply` 用 bug_summary 兜底对话展示 |
