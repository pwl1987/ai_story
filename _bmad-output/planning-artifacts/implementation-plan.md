---
project: AI Story Generation System
documentType: Implementation Plan
version: 1.0
created: 2026-01-27
phase: Phase 1 - P0 MVP验证
---

# AI Story - 实施计划

**项目:** AI Story Generation System
**阶段:** Phase 1 - P0 MVP验证
**创建日期:** 2026-01-27
**预计工期:** 2-3周

---

## 执行摘要

根据**实施就绪评估报告**的建议,项目已满足实施条件(评分26/30,优秀)。本计划文档将指导团队完成Phase 1的P0 MVP验证工作。

### 📊 评估结果回顾

| 维度 | 评分 | 状态 |
|------|------|------|
| 文档完整性 | 4/5 | ✅ 优秀 |
| PRD质量 | 5/5 | ✅ 完美 |
| Epic覆盖 | 5/5 | ✅ 完美 |
| Epic质量 | 5/5 | ✅ 完美 |
| UX对齐 | 3/5 | ⚠️ 已补充 |
| 可实施性 | 4/5 | ✅ 良好 |

**最终结论:** ✅ **有条件通过** - 可以开始实施

---

## Phase 1: P0 MVP验证 (2-3周)

### 目标

建立项目的基础设施,确保系统可测试、可观测、稳定运行:

1. ✅ 测试覆盖率从<2%提升到>70%
2. ✅ 实现结构化日志和健康检查
3. ✅ 确保WebSocket实时通信稳定可靠

### 并行实施的3个Epic

#### Epic 1: 测试基础设施

**用户价值:** 开发者可以快速验证代码质量,防止回归问题

**Story清单:**

- **Story 1.1: README文档完善** (1天)
  - 更新backend/README.md和frontend/README.md
  - 添加项目概述、技术栈、快速启动指南
  - 说明服务启动顺序(Redis → Celery → Django → 前端)

- **Story 1.2: 测试框架搭建** (0.5天)
  - 安装pytest、pytest-cov、pytest-django
  - 创建pytest.ini配置文件
  - 配置覆盖率目标>70%

- **Story 1.3: Mock AI客户端实现** (1天)
  - 实现MockLLMClient、MockImageClient、MockVideoClient
  - 支持环境变量ENABLE_MOCK_AI=true启用
  - 返回真实格式的假数据

- **Story 1.4: 核心模块单元测试** (2-3天)
  - 测试core/ai_client/(工厂类、策略类)
  - 测试core/pipeline/(责任链处理器)
  - 测试core/redis/(消息发布/订阅)
  - 目标覆盖率>70%

- **Story 1.5: API集成测试** (2-3天)
  - 测试所有ViewSet端点(projects/content/prompts/models)
  - 测试CRUD操作、权限、验证逻辑
  - 100%端点覆盖

- **Story 1.6: 数据库迁移文档** (0.5天)
  - 创建MIGRATIONS.md文档
  - 说明迁移命令和回滚方法

**Epic 1总计:** 7-9天

#### Epic 2: 系统可观测性

**用户价值:** 运维人员可以实时监控系统健康状态,快速定位问题

**Story清单:**

- **Story 2.1: 结构化日志系统搭建** (1天)
  - 配置python-json-logger
  - 所有日志输出为JSON格式
  - 敏感信息自动脱敏

- **Story 2.2: 健康检查端点实现** (1天)
  - 创建/api/v1/health/端点
  - 检查数据库、Redis(5个数据库)连接状态
  - 响应时间<200ms(P95)

- **Story 2.3: API错误日志中间件** (1天)
  - 自动捕获API调用异常
  - 记录请求路径、方法、参数、错误堆栈
  - 返回友好的错误消息

- **Story 2.4: Celery任务失败日志** (1天)
  - 配置Celery task_logging
  - 记录任务名称、参数、失败原因、重试次数

- **Story 2.5: API响应时间监控** (1天)
  - 创建响应时间记录中间件
  - 记录P50、P95、P99响应时间

- **Story 2.6: Celery任务执行时间监控** (1天)
  - 使用task_prerun/task_postrun信号
  - 记录任务执行时长

- **Story 2.7: 日志查询和告警配置** (0.5天)
  - 创建LOGGING.md文档
  - 提供常见查询示例

**Epic 2总计:** 6.5-7.5天

#### Epic 3: 实时通信稳定性

**用户价值:** 创作者可以实时查看项目进度,连接断开时自动恢复

**Story清单:**

- **验证WebSocket连接稳定性**
  - 测试WebSocket连接建立时间(<1秒)
  - 测试多客户端并发连接

