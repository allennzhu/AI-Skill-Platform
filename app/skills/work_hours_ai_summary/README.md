# work_hours_ai_summary — 工时工作总结

对应 Aily `pm-platform-api` 的「生成工作总结 / 日报」能力：前端装配工时明细，经 51PM 代理调本 skill，返回 Markdown 总结。

skill **不查数**。工时来源与 Aily 相同：`GET /manage_api/data_export/get_daily_estimate_list`。

---

## 调用

```
POST /manage_api/ai_skill/execute
超时 900s；需已配置个人 AI Key
```

```json
{
  "intent": "work_hours_ai_summary",
  "slots": {
    "user_note": "明天优先做什么",
    "context": {
      "period": { "start_date": "2026-08-11", "end_date": "2026-08-14" },
      "filters": { "user_name": "张三" },
      "items": [
        {
          "date": "2026-08-14",
          "task_name": "联调接口",
          "consumed": 8,
          "name": "某项目",
          "sj_num": "SJ20260001",
          "remark": "",
          "task_process": 80,
          "confirm_status_name": "已确认",
          "user_name": "张三"
        }
      ]
    }
  }
}
```

日期缺省约定（前端自己算，不要让 skill 猜）：本周一～今天；用户说「今日」则起止均为当天。

也可传 51PM `ai_assistant` 已聚合的形状：`date` + `tasks` + `projects` + `total_hours`（`hours` 对应 `consumed`）。`items` 与 `tasks` 至少提供一种。

可选 `slots.scope`：`personal` / `department`。不传则按工时明细里出现的人数推断（多于 1 人视为部门）。

**成功：** `data.status === 'ok'`，展示 `data.reply` 或 `data.result.summary`（Markdown）。

输出固定八节：工作概览 / Top5 亮点 / 各项目投入 / 风险与阻塞 / 综合评分 / 改进建议 / 待补充信息 / 行动建议。部门总结须先列成员，每项产出标注真实姓名。无工时则说明「暂无已确认工时」，不编造。
