---
project: AI Story Generation System
documentType: UX Design Specification
version: 1.0
created: 2026-01-27
focus: Core Pages and Components (P0 - Implementation Ready)
---

# AI Story - UX设计规范

**项目:** AI Story Generation System
**文档类型:** UX设计规范(P0核心)
**创建日期:** 2026-01-27
**技术栈:** Vue 2.7.14 + daisyUI + Tailwind CSS

---

## 设计目标

根据实施就绪评估报告的建议,本文档提供:

### P0范围 (本次实施)
- ✅ 核心页面线框图:项目列表页、项目详情页
- ✅ 关键组件规范:进度条、控制按钮、文件预览
- ✅ 实时进度更新UI实现

### P1范围 (后续实施)
- UI组件库建立
- 响应式断点定义
- 前端代码规范

### P2范围 (优化阶段)
- 动画和过渡效果
- 无障碍访问支持
- UI/UX迭代优化

---

## 1. 设计系统基础

### 1.1 颜色规范

基于daisyUI主题配色:

```css
/* 主色调 - Primary */
--primary: #3b82f6; /* blue-500 */
--primary-focus: #2563eb; /* blue-600 */

/* 成功色 - Success */
--success: #22c55e; /* green-500 */
--success-focus: #16a34a; /* green-600 */

/* 警告色 - Warning */
--warning: #eab308; /* yellow-500 */
--warning-focus: #ca8a04; /* yellow-600 */

/* 错误色 - Error */
--error: #ef4444; /* red-500 */
--error-focus: #dc2626; /* red-600 */

/* 中性色 - Neutral */
--neutral: #404040; /* gray-700 */
--neutral-focus: #262626; /* gray-800 */

/* 背景色 */
--bg-base: #ffffff;
--bg-alt: #f3f4f6; /* gray-100 */

/* 文字色 */
--text-base: #1f2937; /* gray-800 */
--text-muted: #6b7280; /* gray-500 */
```

### 1.2 字体规范

```css
/* 字体家族 */
font-family: 'Inter', system-ui, -apple-system, sans-serif;

/* 字体大小 */
--text-xs: 0.75rem;   /* 12px */
--text-sm: 0.875rem;  /* 14px */
--text-base: 1rem;    /* 16px */
--text-lg: 1.125rem;  /* 18px */
--text-xl: 1.25rem;   /* 20px */
--text-2xl: 1.5rem;   /* 24px */
--text-3xl: 1.875rem; /* 30px */

/* 字重 */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### 1.3 间距规范

基于Tailwind CSS间距系统:

```css
/* 间距单位 */
--spacing-1: 0.25rem;  /* 4px */
--spacing-2: 0.5rem;   /* 8px */
--spacing-3: 0.75rem;  /* 12px */
--spacing-4: 1rem;     /* 16px */
--spacing-6: 1.5rem;   /* 24px */
--spacing-8: 2rem;     /* 32px */
```

---

## 2. 核心页面设计

### 2.1 页面布局结构

```
┌─────────────────────────────────────────┐
│  Navbar (固定顶部)                       │
│  Logo | 项目列表 | 新建项目             │
├─────────────────────────────────────────┤
│                                         │
│  Main Content (可滚动区域)               │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 项目列表 / 项目详情内容          │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
├─────────────────────────────────────────┤
│  Footer (可选)                           │
│  © 2026 AI Story                        │
└─────────────────────────────────────────┘
```

### 2.2 项目列表页 (Project List Page)

**路由:** `/projects`
**功能:** 展示所有项目,支持创建新项目

#### 页面线框图

```
┌────────────────────────────────────────────────────────┐
│  🎬 AI Story              [+ 新建项目]                 │
├────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 📂 萌猫日常                                        │  │
│  │ 状态: 进行中 | 进度: 45%                          │  │
│  │ 创建: 2026-01-27 | 更新: 2小时前                 │  │
│  │ [▶ 继续] [🗑 删除]                               │  │
│  └─────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 📂 汪星人成长记                                    │  │
│  │ 状态: 已完成 | 进度: 100%                         │  │
│  │ 创建: 2026-01-25 | 更新: 1天前                   │  │
│  │ [▶ 查看] [🗑 删除]                               │  │
│  └─────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 📂 美食制作教程                                    │  │
│  │ 状态: 失败 | 进度: 30% (文案改写失败)              │  │
│  │ 创建: 2026-01-24 | 更新: 3天前                   │  │
│  │ [🔄 重试] [🗑 删除]                              │  │
│  └─────────────────────────────────────────────────┘  │
│                                                          │
└────────────────────────────────────────────────────────┘
```

#### 项目卡片组件规范

**组件名:** `ProjectCard`

**布局:**
```html
<div class="card bg-base-100 shadow-md hover:shadow-lg transition">
  <!-- 卡片头部 -->
  <div class="card-body p-4">
    <div class="flex items-start justify-between">
      <div>
        <h2 class="card-title text-lg font-semibold">
          <span class="text-2xl mr-2">📂</span>
          {{ project.name }}
        </h2>
        <p class="text-sm text-muted mt-1">
          状态: <span class="badge badge-{{ statusColor }}">{{ statusText }}</span>
        </p>
      </div>
      <progress class="progress w-24" value="{{ progress }}" max="100"></progress>
    </div>

    <!-- 元数据 -->
    <div class="text-xs text-muted mt-2">
      <span>创建: {{ createdAt }}</span>
      <span class="mx-2">|</span>
      <span>更新: {{ updatedAt }}</span>
    </div>

    <!-- 操作按钮 -->
    <div class="card-actions justify-end mt-4">
      <button class="btn btn-primary btn-sm">{{ primaryAction }}</button>
      <button class="btn btn-ghost btn-sm text-error">🗑 删除</button>
    </div>
  </div>
