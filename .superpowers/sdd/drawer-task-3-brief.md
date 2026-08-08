### Task 3: ChatPanel + AiAssistant 壳

**Files:**
- Create: `D:\51pm_new\src\components\ai-assistant\ChatPanel.vue`
- Create: `D:\51pm_new\src\components\ai-assistant\AiAssistant.vue`
- Modify: `D:\51pm_new\.env.development`（及 test/production 占位）

**Interfaces:**
- Consumes: `chat()`, `sessionStore.*`
- Produces: 悬浮钮 + 抽屉；发送消息；展示 reply/meta；快捷示例；新会话按钮

- [ ] **Step 1: 环境变量**

`.env.development` 增加：
```text
VUE_APP_AGENT_API = 'http://127.0.0.1:9000'
```

（按你当前 Agent 端口；其他 mode 文件同样加键，值可先同开发）

- [ ] **Step 2: 实现 ChatPanel.vue**

- props: 无强依赖；内部读/写 sessionStore
- data: `input`, `loading`, `messages`, `agentSessionId`, `showDebug`
- methods: `send`, `onExample`, `newSession`, `applyAssistantPayload(data)`
- template: 消息列表、`el-collapse` 详情、示例 `el-tag`、`el-input` type textarea、发送按钮
- Enter 发送 / Shift+Enter 换行：在 `@keydown.enter.exact.prevent="send"`

助手文案优先级：`data.reply` → 若 `need_slot` 用 reply → 否则 JSON 摘要 status

- [ ] **Step 3: 实现 AiAssistant.vue**

```vue
<template>
  <div class="ai-assistant-root">
    <el-button class="ai-fab" type="primary" circle icon="el-icon-chat-dot-round" @click="visible = true" />
    <el-drawer title="AI 助手" :visible.sync="visible" direction="rtl" size="420px" append-to-body>
      <ChatPanel />
    </el-drawer>
  </div>
</template>
```

FAB `position: fixed; right: 24px; bottom: 24px; z-index: 3000;`

- [ ] **Step 4: 手工冒烟（组件未挂 App 前可用临时页；若已准备挂载则进 Task 4）**

- [ ] **Step 5: Commit** → `feat: add AI assistant drawer UI shell`

---

