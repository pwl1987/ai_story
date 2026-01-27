# AI Story Frontend

AI Story生成系统的Vue.js前端应用。

## 技术栈

- **Vue 2.7.14** - 渐进式JavaScript框架
- **Vue Router 3** - 官方路由管理器
- **Vuex 3** - 状态管理
- **Element UI** - UI组件库
- **Tailwind CSS** - 实用优先的CSS框架
- **Axios** - HTTP客户端
- **Socket.IO Client** - WebSocket实时通信
- **Webpack 5** - 模块打包工具

## 项目结构

```
frontend/
├── config/                 # Webpack配置
│   ├── webpack.common.js   # 通用配置
│   ├── webpack.dev.js      # 开发环境配置
│   └── webpack.prod.js     # 生产环境配置
├── public/                 # 静态资源
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── assets/            # 资源文件
│   │   ├── css/           # 样式文件
│   │   └── images/        # 图片资源
│   ├── components/        # 组件
│   │   ├── common/        # 通用组件
│   │   ├── layout/        # 布局组件
│   │   ├── projects/      # 项目相关组件
│   │   ├── content/       # 内容相关组件
│   │   ├── models/        # 模型相关组件
│   │   └── prompts/       # 提示词相关组件
│   ├── views/             # 页面组件
│   │   ├── projects/      # 项目页面
│   │   ├── prompts/       # 提示词页面
│   │   ├── models/        # 模型页面
│   │   ├── Layout.vue     # 主布局
│   │   └── NotFound.vue   # 404页面
│   ├── router/            # 路由配置
│   │   └── index.js
│   ├── store/             # Vuex状态管理
│   │   ├── modules/       # 模块
│   │   │   ├── projects.js
│   │   │   ├── prompts.js
│   │   │   ├── models.js
│   │   │   └── content.js
│   │   └── index.js
│   ├── services/          # API服务
│   │   ├── apiClient.js   # Axios配置
│   │   ├── projectService.js
│   │   ├── promptService.js
│   │   ├── modelService.js
│   │   ├── contentService.js
│   │   └── websocketClient.js
│   ├── utils/             # 工具函数
│   │   ├── helpers.js     # 辅助函数
│   │   └── constants.js   # 常量定义
│   ├── App.vue            # 根组件
│   └── main.js            # 应用入口
├── .babelrc.js            # Babel配置
├── .eslintrc.js           # ESLint配置
├── postcss.config.js      # PostCSS配置
├── tailwind.config.js     # Tailwind配置
└── package.json

```

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 开发模式

```bash
npm run dev
```

应用将在 http://localhost:3000 启动。

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env.local

# 编辑.env.local文件配置后端API地址
# VUE_APP_API_BASE_URL=http://localhost:8000/api/v1
# VUE_APP_WS_URL=ws://localhost:8000
```

**重要:** Vue项目使用`.env.local`文件存储本地环境变量(该文件已加入.gitignore)。

### 3. 与后端集成

**API端点配置:**
- 开发环境默认: `http://localhost:8000/api/v1`
- WebSocket地址: `ws://localhost:8000`

**前端如何连接后端:**
```javascript
// src/services/apiClient.js
const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

// WebSocket连接
const WS_URL = process.env.VUE_APP_WS_URL || 'ws://localhost:8000';
```

**确保后端已启动:**
1. 检查后端健康状态: `curl http://localhost:8000/api/v1/health/`
2. 如果后端运行在不同端口,更新`.env.local`文件

### 4. 开发模式

### 4. 生产构建

```bash
npm run build
```

构建产物将生成在 `dist/` 目录。

### 4. 代码检查

```bash
npm run lint        # 检查代码
npm run lint:fix    # 自动修复
```

## Docker部署

### 开发环境

```bash
# 从项目根目录执行
docker-compose up frontend
```

### 生产环境

```bash
# 构建生产镜像
docker build -f docker/frontend.Dockerfile -t ai-story-frontend .

# 运行容器
docker run -p 3000:80 ai-story-frontend
```

## 核心功能

### 1. 项目管理
- 项目列表、创建、编辑、删除
- 项目详情查看
- 工作流阶段可视化
- 实时状态更新(WebSocket)

### 2. 内容展示
- 分镜列表展示
- 生成图片预览
- 生成视频播放

### 3. 提示词管理
- 提示词集管理
- 模板查看和编辑

### 4. 模型管理
- 模型提供商列表
- 使用统计查看

## API集成

前端通过以下服务与后端通信:

- **RESTful API**: `/api/v1/*`
- **WebSocket**: `ws://localhost:8000/ws/projects/{id}/`

