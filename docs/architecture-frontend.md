# Frontend 架构文档

**生成时间:** 2026-01-26T12:24:00Z
**项目部分:** frontend
**技术栈:** Vue 2.7.14 + Vuex + daisyUI + Tailwind CSS

---

## 执行摘要

Frontend 采用**组件化架构**结合**集中式状态管理**,使用 Vue 2 生态系统构建现代化的单页应用。

**核心特性:**
- 组件化架构: 可复用 UI 组件库
- 集中式状态管理: Vuex Store
- 路由管理: Vue Router
- API 服务层: Axios HTTP 客户端
- 实时通信: Socket.IO WebSocket 客户端
- 原子化 CSS: Tailwind CSS + daisyUI

---

## 技术栈

### 核心框架

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue.js | 2.7.14 | 前端框架 |
| Vuex | 3.6.2 | 状态管理 |
| Vue Router | 3.6.5 | 客户端路由 |
| Axios | 1.6.2 | HTTP 客户端 |
| Socket.IO Client | 4.6.1 | WebSocket 客户端 |

### UI 框架

| 技术 | 版本 | 用途 |
|------|------|------|
| Tailwind CSS | 3.4.17 | 原子化 CSS 框架 |
| daisyUI | 4.12.23 | 组件库 |
| PostCSS | 8.4.32 | CSS 转换 |

### 构建工具

| 技术 | 版本 | 用途 |
|------|------|------|
| Webpack | 5.89.0 | 模块打包 |
| Babel | 7.23.5 | JavaScript 转译 |
| ESLint | 8.55.0 | 代码检查 |

### 架构模式

**组件化架构 (Component-Based Architecture)**

```
┌─────────────────────────────────────────┐
│  视图层 (Views)                         │
│  - 页面级组件                            │
│  - 路由组件                              │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  组件层 (Components)                     │
│  - 可复用 UI 组件                        │
│  - 业务组件                              │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  状态管理 (Vuex)                         │
│  - 集中式状态                            │
│  - 模块化 Store                          │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  路由 (Vue Router)                      │
│  - 路由配置                              │
│  - 导航守卫                              │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  服务层 (Services)                       │
│  - API 客户端                            │
│  - WebSocket 连接                        │
└─────────────────────────────────────────┘
```

---

## 状态管理

### Vuex Store 结构

**位置:** `src/store/`

**模块划分:**
- `projects.js` - 项目状态模块
- `prompts.js` - 提示词状态模块
- `models.js` - 模型状态模块
- `user.js` - 用户状态模块

**状态示例 (projects 模块):**
```javascript
state: {
  projects: [],
  currentProject: null,
  loading: false,
  error: null
}

actions: {
  async fetchProjects({ commit }) {
    commit('SET_LOADING', true)
    const projects = await api.projects.list()
    commit('SET_PROJECTS', projects)
    commit('SET_LOADING', false)
  }
}

mutations: {
  SET_PROJECTS(state, projects) {
    state.projects = projects
  }
}
```

---

## 组件概览

### 页面视图组件 (Views)

**位置:** `src/views/`

**主要页面:**
- `projects/ProjectList.vue` - 项目列表页
- `projects/ProjectDetail.vue` - 项目详情页
- `projects/StageContent.vue` - 阶段内容组件
- `prompts/` - 提示词管理页面
- `models/` - 模型管理页面

### 可复用组件 (Components)

**位置:** `src/components/`

**组件分类:**
- `common/` - 通用组件 (Button, Input, Modal 等)
- `project/` - 项目相关组件
- `prompt/` - 提示词相关组件

---

## 路由设计

### 路由配置

**位置:** `src/router/index.js`

**主要路由:**
```javascript
const routes = [
  {
    path: '/projects',
    name: 'ProjectList',
    component: () => import('@/views/projects/ProjectList.vue')
  },
  {
    path: '/projects/:id',
    name: 'ProjectDetail',
    component: () => import('@/views/projects/ProjectDetail.vue')
  },
  {
    path: '/prompts',
    name: 'PromptList',
    component: () => import('@/views/prompts/PromptList.vue')
  }
]
```

### 导航守卫

- 路由前置守卫 (检查认证)
- 权限验证

---

## API 服务层

### API 客户端配置

**位置:** `src/services/api/client.js`

**Axios 实例:**
```javascript
import axios from 'axios'

const client = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:8000/api/v1/',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getToken()}`
  }
})

// 请求拦截器
client.interceptors.request.use(config => {
  // 添加 token
  return config
})

// 响应拦截器
client.interceptors.response.use(
  response => response,
  error => {
    // 错误处理
    return Promise.reject(error)
  }
)
```

### API 服务模块

**位置:** `src/services/api/`

**服务模块:**
- `projects.js` - 项目 API
- `prompts.js` - 提示词 API
- `models.js` - 模型 API
- `content.js` - 内容 API

**使用示例:**
```javascript
import api from '@/services/api/projects'

