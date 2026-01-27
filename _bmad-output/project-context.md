---
project_name: 'ai_story'
user_name: 'Root'
date: '2026-01-26'
sections_completed: ['discovery']
existing_patterns_found: {
  "naming_conventions": 3,
  "architecture_patterns": 4,
  "critical_rules": 7
}
---

# Project Context for AI Agents

_本文件包含AI代理在实现代码时必须遵循的关键规则和模式。重点关注容易被忽略的不明显细节。_

**项目类型:** Brownfield - 系统维护与部署
**代码规模:** ~8,000+ LOC
**主要关注:** 系统稳定性验证

---

## Technology Stack & Versions

### Backend (Python)

**核心框架:**
- Django 3.2.15 (LTS) - ⚠️ 不可更改
- Django REST Framework 3.14.0
- Django Channels 4.0.0 (WebSocket支持)

**异步任务:**
- Celery 5.5.0b2 (Beta版本) - ⚠️ 已知不稳定性,需监控
- Redis 5.x (5数据库分离架构)

**数据库:**
- 开发: SQLite
- 生产: PostgreSQL

**包管理:**
- uv (现代Python包管理器)

### Frontend (JavaScript)

**核心框架:**
- Vue.js 2.7.14 - ⚠️ 不可更改
- Vuex 3.6.2 (状态管理)
- Vue Router 3.6.5 (路由)

**HTTP & WebSocket:**
- Axios 1.6.2
- Socket.IO Client 4.6.1

**UI框架:**
- Tailwind CSS 3.4.17
- daisyUI 4.12.23

**构建工具:**
- Webpack 5.89.0
- Babel 7.23.5
- ESLint 8.55.0

---

## Critical Implementation Rules

### 🔴 MUST规则 (强制执行)

#### 1. 遵循现有代码库模式

**这是Brownfield项目 - 不得引入新模式!**

- ✅ Backend使用snake_case命名 (函数、变量、文件名)
- ✅ Backend类使用PascalCase (Django模型、ViewSet、Serializer)
- ✅ Frontend组件使用PascalCase.vue (ProjectList.vue)
- ✅ Frontend组件template中使用kebab-case (<project-list />)
- ✅ Frontend变量使用camelCase (projectId, stageName)
- ✅ API端点使用复数形式 + 版本前缀 (/api/v1/projects/)

**❌ 禁止:**
- Backend使用camelCase命名
- API端点使用单数形式 (/api/v1/project/)
- Vue组件使用snake_case.vue

#### 2. DDD领域边界不可违反

**Backend组织:**
```
apps/                    # 业务应用(DDD领域) - 可包含业务逻辑
├── projects/           # 项目管理域(聚合根)
├── content/            # 内容生成域(处理器)
├── prompts/            # 提示词管理域
├── models/             # 模型管理域
└── users/              # 用户管理域

core/                   # 核心基础设施 - 不包含业务逻辑
├── ai_client/          # AI客户端抽象层
├── pipeline/           # Pipeline工作流引擎
└── redis/              # Redis Pub/Sub
```

**规则:**
- ✅ apps/*/ 可包含业务逻辑 (services.py, tasks.py)
- ✅ core/ 仅包含通用基础设施代码
- ❌ core/ 不得包含具体业务逻辑
- ❌ projects/ 不得直接调用content/ (通过core/间接调用)

#### 3. 服务导向分层架构

**Backend分层(自上而下):**
```
API层 (DRF ViewSets)
    ↓
业务逻辑层 (Services + Tasks)
    ↓
工作流引擎 (Pipeline - 责任链模式)
    ↓
AI客户端层 (Strategy + Factory模式)
    ↓
数据层 (Django ORM)
```

**实施要求:**
- ✅ ViewSets仅处理HTTP请求/响应,业务逻辑提取到services.py
- ✅ Celery任务放在tasks.py,通过services.py调用业务逻辑
- ✅ AI客户端调用通过core/ai_client/factory.py统一管理
- ❌ ViewSets不得直接调用AI客户端(绕过抽象层)
- ❌ 业务逻辑不得散落在views.py中

#### 4. 测试覆盖率要求

**当前状态:** <2% (仅1个测试文件)
**目标状态:** >70% 单元测试 + 100% API集成测试

**实施要求:**
- ✅ 使用pytest + pytest-cov
- ✅ 测试文件与被测代码同目录 (apps/*/tests/)
- ✅ API测试使用DRF APITestCase
- ✅ 所有AI客户端调用必须可切换为Mock模式
- ✅ 测试执行时间 <5分钟