环境变量配置:

```env
VUE_APP_API_BASE_URL=http://localhost:8000/api/v1
VUE_APP_WS_URL=ws://localhost:8000
```

## 代码规范

### 组件命名
- 使用 PascalCase: `ProjectList.vue`
- 组件名必须多个单词(避免与HTML元素冲突)

### 文件组织
- 每个组件一个文件
- 相关组件放在同一目录
- 通用组件放在 `components/common/`

### 样式约定
- 优先使用 Tailwind CSS 工具类
- 组件特定样式使用 scoped CSS
- 全局样式定义在 `assets/css/main.css`

### 状态管理
- 按功能模块划分 Vuex modules
- 异步操作放在 actions
- 避免直接修改 state,使用 mutations

## 开发建议

### 性能优化
- 使用路由懒加载
- 图片资源按需加载
- 合理使用 computed 和 watch
- 避免不必要的组件重渲染

### 错误处理
- API调用统一错误处理(apiClient拦截器)
- 组件级别错误边界
- 用户友好的错误提示

### 调试技巧
- 使用 Vue DevTools 浏览器扩展
- Chrome DevTools 网络面板监控API
- WebSocket调试工具

## Phase 1 - P0 MVP验证实施计划

**当前阶段:** Phase 1 - 系统稳定性验证 (预计3周)

**前端在Phase 1的主要工作:**

### Epic 3: 实时通信稳定性 (与后端Epic 3并行)

**目标:** 确保WebSocket连接稳定可靠,实时进度推送正常工作

**关键组件开发:**
- ⏳ WebSocket连接管理器 (自动重连机制)
- ⏳ 实时进度条组件
- ⏳ 进度推送延迟优化(<500ms)
- ⏳ SSE备用方案(降级支持)

**Phase 1完成标准:**
- ✅ WebSocket实时进度推送正常工作
- ✅ WebSocket自动重连机制正常(最多5次)
- ✅ 进度推送延迟<500ms
- ✅ 连接断开时显示友好提示

### Epic 4: 项目管理 (Phase 2,已在规划中)

**核心页面开发:**
- ⏳ 项目列表页 (基于UX设计规范)
- ⏳ 项目详情页 (包含实时进度显示)
- ⏳ 创建项目表单
- ⏳ 控制按钮组(开始、暂停、重试、删除)

**关键UI组件:**
- ⏳ ProjectCard (项目卡片)
- ⏳ StageProgressBar (阶段进度条)
- ⏳ RealTimeProgressBar (实时进度条)
- ⏳ FilePreview (文件预览)

**详细UX设计规范:** 参见 `_bmad-output/planning-artifacts/ux-design-specification.md`

**详细实施计划:** 参见 `_bmad-output/planning-artifacts/implementation-plan.md`

---

## 待开发功能

### Phase 1后 (Phase 2/3)
- [ ] 用户认证和权限管理
- [ ] 图片查看器组件
- [ ] 视频播放器组件
- [ ] 批量操作功能
- [ ] 导出功能
- [ ] 主题切换
- [ ] 国际化支持

## 故障排查

### 常见问题

**1. 依赖安装失败**
```bash
# 清除缓存重新安装
rm -rf node_modules package-lock.json
npm install
```

**2. 端口被占用**
```bash
# 修改 webpack.dev.js 中的端口配置
devServer: {
  port: 3001,  // 改成其他端口
}
```

**3. API请求失败**
- 检查后端服务是否启动
- 确认环境变量配置正确
- 查看浏览器控制台网络请求

### 新增问题排查

**WebSocket连接失败**
```bash
# 检查后端是否使用ASGI服务器
# 错误: "WebSocket connection failed"
# 解决: 后端必须使用 ./run_asgi.sh 而不是 python manage.py runserver
```

**CORS错误**
```bash
# 后端需要配置CORS
# 检查 backend/config/settings/base.py
# CORS_ALLOWED_ORIGINS 应包含 http://localhost:3000
```

### 更多文档

- **后端文档:** [backend/README.md](../backend/README.md)
- **项目架构:** [CLAUDE.md](../CLAUDE.md)
- **Celery + Redis:** [docs/CELERY_REDIS_STREAMING.md](../docs/CELERY_REDIS_STREAMING.md)
- **项目概览:** [docs/project-overview.md](../docs/project-overview.md)

## 贡献指南

1. 遵循项目代码规范
2. 编写必要的单元测试
3. 更新相关文档
4. 提交前运行 lint 检查

## License

MIT