// 获取项目列表
const projects = await api.list()

// 创建项目
const project = await api.create({ name: 'My Project' })

// 执行阶段
await api.executeStage(projectId, { stage_name: 'rewrite' })
```

---

## WebSocket 集成

### Socket.IO 客户端

**位置:** `src/utils/websocket.js`

**连接管理:**
```javascript
import io from 'socket.io-client'

class WebSocketClient {
  constructor(projectId) {
    this.socket = io(`ws://localhost:8000/ws/projects/${projectId}/`)
    this.setupListeners()
  }

  setupListeners() {
    this.socket.on('stage_update', (data) => {
      // 处理阶段更新
      console.log('Stage update:', data)
    })

    this.socket.on('task_progress', (data) => {
      // 处理任务进度
      console.log('Task progress:', data)
    })
  }

  disconnect() {
    this.socket.disconnect()
  }
}
```

**在 Vue 组件中使用:**
```javascript
import WebSocketClient from '@/utils/websocket'

export default {
  data() {
    return {
      wsClient: null
    }
  },
  mounted() {
    this.wsClient = new WebSocketClient(this.projectId)
  },
  beforeDestroy() {
    this.wsClient?.disconnect()
  }
}
```

---

## 开发工作流

### 开发环境设置

```bash
# 1. 安装依赖
cd frontend
npm install

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 启动开发服务器
npm run dev

# 应用将在 http://localhost:3000 启动
```

### 开发命令

```bash
# 开发服务器
npm run dev

# 生产构建
npm run build

# 代码检查
npm run lint

# 修复代码
npm run lint:fix
```

### 代码规范

**ESLint 配置:**
- `.eslintrc.js` - ESLint 规则
- `eslint-plugin-vue` - Vue.js 插件

**Babel 配置:**
- `.babelrc.js` - Babel 转译配置

---

## 部署架构

### 生产构建

```bash
# 构建生产版本
npm run build

# 输出目录: dist/
```

### Nginx 配置

```nginx
server {
  listen 80;
  server_name example.com;

  root /var/www/frontend/dist;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location /api/ {
    proxy_pass http://backend:8000;
  }
}
```

### 环境变量

```bash
# .env.production
VUE_APP_API_URL=https://api.example.com/api/v1/
VUE_APP_WS_URL=wss://api.example.com/ws/
```

---

## UI 组件库

### Tailwind CSS

**配置:** `tailwind.config.js`

**使用示例:**
```vue
<template>
  <div class="bg-blue-500 text-white p-4 rounded">
    Hello, Tailwind!
  </div>
</template>
```

### daisyUI

**主题配置:**
```javascript
// tailwind.config.js
daisyui: {
  themes: ['light', 'dark', 'cupcake'],
  darkTheme: 'dark'
}
```

**组件示例:**
```vue
<template>
  <button class="btn btn-primary">Primary Button</button>
  <input type="text" class="input input-bordered" />
  <div class="alert alert-info">Info message</div>
</template>
```

---

## 性能优化

### 代码分割

```javascript
// 路由懒加载
const ProjectDetail = () => import('@/views/projects/ProjectDetail.vue')
```

### Vuex 模块化

```javascript
// 动态注册模块
store.registerModule('projects', projectsModule)
```

### Axios 缓存

```javascript
// 响应缓存
const cache = new Map()

async function getCachedData(url) {
  if (cache.has(url)) {
    return cache.get(url)
  }
  const data = await api.get(url)
  cache.set(url, data)
  return data
}
```

---

## 测试策略

### 单元测试

**推荐工具:**
- Jest - 测试框架
- Vue Test Utils - Vue 组件测试
- Vue Router - 路由测试

**示例:**
```javascript
import { mount } from '@vue/test-utils'
import ProjectList from '@/views/projects/ProjectList.vue'

test('renders project list', () => {
  const wrapper = mount(ProjectList)
  expect(wrapper.find('.project-list').exists()).toBe(true)
})
```

### E2E 测试

**推荐工具:**
- Cypress
- Playwright

---

## 相关文档

- [组件清单](./component-inventory.md) _(To be generated)_
- [API 契约 - Backend](./api-contracts-backend.md) _(To be generated)_
- [集成架构](./integration-architecture.md) _(To be generated)_

---

## 现有文档

- [Frontend README](../frontend/README.md)
- [Frontend 迁移指南](../frontend/FRONTEND_MIGRATION_GUIDE.md)
- [SSE 集成](../frontend/SSE_INTEGRATION.md)

---

**生成信息:**
- 扫描模式: Deep Scan
- 生成时间: 2026-01-26T12:24:00Z