- **实现进度推送延迟<500ms**
  - 优化Redis Pub/Sub消息传递
  - 添加进度推送时间监控

- **添加WebSocket自动重连机制**
  - 前端实现断线重连(最多5次)
  - 间隔递增策略(1s→2s→4s→8s→16s)

- **实现SSE备用方案**
  - 当WebSocket不可用时切换到轮询模式
  - 提供降级体验

**Epic 3总计:** 3-5天

### Phase 1时间表

| 周次 | Epic 1 | Epic 2 | Epic 3 |
|------|--------|--------|--------|
| 第1周 | Story 1.1-1.3 | Story 2.1-2.3 | WebSocket验证 |
| 第2周 | Story 1.4-1.5 | Story 2.4-2.6 | 进度推送优化 |
| 第3周 | Story 1.6 | Story 2.7 | 重连机制+SSE |

**总工期:** 15个工作日 (约3周)

---

## Phase 1完成标准

### 测试基础设施 (Epic 1)

- ✅ 单元测试覆盖率>70%
  ```bash
  pytest --cov=backend --cov-report=html
  # Coverage: 70%+
  ```

- ✅ API集成测试100%覆盖
  ```bash
  pytest backend/apps/*/tests/test_*.py
  # 所有端点100%覆盖
  ```

- ✅ Mock AI客户端正常工作
  ```bash
  ENABLE_MOCK_AI=true pytest
  # 所有测试通过,无需真实API
  ```

### 系统可观测性 (Epic 2)

- ✅ 健康检查端点响应<200ms
  ```bash
  curl http://localhost:8000/api/v1/health/
  # Response time < 200ms
  # {"status": "healthy", "checks": {...}}
  ```

- ✅ 结构化日志(JSON格式)完整记录
  ```json
  {"timestamp": "2026-01-27T10:00:00Z", "level": "INFO", "message": "..."}
  ```

- ✅ API响应时间P95可监控
  ```bash
  # 查看日志中的duration_ms字段
  ```

### 实时通信稳定性 (Epic 3)

- ✅ WebSocket实时进度推送正常工作
  ```javascript
  // 前端能实时接收进度更新(延迟<500ms)
  ```

- ✅ WebSocket自动重连机制正常
  ```javascript
  // 连接断开后自动重连(最多5次)
  ```

- ✅ SSE降级方案可用
  ```javascript
  // WebSocket不可用时自动切换到轮询
  ```

---

## 立即开始的准备工作 (1-2天)

### ✅ 已完成

1. ✅ 实施就绪评估报告完成
   - 评分26/30 (优秀)
   - 识别出唯一中等风险:UX文档缺失

2. ✅ UX设计规范文档已创建
   - 文件: `planning-artifacts/ux-design-specification.md`
   - 包含:核心页面线框图、关键组件规范、实时进度UI

### 📋 待完成 (可选)

在启动Phase 1之前,建议完成以下准备工作:

#### 开发环境验证

```bash
# 1. 验证所有服务可正常启动
cd backend && uv run python manage.py migrate
./run_asgi.sh  # Django ASGI
uv run celery -A config worker -Q llm,image,video -l info  # Celery

cd frontend && npm run dev  # Vue前端

# 2. 验证Redis 5数据库连接
redis-cli
> INFO keyspace
> SELECT 0  # Broker
> SELECT 1  # Result backend
> SELECT 2  # Pub/Sub
> SELECT 3  # Channels
> SELECT 4  # Cache
```

#### 前端组件库初始化

```bash
cd frontend

# 确认daisyUI和Tailwind CSS已安装
npm install -D daisyui@latest tailwindcss@latest

# 配置tailwind.config.js
module.exports = {
  content: ["./src/**/*.{html,js,vue}"],
  plugins: [require("daisyui")],
};
```

#### Vuex Store结构初始化

```bash
# 创建store目录结构
mkdir -p frontend/src/store/modules
touch frontend/src/store/index.js
touch frontend/src/store/modules/projects.js
touch frontend/src/store/modules/websocket.js
```

---

## 推荐的实施顺序

### 第1步: 环境准备 (Day 1)

**上午:**
- [ ] 验证开发环境(Backend + Frontend)
- [ ] 启动所有服务(Redis → Celery → Django → 前端)
- [ ] 验证WebSocket连接

**下午:**
- [ ] 初始化前端组件库
- [ ] 创建Vuex store结构
- [ ] 配置ESLint和Prettier

### 第2步: 并行启动3个Epic (Day 2-15)

#### Epic 1负责人 - 测试工程师

