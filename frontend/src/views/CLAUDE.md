# CLAUDE.md - 前端视图模块 (views)

[根目录](../../../CLAUDE.md) > [frontend](../../) > [src](../) > **views**

> 最后更新: 2026-01-26 12:08:52

---

## 模块职责

前端视图模块负责：
- 页面级组件（路由页面）
- 用户交互界面
- 业务逻辑展示
- 与用户交互的核心UI

---

## 入口与启动

### 主要文件

| 文件 | 职责 |
|------|------|
| [Layout.vue](./Layout.vue) | 主布局（侧边栏、顶部栏） |
| [NotFound.vue](./NotFound.vue) | 404页面 |
| [auth/Login.vue](./auth/Login.vue) | 登录页面 |
| [auth/Register.vue](./auth/Register.vue) | 注册页面 |
| [projects/ProjectList.vue](./projects/ProjectList.vue) | 项目列表页 |
| [projects/ProjectCreate.vue](./projects/ProjectCreate.vue) | 创建项目页 |
| [projects/ProjectDetail.vue](./projects/ProjectDetail.vue) | 项目详情页 |
| [projects/ProjectEdit.vue](./projects/ProjectEdit.vue) | 编辑项目页 |
| [prompts/PromptList.vue](./prompts/PromptList.vue) | 提示词列表页 |
| [prompts/PromptSetForm.vue](./prompts/PromptSetForm.vue) | 提示词集表单 |
| [prompts/PromptSetDetail.vue](./prompts/PromptSetDetail.vue) | 提示词集详情 |
| [prompts/PromptTemplateEditor.vue](./prompts/PromptTemplateEditor.vue) | 提示词编辑器 |
| [prompts/GlobalVariableList.vue](./prompts/GlobalVariableList.vue) | 全局变量管理 |
| [models/ModelList.vue](./models/ModelList.vue) | 模型列表页 |
| [models/ModelForm.vue](./models/ModelForm.vue) | 模型表单页 |

### 路由配置

```javascript
// router/index.js
const routes = [
  {
    path: '/',
    redirect: '/projects',
  },
  // 认证相关
  {
    path: '/login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { requiresGuest: true },
  },
  // 项目管理
  {
    path: '/projects',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        component: () => import('@/views/projects/ProjectList.vue'),
      },
      {
        path: 'create',
        component: () => import('@/views/projects/ProjectCreate.vue'),
      },
      {
        path: ':id',
        component: () => import('@/views/projects/ProjectDetail.vue'),
      },
      {
        path: ':id/edit',
        component: () => import('@/views/projects/ProjectEdit.vue'),
      },
    ],
  },
  // 提示词管理
  {
    path: '/prompts',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        component: () => import('@/views/prompts/PromptList.vue'),
      },
      {
        path: 'sets/create',
        component: () => import('@/views/prompts/PromptSetForm.vue'),
      },
      {
        path: 'sets/:id',
        component: () => import('@/views/prompts/PromptSetDetail.vue'),
      },
      // ...
    ],
  },
  // 模型管理
  {
    path: '/models',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        component: () => import('@/views/models/ModelList.vue'),
      },
      {
        path: 'create',
        component: () => import('@/views/models/ModelForm.vue'),
      },
      {
        path: ':id/edit',
        component: () => import('@/views/models/ModelForm.vue'),
      },
    ],
  },
  // 404页面
  {
    path: '/404',
    component: () => import('@/views/NotFound.vue'),
  },
  {
    path: '*',
    redirect: '/404',
  },
];
```

---

## 对外接口

### 典型页面组件结构

```vue
<template>
  <div class="page-container">
    <!-- 页面内容 -->
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
  name: 'PageName',
  components: { /* ... */ },
  data() {
    return {
      // 本地状态
    };
  },
  computed: {
    ...mapState('moduleName', ['state1', 'state2']),
  },
  methods: {
    ...mapActions('moduleName', ['action1', 'action2']),
    // 本地方法
  },
  mounted() {
    // 初始化逻辑
  },
  beforeDestroy() {
    // 清理逻辑
  },
};
</script>

<style scoped>
/* 样式 */
</style>
```

### 关键页面说明

#### ProjectList.vue（项目列表页）
- 显示所有项目
- 支持筛选、排序
- 快速操作（启动、暂停、删除）

#### ProjectDetail.vue（项目详情页）
- 显示项目完整信息
- 阶段进度展示
- 实时WebSocket连接
- 分镜、图片、视频预览

#### PromptSetForm.vue（提示词集表单）
- 创建/编辑提示词集
- 管理提示词模板
- 变量配置

#### ModelForm.vue（模型表单）
- 添加/编辑模型配置
- 测试模型连接
- 配置负载均衡

---

## 关键依赖与配置

### 依赖的Vuex模块

```javascript
// 各页面依赖的Vuex模块
import { mapState, mapActions } from 'vuex';

computed: {
  ...mapState('projects', ['list', 'current']),
  ...mapState('prompts', ['sets', 'templates']),
  ...mapState('models', ['providers']),
  ...mapState('auth', ['user', 'isAuthenticated']),
},
```

### 依赖的API服务

```javascript
// 各页面依赖的API服务
import api from '@/api/projects';
import promptApi from '@/api/prompts';
import modelApi from '@/api/models';
```

### 依赖的组件