**命名规范:**
```
apps/projects/tests/
├── test_models.py        # 模型测试
├── test_views.py         # API测试
├── test_serializers.py   # 序列化器测试
├── test_tasks.py         # Celery任务测试
└── test_services.py      # 业务逻辑测试
```

#### 5. 数据库事务完整性

**配置要求:**
```python
# config/settings/base.py
DATABASES = {
    'default': {
        'ATOMIC_REQUESTS': True,  # ✅ 必须启用
    }
}
```

**Celery任务事务处理:**
```python
from django.db import transaction

@celery_app.task
def create_project_stage(project_id, stage_data):
    # ✅ 使用transaction.on_commit确保事务提交后再执行Celery任务
    def on_commit():
        process_stage_async.delay(project_id, stage_data)

    transaction.on_commit(on_commit)
```

**外键约束:**
```python
# ✅ 级联删除,无孤儿数据
project = models.ForeignKey(
    Project,
    on_delete=models.CASCADE,  # ✅ 使用CASCADE
    related_name='stages'
)
```

#### 6. Redis 5数据库分离架构

**⚠️ 关键约束 - 不可混淆!**

```python
# DB 0: Celery任务队列
CELERY_BROKER_URL = 'redis://localhost:6379/0'

# DB 1: Celery结果存储
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'

# DB 2: Redis Pub/Sub (进度推送)
REDIS_PUBSUB_URL = 'redis://localhost:6379/2'

# DB 3: Channels (WebSocket)
CHANNEL_LAYERS = {'hosts': ['redis://localhost:6379/3']}

# DB 4: Django缓存
CACHES = {'LOCATION': 'redis://localhost:6379/4'}
```

**实施要求:**
- ✅ 每个Redis客户端必须指定正确的数据库编号
- ✅ Redis Publisher使用DB 2
- ✅ Django Channels使用DB 3
- ❌ 不得混用数据库(如Celery使用DB 2)

#### 7. JSON响应格式统一

**Backend → Frontend:**
```python
# ✅ 使用snake_case (Python风格)
{
  "project_id": 1,
  "stage_name": "text_generation",
  "created_at": "2026-01-26T12:00:00Z"
}

# ❌ 禁止使用camelCase (JavaScript风格)
{
  "projectId": 1,
  "stageName": "text_generation"
}
```

**理由:** Backend主导数据格式,Frontend适配Backend

---

### 🟡 SHOULD规则 (强烈建议)

#### 1. 错误处理模式

**Backend (DRF):**
```python
# ✅ 自定义异常处理器
def custom_exception_handler(exc, context):
    # 调用DRF默认异常处理
    response = exception_handler(exc, context)

    if response is not None:
        # 自定义错误格式
        response.data = {
            'error': {
                'code': exc.default_code,
                'message': str(exc.detail)
            }
        }

    return response

# ✅ 友好的错误消息(不暴露技术堆栈)
raise APIException(detail="无法连接到AI服务,请稍后重试")
# ❌ 避免: raise APIException(detail="ConnectionError: timeout")
```

**Frontend:**
```javascript
// ✅ 显示友好的错误消息
try {
  await this.fetchProjects();
} catch (error) {
  this.error = "获取项目列表失败,请稍后重试";
  console.error('API Error:', error); // 技术细节仅记录到console
}
```

#### 2. Celery任务重试机制

```python
@celery_app.task(
    bind=True,
    max_retries=3,  # ✅ 最多重试3次
    default_retry_delay=1  # 初始延迟1秒
)
def process_stage(self, project_id, stage_name):
    try:
        # 任务逻辑
    except Exception as exc:
        # ✅ 指数退避重试 (1s → 2s → 4s)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

#### 3. WebSocket连接管理

**Frontend重连机制:**
```javascript
const socket = io('ws://localhost:8000/ws/projects/1/', {
  reconnection: true,
  reconnectionAttempts: 5,  // ✅ 最多5次
  reconnectionDelay: 1000,   // 初始1秒
  reconnectionDelayMax: 5000, // 最大5秒
  randomizationFactor: 0.5   // 随机因子避免雷群效应
});

// ✅ 监听重连事件
socket.on('reconnect_failed', () => {
  console.error('WebSocket重连失败,切换到轮询模式');
  startPolling();  // 降级到SSE或轮询
});
```

**Backend心跳检测:**
```python
class ProjectConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        # ✅ 启动心跳定时器 (每30秒)
        self.heartbeat_task = asyncio.create_task(self.send_heartbeat())

    async def send_heartbeat(self):
        while True:
            try:
                await asyncio.sleep(30)
                await self.send(text_data=json.dumps({
                    'type': 'ping',
                    'timestamp': datetime.now().isoformat()
                }))
            except Exception:
                break  # 连接已断开
