### Task 2: sessionStore + agentApi

**Files:**
- Create: `D:\51pm_new\src\components\ai-assistant\sessionStore.js`
- Create: `D:\51pm_new\src\components\ai-assistant\agentApi.js`
- Create: `D:\51pm_new\scripts\verify-session-store.js`（Node 冒烟，不依赖 jest）

**Interfaces:**
- Produces:
  - `STORAGE_KEY = '51pm_ai_assistant_sessions'`
  - `loadState() / saveState(state)`
  - `createSession(title?) -> session`
  - `listSessions() -> sessions sorted by updatedAt desc`
  - `getSession(id) / setCurrent(id) / getCurrent()`
  - `appendMessage(sessionLocalId, message)`
  - `updateSessionAgentId(localId, agentSessionId)`
  - `clearToNewSession() -> session`（新会话）
  - `pruneToMax(20)`
  - `chat({ message, session_id }) -> Promise<data>` 使用 `axios.post(\`${process.env.VUE_APP_AGENT_API}/v1/chat\`, ...)`

- [ ] **Step 1: 写 Node 验证脚本（先红）**

`scripts/verify-session-store.js` 用内存 mock `localStorage`，require/编译前可把 sessionStore 写成不依赖 Vue 的纯函数模块；脚本断言 create/append/prune/list 排序。先故意让断言失败或模块不存在。

- [ ] **Step 2: 实现 sessionStore.js**

```javascript
export const STORAGE_KEY = '51pm_ai_assistant_sessions'
export const MAX_SESSIONS = 20

function uid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

export function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { currentId: null, sessions: [] }
    return JSON.parse(raw)
  } catch (e) {
    return { currentId: null, sessions: [] }
  }
}

export function saveState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

// ... createSession, appendMessage, listSessions, clearToNewSession, pruneToMax
```

- [ ] **Step 3: 实现 agentApi.js**

```javascript
import axios from 'axios'

export function getAgentBase() {
  return (process.env.VUE_APP_AGENT_API || '').replace(/\/$/, '')
}

export function chat({ message, session_id }) {
  const base = getAgentBase()
  if (!base) {
    return Promise.reject(new Error('VUE_APP_AGENT_API is not configured'))
  }
  return axios
    .post(`${base}/v1/chat`, { message, session_id: session_id || undefined })
    .then(res => res.data)
}
```

- [ ] **Step 4: 跑通 verify 脚本**

```bash
cd D:\51pm_new
node scripts/verify-session-store.js
```

Expected: print `OK`

- [ ] **Step 5: Commit**（若 51pm_new 是 git 仓）

```bash
git add src/components/ai-assistant/sessionStore.js src/components/ai-assistant/agentApi.js scripts/verify-session-store.js
git commit -m "feat: add AI assistant session store and agent API client"
```

---