</div>
```

**状态映射:**
- `pending` → 灰色 (badge-neutral)
- `processing` → 蓝色 (badge-primary)
- `completed` → 绿色 (badge-success)
- `failed` → 红色 (badge-error)

**按钮文本映射:**
- `processing` → "▶ 继续"
- `completed` → "▶ 查看"
- `failed` → "🔄 重试"

#### 新建项目按钮

```html
<button class="btn btn-primary">
  <span class="text-xl mr-1">+</span>
  新建项目
</button>
```

**弹窗表单:**
```html
<div class="modal">
  <div class="modal-box">
    <h3 class="font-bold text-lg">新建项目</h3>

    <form class="py-4 space-y-4">
      <!-- 项目名称 -->
      <div class="form-control">
        <label class="label"><span class="label-text">项目名称</span></label>
        <input type="text" placeholder="例如: 萌猫日常" class="input input-bordered" />
      </div>

      <!-- 故事主题 -->
      <div class="form-control">
        <label class="label"><span class="label-text">故事主题</span></label>
        <textarea class="textarea textarea-bordered h-24"
                  placeholder="描述你的故事主题..."></textarea>
      </div>

      <!-- 视频风格 -->
      <div class="form-control">
        <label class="label"><span class="label-text">视频风格</span></label>
        <select class="select select-bordered">
          <option>可爱搞笑风</option>
          <option>科技未来风</option>
          <option>温馨治愈风</option>
        </select>
      </div>

      <!-- 操作按钮 -->
      <div class="modal-action">
        <button type="submit" class="btn btn-primary">创建项目</button>
        <button type="button" class="btn">取消</button>
      </div>
    </form>
  </div>