```javascript
// 公共组件
import PageCard from '@/components/common/PageCard.vue';
import StatusBadge from '@/components/common/StatusBadge.vue';
import LoadingContainer from '@/components/common/LoadingContainer.vue';

// 业务组件
import StoryboardViewer from '@/components/content/StoryboardViewer.vue';
import StageContent from '@/components/projects/StageContent.vue';
```

---

## 数据模型

### 页面Props和Events

#### ProjectDetail.vue

```javascript
// Props
props: {
  id: {
    type: String,
    required: true,
  },
},

// Events (emits)
emits: ['project-updated', 'stage-changed'],
```

#### PromptSetForm.vue

```javascript
// Props
props: {
  setId: {
    type: String,
    default: null,
  },
},

// Events
emits: ['saved', 'cancelled'],
```

---

## 测试与质量

### 当前测试覆盖

- ❌ **无单元测试** - 需要添加
- ❌ **无E2E测试** - 需要添加

### 建议的测试文件

```
frontend/src/views/
├── tests/
│   ├── unit/
│   │   ├── ProjectList.test.js      # 项目列表单元测试
│   │   ├── ProjectDetail.test.js    # 项目详情单元测试
│   │   ├── PromptSetForm.test.js    # 提示词表单测试
│   │   └── ModelForm.test.js        # 模型表单测试
│   └── e2e/
│       ├── projects.spec.js         # 项目流程E2E测试
│       ├── prompts.spec.js          # 提示词流程E2E测试
│       └── auth.spec.js             # 认证流程E2E测试
```

### 测试重点

1. **单元测试**
   - 组件渲染是否正确
   - 用户交互是否触发正确的事件
   - Vuex actions是否被调用
   - 路由跳转是否正确

2. **E2E测试**
   - 完整的用户流程（创建项目→启动→查看结果）
   - 跨页面交互
   - WebSocket实时通信

---

## 常见问题 (FAQ)

### Q1: 如何添加新的页面？

**A:** 步骤：
1. 在 `views/` 创建新的 `.vue` 文件
2. 在 `router/index.js` 中添加路由
3. （可选）在侧边栏导航中添加链接

示例：
```javascript
// 1. 创建 views/myPage/MyNewPage.vue
<template>
  <div>我的新页面</div>
</template>

// 2. 添加路由
{
  path: '/my-page',
  component: () => import('@/views/myPage/MyNewPage.vue'),
  meta: { requiresAuth: true },
}
```

### Q2: 如何处理权限控制？

**A:** 使用路由守卫：
```javascript
// router/index.js
router.beforeEach((to, from, next) => {
  const isAuthenticated = store.getters['auth/isAuthenticated'];

  if (to.matched.some(record => record.meta.requiresAuth) && !isAuthenticated) {
    next('/login');
  } else if (to.matched.some(record => record.meta.requiresGuest) && isAuthenticated) {
    next('/projects');
  } else {
    next();
  }
});
```

### Q3: 如何实现实时进度更新？

**A:** 使用WebSocket：
```javascript
// ProjectDetail.vue
import { wsClient } from '@/utils/wsClient';

mounted() {
  // 连接WebSocket
  wsClient.connect(this.projectId);
  wsClient.onMessage((data) => {
    this.$store.commit('projects/UPDATE_STAGE_PROGRESS', data);
  });
},

beforeDestroy() {
  // 断开连接
  wsClient.disconnect();
}
```

### Q4: 如何处理表单验证？

**A:** 使用Vuelidate或手动验证：
```javascript
// 手动验证示例
methods: {
  async submit() {
    // 验证
    if (!this.form.name) {
      this.$message.error('请输入项目名称');
      return;
    }

    // 提交
    try {
      await this.createProject(this.form);
      this.$message.success('创建成功');
      this.$router.push('/projects');
    } catch (error) {
      this.$message.error(error.message);
    }
  },
}
```

---

## 相关文件清单

### 核心文件

```
frontend/src/views/
├── Layout.vue                 # 主布局
├── NotFound.vue               # 404页面
├── auth/
│   ├── Login.vue              # 登录页
│   └── Register.vue           # 注册页
├── projects/
│   ├── ProjectList.vue        # 项目列表
│   ├── ProjectCreate.vue      # 创建项目
│   ├── ProjectDetail.vue      # 项目详情
│   └── ProjectEdit.vue        # 编辑项目
├── prompts/
│   ├── PromptList.vue         # 提示词列表
│   ├── PromptSetForm.vue      # 提示词集表单
│   ├── PromptSetDetail.vue    # 提示词集详情
│   ├── PromptTemplateEditor.vue  # 提示词编辑器
│   └── GlobalVariableList.vue # 全局变量
└── models/
    ├── ModelList.vue          # 模型列表
    └── ModelForm.vue          # 模型表单
```

### 关键依赖

```
# 内部依赖
src/store/                    # Vuex状态管理
src/api/                      # API服务
src/components/               # 公共组件
src/utils/                    # 工具函数
src/router/                   # 路由配置

# 外部依赖
vue                          # Vue框架
vue-router                   # 路由
vuex                         # 状态管理
daisyui + tailwindcss        # UI组件库
```

---

## 变更记录 (Changelog)

### 2026-01-26 12:08:52
- 初始化前端视图模块文档
- 添加导航面包屑
- 完成路由结构、页面说明、测试覆盖分析
