# CLAUDE.md - 前端状态管理模块 (store)

[根目录](../../../CLAUDE.md) > [frontend](../../) > [src](../) > **store**

> 最后更新: 2026-01-26 12:08:52

---

## 模块职责

Vuex状态管理模块负责：
- 管理全局状态（projects、prompts、models、auth、ui）
- 统一API调用（actions）
- 状态派生（getters）
- 模块化状态管理

---

## 入口与启动

### 主要文件

| 文件 | 职责 |
|------|------|
| [index.js](./index.js) | Store入口，导出所有模块 |
| [modules/projects.js](./modules/projects.js) | 项目状态管理 |
| [modules/prompts.js](./modules/prompts.js) | 提示词状态管理 |
| [modules/models.js](./modules/models.js) | 模型状态管理 |
| [modules/auth.js](./modules/auth.js) | 用户认证状态 |
| [modules/content.js](./modules/content.js) | 内容状态管理 |
| [modules/ui.js](./modules/ui.js) | UI状态（loading、sidebar等） |

### Store 结构

```javascript
// store/index.js
import Vue from 'vue';
import Vuex from 'vuex';
import projects from './modules/projects';
import prompts from './modules/prompts';
import models from './modules/models';
import auth from './modules/auth';
import content from './modules/content';
import ui from './modules/ui';

Vue.use(Vuex);

export default new Vuex.Store({
  modules: {
    projects,
    prompts,
    models,
    auth,
    content,
    ui,
  },
});
```

---

## 对外接口

### State 结构

```javascript
{
  // 项目模块
  projects: {
    list: [],              // 项目列表
    current: null,         // 当前项目
    loading: false,
    error: null,
  },

  // 提示词模块
  prompts: {
    sets: [],              // 提示词集列表
    templates: [],         // 提示词模板列表
    globalVariables: [],   // 全局变量
    currentSet: null,      // 当前提示词集
  },

  // 模型模块
  models: {
    providers: [],         // 模型提供商列表
    currentProvider: null, // 当前模型
  },

  // 认证模块
  auth: {
    token: localStorage.getItem('token'),
    user: null,
    isAuthenticated: !!localStorage.getItem('token'),
  },

  // 内容模块
  content: {
    storyboards: [],       // 分镜列表
    images: [],            // 图片列表
    videos: [],            // 视频列表
  },

  // UI模块
  ui: {
    sidebarOpen: true,     // 侧边栏状态
    loading: false,        // 全局loading
  },
}
```

### 典型模块结构（以 projects 为例）

```javascript
// store/modules/projects.js

const state = {
  list: [],
  current: null,
  loading: false,
  error: null,
};

const getters = {
  projectList: (state) => state.list,
  currentProject: (state) => state.current,
  isLoading: (state) => state.loading,
};

const mutations = {
  SET_PROJECTS(state, projects) {
    state.list = projects;
  },
  SET_CURRENT_PROJECT(state, project) {
    state.current = project;
  },
  SET_LOADING(state, loading) {
    state.loading = loading;
  },
};

const actions = {
  async fetchProjects({ commit }) {
    commit('SET_LOADING', true);
    try {
      const response = await api.getProjects();
      commit('SET_PROJECTS', response.data);
    } catch (error) {
      commit('SET_ERROR', error.message);
    } finally {
      commit('SET_LOADING', false);
    }
  },
};

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions,
};
```

---

## 关键依赖与配置

### 依赖的API服务

```javascript
// 各模块依赖的API服务
import api from '@/api/projects';
import promptApi from '@/api/prompts';
import modelApi from '@/api/models';
```

### 在组件中使用

```javascript
// 在 Vue 组件中使用
import { mapState, mapGetters, mapActions } from 'vuex';

export default {
  computed: {
    ...mapState('projects', ['list', 'loading']),
    ...mapGetters('projects', ['currentProject']),
  },
  methods: {
    ...mapActions('projects', ['fetchProjects', 'createProject']),
  },
  mounted() {
    this.fetchProjects();
  },
};
```

---

## 数据模型

### State 数据结构

#### projects 模块