</div>
```

### 2.3 项目详情页 (Project Detail Page)

**路由:** `/projects/:id`
**功能:** 展示项目详情、实时进度、生成内容

#### 页面线框图

```
┌────────────────────────────────────────────────────────┐
│  ← 返回 | 📂 萌猫日常                    [✏ 编辑] [🗑 删除]│
├────────────────────────────────────────────────────────┤
│                                                          │
│  项目信息                                               │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 故事主题: 一只橘猫在客厅追逐激光笔...            │  │
│  │ 视频风格: 可爱搞笑风                             │  │
│  │ 创建时间: 2026-01-27 14:30                       │  │
│  └─────────────────────────────────────────────────┘  │
│                                                          │
│  进度监控 (实时更新)                                    │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 总体进度: ███████░░░░░░░░░░░ 45%                  │  │
│  │ 当前阶段: 分镜生成 (Stage 2/5)                   │  │
│  │ 预计剩余: 3-5分钟                                 │  │
│  │                                                  │  │
│  │ 阶段详情:                                        │  │
│  │ ✅ 1. 文案改写 (100%) - 完成                     │  │
│  │ 🔄 2. 分镜生成 (60%) - 进行中...                 │  │
│  │ ⏸ 3. 文生图 (0%) - 等待中                       │  │
│  │ ⏸ 4. 运镜生成 (0%) - 等待中                      │  │
│  │ ⏸ 5. 图生视频 (0%) - 等待中                     │  │
│  │                                                  │  │
│  │ [⏸ 暂停] [🔄 重试阶段] [▶ 继续工作流]            │  │
│  └─────────────────────────────────────────────────┘  │
│                                                          │
│  生成内容                                               │
│  ┌─────────────────────────────────────────────────┐  │
│  │ 文案内容                                         │  │
│  │ "在一个阳光明媚的下午,一只名叫橘子的橘猫..."     │  │
│  │                                                  │  │
│  │ 分镜 (5个场景)                                   │  │
│  │ [场景1] [场景2] [场景3] [场景4] [场景5]          │  │
│  │                                                  │  │
│  │ 图片预览 (3/5完成)                               │  │
│  │ [图1] [图2] [图3] [⏳] [⏳]                      │  │
│  └─────────────────────────────────────────────────┘  │
│                                                          │
└────────────────────────────────────────────────────────┘
```

#### 进度条组件规范

**组件名:** `StageProgressBar`

**实现:**
```html
<!-- 总体进度条 -->
<div class="w-full bg-neutral rounded-full h-4">
  <div class="bg-primary h-4 rounded-full"
       style="width: {{ progress }}%">
    <span class="text-xs text-white font-bold pl-2">{{ progress }}%</span>
  </div>
</div>

<!-- 当前阶段指示器 -->
<div class="flex items-center justify-between mt-2">
  <span class="text-sm text-muted">当前阶段: {{ currentStage }}</span>
  <span class="text-sm font-medium">{{ progress }}%</span>
</div>
```

**颜色状态:**
- `pending` → 灰色 (bg-neutral)
- `processing` → 蓝色 (bg-primary,带动画)
- `completed` → 绿色 (bg-success)
- `failed` → 红色 (bg-error)

**动画效果:**
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.progress-bar.processing {
  animation: pulse 2s ease-in-out infinite;
}
```

#### 阶段列表组件

**组件名:** `StageList`

```html
<div class="space-y-2">
  <!-- 已完成阶段 -->
  <div class="flex items-center p-3 bg-success/10 rounded-lg border border-success/20">
    <span class="text-success text-xl mr-3">✅</span>
    <div class="flex-1">
      <div class="font-medium">1. 文案改写</div>
      <div class="text-xs text-muted">完成于 14:35</div>
    </div>
    <span class="badge badge-success">100%</span>
  </div>

  <!-- 进行中阶段 -->
  <div class="flex items-center p-3 bg-primary/10 rounded-lg border border-primary/20">
    <span class="text-primary text-xl mr-3 animate-spin">🔄</span>
    <div class="flex-1">
      <div class="font-medium">2. 分镜生成</div>
      <div class="text-xs text-muted">预计剩余 2-3分钟</div>
      <progress class="progress w-full mt-2" value="60" max="100"></progress>
    </div>
    <span class="badge badge-primary">60%</span>
  </div>

  <!-- 等待中阶段 -->
  <div class="flex items-center p-3 bg-neutral/10 rounded-lg border border-neutral/20">
    <span class="text-muted text-xl mr-3">⏸</span>
    <div class="flex-1">
      <div class="font-medium text-muted">3. 文生图</div>
      <div class="text-xs text-muted">等待上一阶段完成</div>
    </div>
    <span class="badge badge-neutral">0%</span>
  </div>
</div>
```

#### 控制按钮组

**组件名:** `WorkflowControls`