```

---

### 🟢 MAY规则 (可选优化)

#### 1. 日志记录规范

**当前:** 仅有基础console logging
**目标:** 结构化JSON日志

```python
# 推荐配置
LOGGING = {
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
        }
    },
    'handlers': {
        'file': {
            'formatter': 'json',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.json.log',
        }
    }
}

# ✅ 包含的字段
logger.info('Project created', extra={
    'request_id': request.id,
    'user_id': request.user.id,
    'action': 'project.create',
    'duration_ms': 123
})
```

#### 2. 健康检查端点

**实现建议:**
```python
# /api/v1/health/
# 响应时间要求: < 200ms

from django.db import connections
from redis import Redis

def health_check(request):
    status = {
        'database': check_database(),
        'redis_celery': check_redis_db(0),
        'redis_pubsub': check_redis_db(2),
        'redis_channels': check_redis_db(3),
        'redis_cache': check_redis_db(4),
        'celery_worker': check_celery_worker(),
        'disk_space': check_disk_space(),
    }

    return Response(status, status=200 if all(status.values()) else 503)
```

---

## Common Patterns & Conventions

### Backend (Django)

**模型定义:**
```python
# ✅ 正确示例
class Project(models.Model):
    """项目模型"""
    original_topic = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'projects_project'
        ordering = ['-created_at']
```

**ViewSet模式:**
```python
# ✅ 正确示例
class ProjectViewSet(viewsets.ModelViewSet):
    """项目管理API"""
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def execute_stage(self, request, pk=None):
        """执行指定阶段"""
        project = self.get_object()
        # ✅ 调用service处理业务逻辑
        result = ProjectService.execute_stage(project, request.data)
        return Response(result)
```

**Celery任务模式:**
```python
@celery_app.task(bind=True, max_retries=3)
def process_stage(self, project_id, stage_name):
    """处理阶段任务"""
    try:
        # ✅ 通过service调用业务逻辑
        result = ProjectService.process_stage(project_id, stage_name)
        return result
    except Exception as exc:
        # ✅ 指数退避重试
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### Frontend (Vue)

**组件结构:**
```javascript
// ✅ 正确示例
export default {
  name: 'ProjectList',
  components: { StageContent, StatusBadge },

  data() {
    return {
      loading: false,
      projects: [],
      error: null
    }
  },

  mounted() {
    this.fetchProjects();
  },

  methods: {
    async fetchProjects() {
      this.loading = true;
      try {
        const response = await api.projects.list();
        this.projects = response.data.results;
      } catch (error) {
        this.error = "获取项目列表失败";
        console.error('Error:', error);
      } finally {
        this.loading = false;
      }
    }
  }
}
```

**Vuex Store模式:**
```javascript
// ✅ 正确示例
export default {
  namespaced: true,

  state: {
    current_project: null,
    project_list: [],
    loading: false
  },

  mutations: {
    SET_CURRENT_PROJECT(state, project) {
      state.current_project = project;
    }
  },

  actions: {
    async fetch_projects({ commit }) {
      commit('SET_LOADING', true);
      try {
        const response = await api.projects.list();
        commit('SET_PROJECT_LIST', response.data.results);
      } finally {
        commit('SET_LOADING', false);
      }
    }
  }
}
```

---

## Testing Requirements

### Backend Testing

**单元测试:**
```python
# apps/projects/tests/test_models.py
import pytest
from apps.projects.models import Project

@pytest.mark.django_db
def test_project_creation():
    """测试项目创建"""
    project = Project.objects.create(
        original_topic="测试主题"
    )
    assert project.status == 'pending'
    assert Project.objects.count() == 1
```

**API集成测试:**
```python
# apps/projects/tests/test_views.py
from rest_framework.test import APITestCase

class ProjectViewSetTests(APITestCase):
    """项目API测试"""

    def test_create_project(self):
        """测试创建项目API"""
        url = '/api/v1/projects/'
        data = {'original_topic': '测试主题'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Project.objects.count(), 1)
```

### Mock AI客户端

```python
# ✅ 使用Mock客户端进行离线测试
from unittest.mock import patch
from core.ai_client.factory import AIClientFactory

@patch.object(AIClientFactory, 'get_client')
def test_llm_stage_with_mock(mock_get_client):
    """使用Mock客户端测试LLM阶段"""
    # 设置Mock返回值
    mock_client = Mock()
    mock_client.generate.return_value = {"text": "Mock response"}
    mock_get_client.return_value = mock_client

    # 执行测试
    result = LLMStageProcessor().process(project_id)

    # 验证
    assert result['text'] == "Mock response"
```