```javascript
{
  list: [
    {
      id: 'uuid',
      name: '项目名称',
      description: '描述',
      status: 'processing',  // draft/processing/completed/failed/paused
      original_topic: '主题',
      created_at: '2026-01-26T12:08:52Z',
      updated_at: '2026-01-26T12:08:52Z',
      stages: [
        {
          stage_type: 'rewrite',
          status: 'completed',
          progress: 100,
        },
        // ...
      ],
    },
  ],
  current: { /* 同上 */ },
  loading: false,
  error: null,
}
```

#### prompts 模块

```javascript
{
  sets: [
    {
      id: 'uuid',
      name: '提示词集名称',
      description: '描述',
      is_active: true,
      is_default: false,
      templates: [
        {
          id: 'uuid',
          stage_type: 'rewrite',
          template_content: '...',
          variables: {},
        },
      ],
    },
  ],
  globalVariables: [
    {
      id: 'uuid',
      name: '主题',
      key: 'topic',
      default_value: '',
      variable_type: 'text',
    },
  ],
}
```

---

## 测试与质量

### 当前测试覆盖

- ❌ **无单元测试** - 需要添加

### 建议的测试文件

```
frontend/src/store/
├── tests/
│   ├── __init__.js
│   ├── modules/
│   │   ├── projects.test.js      # 项目模块测试
│   │   ├── prompts.test.js       # 提示词模块测试
│   │   ├── models.test.js        # 模型模块测试
│   │   └── auth.test.js          # 认证模块测试
│   └── index.test.js             # Store入口测试
```

### 测试重点

1. **Actions 测试**
   - API调用是否正确
   - mutation 是否被提交
   - 错误处理是否正确

2. **Getters 测试**
   - 派生状态是否正确
   - 缓存是否有效

3. **Mutations 测试**
   - 状态修改是否正确
   - 副作用是否避免

---

## 常见问题 (FAQ)

### Q1: 如何添加新的状态模块？

**A:** 步骤：
1. 在 `store/modules/` 创建新文件
2. 导出 state, getters, mutations, actions
3. 在 `store/index.js` 中注册

示例：
```javascript
// store/modules/myModule.js
export default {
  namespaced: true,
  state: { /* ... */ },
  getters: { /* ... */ },
  mutations: { /* ... */ },
  actions: { /* ... */ },
};

// store/index.js
import myModule from './modules/myModule';

export default new Vuex.Store({
  modules: {
    // ...
    myModule,
  },
});
```

### Q2: 如何在组件中使用模块状态？

**A:** 使用命名空间：
```javascript
computed: {
  ...mapState('myModule', ['data1', 'data2']),
  ...mapGetters('myModule', ['computedData']),
},
methods: {
  ...mapActions('myModule', ['action1', 'action2']),
}
```

### Q3: 如何处理异步错误？

**A:** 在 actions 中使用 try-catch：
```javascript
async myAction({ commit }) {
  commit('SET_LOADING', true);
  try {
    const response = await api.getData();
    commit('SET_DATA', response.data);
  } catch (error) {
    commit('SET_ERROR', error.message);
    throw error;  // 重新抛出供组件处理
  } finally {
    commit('SET_LOADING', false);
  }
}
```

### Q4: 如何持久化状态？

**A:** 使用 vuex-persistedstate：
```javascript
import createPersistedState from 'vuex-persistedstate';

export default new Vuex.Store({
  plugins: [
    createPersistedState({
      key: 'ai-story',
      paths: ['auth.token', 'ui.sidebarOpen'],  // 指定要持久化的路径
    }),
  ],
  // ...
});
```

---

## 相关文件清单

### 核心文件

```
frontend/src/store/
├── index.js                   # Store入口
└── modules/
    ├── projects.js            # 项目模块
    ├── prompts.js             # 提示词模块
    ├── models.js              # 模型模块
    ├── auth.js                # 认证模块
    ├── content.js             # 内容模块
    └── ui.js                  # UI模块
```

### 关键依赖

```
# 内部依赖
src/api/                      # API服务封装
src/utils/                    # 工具函数

# 外部依赖
vuex                          # 状态管理库
vuex-persistedstate           # 状态持久化（可选）
```

---

## 变更记录 (Changelog)

### 2026-01-26 12:08:52
- 初始化前端状态管理模块文档
- 添加导航面包屑
- 完成模块结构、接口、测试覆盖分析