```html
<div class="flex gap-2">
  <!-- 暂停按钮 -->
  <button class="btn btn-warning btn-sm">
    <span class="mr-1">⏸</span>
    暂停
  </button>

  <!-- 重试按钮 (仅失败阶段显示) -->
  <button class="btn btn-error btn-sm">
    <span class="mr-1">🔄</span>
    重试阶段
  </button>

  <!-- 继续按钮 -->
  <button class="btn btn-success btn-sm">
    <span class="mr-1">▶</span>
    继续工作流
  </button>

  <!-- 单个阶段重试 -->
  <button class="btn btn-ghost btn-sm">
    🔄 重新生成此阶段
  </button>
</div>
```

---

## 3. 关键组件规范

### 3.1 实时进度条组件

**组件名:** `RealTimeProgressBar`

**功能:** 显示WebSocket实时推送的进度更新

**Props:**
```javascript
{
  projectId: String,
  stage: String,        // 当前阶段名称
  progress: Number,     // 0-100
  status: String,       // pending/processing/completed/failed
  estimatedTime: Number // 预计剩余时间(秒)
}
```

**实现:**
```vue
<template>
  <div class="real-time-progress">
    <!-- 总体进度 -->
    <div class="mb-2">
      <div class="flex justify-between text-sm mb-1">
        <span class="font-medium">{{ stage }}</span>
        <span class="text-muted">{{ progress }}%</span>
      </div>
      <div class="w-full bg-neutral rounded-full h-3">
        <div class="bg-primary h-3 rounded-full transition-all duration-300"
             :class="{ 'animate-pulse': status === 'processing' }"
             :style="{ width: progress + '%' }">
        </div>
      </div>
    </div>

    <!-- 预计剩余时间 -->
    <div v-if="status === 'processing'" class="text-xs text-muted">
      预计剩余: {{ formatTime(estimatedTime) }}
    </div>

    <!-- 状态指示器 -->
    <div class="mt-2">
      <span v-if="status === 'completed'" class="badge badge-success">
        ✅ 完成
      </span>
      <span v-else-if="status === 'failed'" class="badge badge-error">
        ❌ 失败
      </span>
      <span v-else-if="status === 'processing'" class="badge badge-primary">
        🔄 进行中
      </span>
      <span v-else class="badge badge-neutral">
        ⏸ 等待中
      </span>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    formatTime(seconds) {
      if (seconds < 60) return `${seconds}秒`;
      const minutes = Math.floor(seconds / 60);
      return `${minutes}分钟`;
    }
  }
}
</script>
```

**WebSocket集成:**
```javascript
// 在Vuex store中
const actions = {
  connectToProject({ commit }, projectId) {
    const ws = new WebSocket(`ws://localhost:8000/ws/projects/${projectId}/`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'progress_update') {
        commit('UPDATE_PROGRESS', {
          stage: data.stage,
          progress: data.progress,
          status: data.status,
          estimatedTime: data.estimatedTime
        });
      }
    };

    commit('SET_WEBSOCKET', ws);
  }
}
```

### 3.2 文件预览组件

**组件名:** `FilePreview`

**功能:** 预览生成的图片和视频

**图片预览:**
```vue
<template>
  <div class="file-preview-grid">
    <div v-for="(file, index) in files" :key="index"
         class="card bg-base-100 shadow-md">
      <figure class="px-4 pt-4">
        <img :src="file.url"
             :alt="file.name"
             class="rounded-lg h-48 w-full object-cover" />
      </figure>
      <div class="card-body p-4">
        <h3 class="card-title text-sm">{{ file.name }}</h3>
        <p class="text-xs text-muted">
          {{ formatFileSize(file.size) }}
        </p>
        <div class="card-actions justify-end">
          <button @click="preview(file)" class="btn btn-primary btn-sm">
            👁 预览
          </button>
          <button @click="download(file)" class="btn btn-ghost btn-sm">
            ⬇ 下载
          </button>
          <button @click="regenerate(index)" class="btn btn-ghost btn-sm">
            🔄 重新生成
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
```

**视频预览:**
```vue
<template>
  <div class="video-preview">
    <video controls class="w-full rounded-lg">
      <source :src="videoUrl" type="video/mp4">
      您的浏览器不支持视频播放。
    </video>

    <div class="flex justify-between mt-4">
      <div class="text-sm">
        <span class="font-medium">时长:</span> {{ video.duration }}
      </div>
      <div class="text-sm">
        <span class="font-medium">大小:</span> {{ formatFileSize(video.size) }}
      </div>
    </div>

    <div class="flex gap-2 mt-4">
      <button @click="download" class="btn btn-primary btn-sm">
        ⬇ 下载视频
      </button>
      <button @click="share" class="btn btn-ghost btn-sm">
        📤 分享
      </button>
    </div>
  </div>