**Week 1:**
- Day 2-3: Story 1.1 (README) + Story 1.2 (测试框架)
- Day 4-5: Story 1.3 (Mock AI客户端)

**Week 2:**
- Day 6-8: Story 1.4 (核心模块单元测试)
- Day 9-10: Story 1.5 (API集成测试)

**Week 3:**
- Day 11: Story 1.6 (迁移文档)
- Day 12-15: 测试覆盖率提升至>70%

#### Epic 2负责人 - 后端工程师

**Week 1:**
- Day 2-3: Story 2.1 (结构化日志) + Story 2.2 (健康检查)
- Day 4-5: Story 2.3 (API错误日志中间件)

**Week 2:**
- Day 6-7: Story 2.4 (Celery任务日志)
- Day 8-9: Story 2.5 (API响应时间监控)

**Week 3:**
- Day 10-11: Story 2.6 (Celery任务监控)
- Day 12: Story 2.7 (日志查询文档)
- Day 13-15: 可观测性优化和调优

#### Epic 3负责人 - 全栈工程师

**Week 1:**
- Day 2-4: WebSocket连接稳定性验证
- Day 5: 进度推送延迟优化

**Week 2:**
- Day 6-8: WebSocket自动重连机制实现
- Day 9-10: 前端重连逻辑

**Week 3:**
- Day 11-13: SSE备用方案实现
- Day 14-15: 实时通信测试和优化

---

## 团队协作建议

### 每日站会 (15分钟)

**时间:** 每天上午10:00
**参与者:** 全体开发人员

**讨论内容:**
1. 昨天完成了什么?
2. 今天计划做什么?
3. 有什么阻碍?

### 周例会 (1小时)

**时间:** 每周五下午16:00
**参与者:** 全体开发人员 + 产品负责人

**讨论内容:**
1. 本周Epic进度回顾
2. 下周计划调整
3. 风险和问题讨论

### 代码审查

**要求:**
- 所有Pull Request必须经过至少1人审查
- 单元测试必须通过(pytest)
- 代码覆盖率不能降低

---

## 风险管理

### 已识别风险

| 风险 | 级别 | 缓解措施 | 负责人 |
|------|------|---------|--------|
| UX文档缺失导致UI不一致 | 中等 | ✅ 已补充UX设计规范 | 全栈工程师 |
| AI API调用失败/超时 | 中等 | Mock客户端 + 重试机制 | 后端工程师 |
| 测试覆盖率提升困难 | 低 | Epic 1专门解决 | 测试工程师 |
| WebSocket连接不稳定 | 低 | Epic 3专门解决 | 全栈工程师 |
| Celery任务失败无法追踪 | 低 | Epic 2添加日志监控 | 后端工程师 |

### 风险应对策略

**立即行动:**
- ✅ UX设计规范已创建 (文档已交付)
- ✅ 实施计划已明确 (本文档)

**持续监控:**
- 每日站会跟踪风险
- 每周例会评估风险状态
- 及时调整计划

---

## 下一步行动

### ✅ 立即可执行 (今天)

1. **启动Epic 1**
   ```bash
   cd backend
   # 开始Story 1.1: README文档完善
   ```

2. **启动Epic 2**
   ```bash
   cd backend
   # 开始Story 2.1: 结构化日志系统
   ```

3. **启动Epic 3**
   ```bash
   cd frontend
   # 开始WebSocket验证
   ```

### 📋 本周目标

- [ ] Epic 1: 完成Story 1.1-1.3 (README + 测试框架 + Mock客户端)
- [ ] Epic 2: 完成Story 2.1-2.3 (日志 + 健康检查 + 错误中间件)
- [ ] Epic 3: 完成WebSocket连接稳定性验证

### 🎯 Week 1验收标准

- [ ] README文档完整,新开发者可按文档搭建环境
- [ ] pytest测试框架配置完成,可运行测试
- [ ] Mock AI客户端可用,ENABLE_MOCK_AI=true时测试通过
- [ ] 健康检查端点/api/v1/health/正常工作
- [ ] 结构化日志(JSON格式)正常输出
- [ ] WebSocket连接稳定,无频繁断连

---

## 联系方式

**项目仓库:** `/home/code/ai_story`
**文档位置:** `_bmad-output/planning-artifacts/`
**评估报告:** `implementation-readiness-report-2026-01-27.md`
**UX设计规范:** `ux-design-specification.md`
**Epic文档:** `epics.md`

---

*本实施计划文档由AI Story团队创建,基于BMad实施就绪评估报告的建议生成。*

**下一步:** 启动Phase 1的3个并行Epic,预计2-3周完成P0 MVP验证。
