### Task 4: SessionHistory + 挂载 App.vue

**Files:**
- Create: `D:\51pm_new\src\components\ai-assistant\SessionHistory.vue`
- Modify: `D:\51pm_new\src\components\ai-assistant\AiAssistant.vue` / `ChatPanel.vue`
- Modify: `D:\51pm_new\src\App.vue`

**Interfaces:**
- Consumes: `listSessions`, `setCurrent`, `getSession`
- Produces: 历史列表切换；App 全局可见助手

- [ ] **Step 1: SessionHistory.vue**

- 列表展示 title + 时间
- emit `select(id)`；父级加载消息并关闭历史面板
- 可用 `el-drawer` 内嵌二级面板或 `el-collapse` / 简单列表

- [ ] **Step 2: ChatPanel 顶部「历史」「新会话」**

- 新会话调用 `clearToNewSession()` 并清空视图消息
- 历史打开 SessionHistory；选择后加载 messages 与 agent `session_id`

- [ ] **Step 3: App.vue 挂载**

在 template 中（与 GlobalUpdateNotifier 同级）加入：
```vue
<AiAssistant v-if="isLogin" />
```

```javascript
import AiAssistant from "@/components/ai-assistant/AiAssistant.vue";
components: { ..., AiAssistant }
```

仅登录后显示，避免登录页干扰。

- [ ] **Step 4: 本地跑前端**

```bash
cd D:\51pm_new
npm run serve
```

确认任意业务页有 FAB；能开抽屉。

- [ ] **Step 5: Commit** → `feat: mount AI assistant with local session history`

---