</template>
```

### 3.3 错误提示组件

**组件名:** `ErrorMessage`

**功能:** 显示友好的错误信息

```vue
<template>
  <div v-if="show" class="alert alert-error">
    <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <span>
      <strong>错误!</strong> {{ message }}
    </span>
    <button @click="retry" class="btn btn-sm btn-error ml-4">
      🔄 重试
    </button>
  </div>
</template>
```

**错误消息映射:**
```javascript
const errorMessages = {
  'WEBSOCKET_DISCONNECTED': 'WebSocket连接断开,正在尝试重连...',
  'AI_API_TIMEOUT': 'AI API调用超时,请稍后重试',
  'TASK_FAILED': '任务执行失败,请检查日志或重试',
  'NETWORK_ERROR': '网络连接失败,请检查网络设置'
};
```

---

## 4. 响应式设计 (P1)

### 4.1 断点定义

```css
/* Tailwind默认断点 */
sm: 640px   /* 手机横屏 */
md: 768px   /* 平板 */
lg: 1024px  /* 桌面(默认) */
xl: 1280px  /* 大桌面 */
```

### 4.2 响应式布局示例

**项目列表页:**
```html
<!-- 桌面: 3列 -->
<!-- 平板: 2列 -->
<!-- 手机: 1列 -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <ProjectCard v-for="project in projects" :key="project.id" />
</div>
```

---

## 5. 实施建议

### 5.1 组件开发优先级

**P0 - 立即实施 (Phase 1):**
1. `ProjectCard` - 项目卡片
2. `StageProgressBar` - 进度条
3. `RealTimeProgressBar` - 实时进度(含WebSocket)
4. `ErrorMessage` - 错误提示

**P1 - Phase 2:**
1. `FilePreview` - 文件预览
2. `WorkflowControls` - 控制按钮组
3. `StageList` - 阶段列表

### 5.2 Vuex Store结构

```javascript
// store/modules/projects.js
const state = {
  projects: [],
  currentProject: null,
  progress: {
    stage: '',
    progress: 0,
    status: 'pending',
    estimatedTime: 0
  },
  websocket: null
};

const mutations = {
  UPDATE_PROGRESS(state, payload) {
    state.progress = { ...state.progress, ...payload };
  },
  SET_WEBSOCKET(state, ws) {
    state.websocket = ws;
  }
};

const actions = {
  async fetchProjects({ commit }) {
    // API调用
  },
  connectToProject({ commit, dispatch }, projectId) {
    // WebSocket连接
  }
};
```

### 5.3 API集成

**项目列表:**
```javascript
// api/projects.js
export const fetchProjects = () => {
  return axios.get('/api/v1/projects/');
};

export const createProject = (data) => {
  return axios.post('/api/v1/projects/', data);
};

export const deleteProject = (id) => {
  return axios.delete(`/api/v1/projects/${id}/`);
};
```

**进度查询:**
```javascript
export const fetchProgress = (projectId) => {
  return axios.get(`/api/v1/projects/${projectId}/progress/`);
};
```

---

## 6. 下一步行动

### P0 - 立即开始 (本次实施)
1. ✅ 创建核心页面Vue组件:
   - `ProjectList.vue`
   - `ProjectDetail.vue`

2. ✅ 创建关键UI组件:
   - `ProjectCard.vue`
   - `StageProgressBar.vue`
   - `RealTimeProgressBar.vue`
   - `ErrorMessage.vue`

3. ✅ 设置Vuex store:
   - `store/modules/projects.js`
   - WebSocket连接管理

4. ✅ 集成API:
   - 项目CRUD操作
   - 实时进度推送

### P1 - 后续优化
1. 建立UI组件库
2. 响应式断点测试
3. 前端单元测试
4. E2E测试覆盖

---

*本UX设计规范文档由AI Story团队创建,基于BMad实施就绪评估报告的建议生成。*