---

## Anti-Patterns to Avoid

### Backend

❌ **错误示例 1: 业务逻辑在ViewSet中**
```python
class ProjectViewSet(viewsets.ModelViewSet):
    def execute_stage(self, request, pk=None):
        # ❌ 100行业务逻辑
        project = self.get_object()
        # ... 大量业务逻辑 ...
        return Response(result)
```

✅ **正确示例:**
```python
class ProjectViewSet(viewsets.ModelViewSet):
    def execute_stage(self, request, pk=None):
        project = self.get_object()
        # ✅ 调用service
        result = ProjectService.execute_stage(project, request.data)
        return Response(result)
```

❌ **错误示例 2: 绕过AI客户端抽象层**
```python
# ❌ 直接导入OpenAI客户端
from openai import OpenAI

def generate_text(prompt):
    client = OpenAI(api_key=...)
    return client.chat.completions.create(...)
```

✅ **正确示例:**
```python
# ✅ 通过工厂模式获取客户端
from core.ai_client.factory import AIClientFactory

def generate_text(prompt):
    client = AIClientFactory.get_client('llm')
    return client.generate(prompt)
```

❌ **错误示例 3: camelCase API响应**
```python
# ❌ Backend返回camelCase
return Response({
    'projectId': project.id,
    'stageName': stage.name
})
```

✅ **正确示例:**
```python
# ✅ Backend返回snake_case
return Response({
    'project_id': project.id,
    'stage_name': stage.name
})
```

### Frontend

❌ **错误示例 1: 直接在组件中调用API**
```javascript
// ❌ 组件直接调用axios
export default {
  methods: {
    async fetchProjects() {
      const response = await axios.get('/api/v1/projects/');
      this.projects = response.data;
    }
  }
}
```

✅ **正确示例:**
```javascript
// ✅ 通过Vuex action调用API
export default {
  methods: {
    fetchProjects() {
      this.$store.dispatch('projects/fetch_projects');
    }
  }
}
```

❌ **错误示例 2: 使用setTimeout延迟**
```javascript
// ❌ 使用setTimeout
setTimeout(() => {
  this.loading = false;
}, 1000);
```

✅ **正确示例:**
```javascript
// ✅ 使用async/await
await this.fetchData();
this.loading = false;
```

---

## File Organization Patterns

### Backend

```
apps/{domain}/
├── models.py           # 数据模型
├── views.py            # ViewSets (API层)
├── serializers.py      # DRF Serializers
├── services.py         # 业务逻辑 (SHOULD在此)
├── tasks.py            # Celery异步任务
├── urls.py             # URL路由
├── consumers.py        # WebSocket消费者
├── admin.py            # Django Admin配置
└── tests/              # 测试文件
    ├── test_models.py
    ├── test_views.py
    ├── test_tasks.py
    └── test_services.py
```

### Frontend

```
src/
├── views/              # 页面级组件(路由级)
│   └── projects/
│       └── ProjectList.vue
├── components/         # 可复用组件
│   ├── common/         # 通用组件
│   └── projects/       # 项目相关组件
├── store/              # Vuex状态管理
│   └── modules/
│       └── projects.js
└── services/           # API服务层
    └── api/
        └── projects.js
```

---

## Development Workflow

### Quick Start

**Backend启动:**
```bash
cd backend
uv sync                                          # 安装依赖
uv run python manage.py migrate                   # 数据库迁移
./run_asgi.sh                                    # 启动ASGI服务器
uv run celery -A config worker -Q llm,image,video -l info  # 启动Celery
```

**Frontend启动:**
```bash
cd frontend
npm install                                      # 安装依赖
npm run dev                                      # 启动开发服务器
```

**Redis:**
```bash
docker run -d -p 6379:6379 redis:latest          # 启动Redis
```

### Code Quality Checks

**Backend:**
```bash
flake8 backend/                                  # PEP 8检查
black backend/                                    # 代码格式化
```

**Frontend:**
```bash
npm run lint                                      # ESLint检查
npm run lint:fix                                  # 自动修复
```

---

## Architecture References

**完整架构文档:** `/home/code/ai_story/_bmad-output/planning-artifacts/architecture.md`

**关键章节:**
- 项目上下文分析
- 核心架构决策
- 实施模式与一致性规则
- 项目结构与边界
- 架构验证结果

**CLAUDE.md (项目主文档):** `/home/code/ai_story/CLAUDE.md`

---

**最后更新:** 2026-01-26
**状态:** READY FOR IMPLEMENTATION ✅
