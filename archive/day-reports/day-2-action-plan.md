---
project: AI Story Generation System
documentType: Day 2 Action Plan
version: 1.0
created: 2026-01-27
phase: Phase 1 - Day 2执行计划
---

# AI Story - Day 2 执行计划

**制定时间:** 2026-01-27
**基于:** Day 1状态分析
**环境:** Python 3.12.3, 无包管理器

---

## Day 1总结回顾

### ✅ 已完成工作

1. **实施就绪评估** (100%)
   - 评分26/30 (优秀)
   - 识别并解决UX文档缺失风险

2. **文档创建** (100%)
   - UX设计规范文档
   - 实施计划文档
   - Day 1执行指南
   - 进度跟踪报告

3. **代码检查发现** (超预期)
   - ✅ Mock AI客户端已完整实现(LLM/Image/Video)
   - ✅ pytest配置完整(80%完成,仅缺依赖安装)
   - ✅ 测试代码已编写(8个测试文件)
   - ❌ 健康检查HTTP端点未实现

### 📊 实际进度

- **预期:** 15%
- **实际:** 30%
- **超预期原因:** Story 1.3已实现,Story 1.2配置完成

### ⚠️ 当前阻塞

**主要阻塞:** Python包管理器缺失
- **影响:** 无法运行测试,无法安装依赖
- **解决:** 安装uv(15分钟)

---

## Day 2执行计划

### 方案A: 完整执行计划(环境就绪后)

**前提条件:** 已安装uv并同步依赖

#### 上午任务 (2小时)

**任务1: 环境准备与验证 (30分钟)**

```bash
# 1. 安装uv (如果未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 2. 同步依赖
cd /home/code/ai_story
uv sync

# 3. 验证pytest
cd backend
python -m pytest --version

# 4. 运行测试验证脚本
./verify_pytest.sh
```

**预期输出:**
- pytest版本>=8.0.0
- 测试发现成功
- 覆盖率报告生成

**任务2: 运行现有测试并分析 (1小时)**

```bash
# 运行所有测试
pytest -v

# 生成覆盖率报告
pytest --cov=apps --cov=core --cov-report=html:htmlcov tests/

# 查看覆盖率摘要
pytest --cov=apps --cov=core --cov-report=term-missing tests/
```

**目标:**
- 建立测试覆盖率基准线
- 识别失败的测试
- 记录需要修复的问题

**任务3: 修复测试问题 (30分钟)**

根据测试结果:
- 修复导入错误
- 修复配置问题
- 更新测试fixture

#### 下午任务 (3小时)

**任务4: Story 2.1 - 配置结构化日志 (1.5小时)**

**步骤1: 安装python-json-logger**
```bash
uv pip install python-json-logger
```

**步骤2: 创建JSON formatter配置**

创建`backend/core/logging/json_formatter.py`:

```python
"""
JSON日志格式化器
基于python-json-logger,提供结构化日志输出
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """
    自定义JSON日志格式化器
    符合SOLID原则: 单一职责,仅负责格式化
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        将日志记录格式化为JSON字符串

        Args:
            record: 日志记录对象

        Returns:
            str: JSON格式的日志字符串
        """
        # 基础日志信息
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息(如果有)
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段(如果有)
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, ensure_ascii=False)
```

**步骤3: 更新Django settings**

在`backend/config/settings/base.py`中添加:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'json': {
            '()': 'core.logging.json_formatter.JSONFormatter',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/ai_story/django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },

    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },

    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

**步骤4: 验证JSON日志输出**

```bash
# 启动Django shell
uv run python manage.py shell

# 在shell中测试
import logging
logger = logging.getLogger(__name__)
logger.info("测试JSON日志输出", extra={"custom_field": "custom_value"})
logger.error("测试错误日志", extra={"error_code": 500})
```

**预期输出:**
```json
{"timestamp":"2026-01-27T10:00:00Z","level":"INFO","logger":"__main__","message":"测试JSON日志输出","module":"__main__","function":"<module>","line":1,"custom_field":"custom_value"}
```

**任务5: Story 2.2 - 健康检查端点实现 (1.5小时)**

**步骤1: 创建健康检查视图**

创建`backend/apps/core/views.py`:

```python
"""
系统健康检查和监控视图
"""

from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_GET
from django.db import connection
from django.core.cache import cache
import time


@require_GET
def health_check(request: HttpRequest) -> JsonResponse:
    """
    系统健康检查端点

    返回系统状态,包括:
    - 数据库连接状态
    - Redis缓存状态
    - 响应时间

    Returns:
        JsonResponse: 健康状态JSON

    示例响应:
    {
        "status": "healthy",
        "timestamp": "2026-01-27T10:00:00Z",
        "checks": {
            "database": {"status": "healthy", "latency_ms": 5},
            "cache": {"status": "healthy", "latency_ms": 2},
            "response_time_ms": 8
        }
    }
    """
    start_time = time.time()

    # 检查数据库连接
    db_status = _check_database()

    # 检查缓存连接
    cache_status = _check_cache()

    # 计算总响应时间
    response_time_ms = int((time.time() - start_time) * 1000)

    # 判断总体健康状态
    overall_status = "healthy"
    if db_status["status"] != "healthy" or cache_status["status"] != "healthy":
        overall_status = "unhealthy"

    # 响应阈值检查
    if response_time_ms > 200:
        overall_status = "degraded"

    return JsonResponse({
        "status": overall_status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checks": {
            "database": db_status,
            "cache": cache_status,
        },
        "response_time_ms": response_time_ms,
    })


def _check_database() -> dict:
    """检查数据库连接"""
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        latency_ms = int((time.time() - start) * 1000)

        return {
            "status": "healthy" if latency_ms < 100 else "degraded",
            "latency_ms": latency_ms,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def _check_cache() -> dict:
    """检查缓存连接"""
    try:
        start = time.time()
        cache.set("health_check", "ok", 10)
        value = cache.get("health_check")
        latency_ms = int((time.time() - start) * 1000)

        return {
            "status": "healthy" if latency_ms < 50 and value == "ok" else "unhealthy",
            "latency_ms": latency_ms,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
```

**步骤2: 创建URL路由**

在`backend/apps/core/urls.py`:

```python
"""
Core app URL配置
"""

from django.urls import path
from .views import health_check

app_name = 'core'

urlpatterns = [
    path('health/', health_check, name='health_check'),
]
```

**步骤3: 在主URL配置中包含**

在`backend/config/urls.py`中添加:

```python
urlpatterns = [
    # ... 现有配置 ...
    path('api/v1/core/', include('apps.core.urls')),
]
```

**步骤4: 测试健康检查端点**

```bash
# 方式1: 使用curl
curl http://localhost:8000/api/v1/core/health/

# 方式2: 使用pytest测试
# 创建 tests/test_health_check.py
import pytest
from django.test import Client

@pytest.mark.django_db
def test_health_check_endpoint():
    """测试健康检查端点"""
    client = Client()
    response = client.get('/api/v1/core/health/')

    assert response.status_code == 200
    data = response.json()

    assert 'status' in data
    assert 'timestamp' in data
    assert 'checks' in data
    assert 'response_time_ms' in data

    # 验证响应时间<200ms
    assert data['response_time_ms'] < 200

    # 验证数据库检查
    assert 'database' in data['checks']
    assert data['checks']['database']['status'] in ['healthy', 'degraded']
```

**预期输出:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T10:00:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 5
    },
    "cache": {
      "status": "healthy",
      "latency_ms": 2
    }
  },
  "response_time_ms": 8
}
```

---

### 方案B: 无包管理器执行计划(等待环境准备)

如果环境问题暂时无法解决,可以继续完成以下分析工作:

#### 可执行任务 (无需包管理器)

**任务1: 完善测试文档 (1小时)**

创建`backend/docs/TESTING.md`:

```markdown
# 测试指南

## 测试框架

本项目使用pytest作为测试框架。

## 运行测试

### 运行所有测试
```bash
pytest
```

### 运行特定测试文件
```bash
pytest tests/test_mock_ai_clients.py
```

### 运行特定测试函数
```bash
pytest tests/test_mock_ai_clients.py::TestMockLLMClient::test_generate
```

### 生成覆盖率报告
```bash
pytest --cov=apps --cov=core --cov-report=html:htmlcov tests/
```

## 测试文件组织

- `tests/conftest.py` - pytest配置和共享fixture
- `tests/test_mock_ai_clients.py` - Mock AI客户端测试
- `tests/test_core_ai_client_base.py` - AI客户端基类测试
- `tests/test_core_pipeline_base.py` - Pipeline基类测试
- `tests/test_core_redis.py` - Redis发布订阅测试

## 编写测试

### 示例: 单元测试
\`\`\`python
import pytest
from core.ai_client.mock_llm_client import MockLLMClient

@pytest.mark.asyncio
async def test_mock_llm_client_generate():
    """测试Mock LLM客户端生成功能"""
    client = MockLLMClient(model_name="mock-model")
    response = await client.generate("测试提示词")

    assert response.success is True
    assert len(response.text) > 0
    assert response.metadata['is_mock'] is True
\`\`\`

### 示例: 集成测试
\`\`\`python
import pytest
from django.test import Client

@pytest.mark.django_db
def test_project_create_api():
    """测试项目创建API"""
    client = Client()
    response = client.post('/api/v1/projects/', {
        'name': '测试项目',
        'description': '测试描述'
    })

    assert response.status_code == 201
\`\`\`
```

**任务2: 数据库迁移文档 (1小时)**

创建`backend/docs/MIGRATIONS.md`:

```markdown
# 数据库迁移指南

## 迁移文件位置

迁移文件位于各app的`migrations/`目录:
- `apps/projects/migrations/`
- `apps/content/migrations/`
- `apps/prompts/migrations/`
- `apps/models/migrations/`
- `apps/users/migrations/`

## 创建迁移

```bash
# 创建迁移文件
uv run python manage.py makemigrations

# 为特定app创建迁移
uv run python manage.py makemigrations apps.projects

# 给迁移命名
uv run python manage.py makemigrations --name add_project_status
```

## 应用迁移

```bash
# 应用所有迁移
uv run python manage.py migrate

# 应用特定app的迁移
uv run python manage.py migrate apps.projects

# 查看迁移状态
uv run python manage.py showmigrations
```

## 迁移最佳实践

1. **迁移文件命名清晰**
   - ✅ `0002_add_project_status_field.py`
   - ❌ `0002_migration.py`

2. **数据迁移单独分离**
   - Schema迁移: 修改表结构
   - Data迁移: 迁移数据

3. **向后兼容**
   - 添加字段: 设置default或null=True
   - 删除字段: 先确认代码中无引用

4. **测试迁移**
   - 在开发环境完整测试
   - 备份生产数据库后再应用

## 回滚迁移

```bash
# 回滚上一次迁移
uv run python manage.py migrate apps.projects 0001

# 回滚特定迁移
uv run python manage.py migrate apps.projects 0001_initial
```

## 迁移故障排查

### 问题: 迁移冲突
```bash
# 解决方案: 合并迁移
uv run python manage.py merge
```

### 问题: 迁移历史不一致
```bash
# 解决方案: 伪造迁移
uv run python manage.py migrate --fake
```
```

**任务3: WebSocket测试脚本 (代码级) (1小时)**

创建`tests/test_websocket_connection.py`:

```python
"""
WebSocket连接稳定性测试
"""

import pytest
import asyncio
import time
from channels.testing import WebsocketCommunicator
from apps.projects.consumers import ProjectProgressConsumer


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_connection():
    """测试WebSocket连接建立"""
    communicator = WebsocketCommunicator(
        ProjectProgressConsumer.as_asgi(),
        '/ws/projects/1/'
    )

    connected, _ = await communicator.connect()
    assert connected is True

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_progress_message():
    """测试WebSocket进度消息接收"""
    communicator = WebsocketCommunicator(
        ProjectProgressConsumer.as_asgi(),
        '/ws/projects/1/'
    )

    await communicator.connect()

    # 模拟接收进度消息
    response = await communicator.receive_json_from(timeout=5)

    assert 'stage' in response
    assert 'progress' in response
    assert 'status' in response

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_latency():
    """测试WebSocket消息延迟"""
    communicator = WebsocketCommunicator(
        ProjectProgressConsumer.as_asgi(),
        '/ws/projects/1/'
    )

    await communicator.connect()

    start_time = time.time()
    await communicator.receive_json_from(timeout=5)
    latency_ms = (time.time() - start_time) * 1000

    # 验证延迟<500ms
    assert latency_ms < 500

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_websocket_reconnection():
    """测试WebSocket自动重连"""
    # 第一次连接
    communicator1 = WebsocketCommunicator(
        ProjectProgressConsumer.as_asgi(),
        '/ws/projects/1/'
    )
    await communicator1.connect()
    await communicator1.disconnect()

    # 等待1秒
    await asyncio.sleep(1)

    # 第二次连接(模拟重连)
    communicator2 = WebsocketCommunicator(
        ProjectProgressConsumer.as_asgi(),
        '/ws/projects/1/'
    )
    connected, _ = await communicator2.connect()
    assert connected is True

    await communicator2.disconnect()
```

---

## 完成标准

### Day 2完成标准

**方案A (环境就绪):**
- ✅ pytest测试框架可运行,覆盖率>70%
- ✅ JSON结构化日志正常输出
- ✅ 健康检查端点响应<200ms
- ✅ 健康检查端点测试通过

**方案B (等待环境):**
- ✅ 测试文档创建完成
- ✅ 迁移文档创建完成
- ✅ WebSocket测试代码编写完成

### Week 1里程碑

**目标:**
- ✅ Epic 1: Story 1.1-1.3完成 (已完成)
- [ ] Epic 1: Story 1.4-1.6完成 (Day 2-3)
- [ ] Epic 2: Story 2.1-2.2完成 (Day 2)
- [ ] Epic 3: Story 3.1完成 (Day 3)

---

## 时间估算

| 任务 | 预计用时 | 优先级 |
|------|---------|--------|
| 环境准备(安装uv) | 15分钟 | 🔴 最高 |
| 测试验证与基准建立 | 1小时 | 🔴 高 |
| 结构化日志配置 | 1.5小时 | 🟡 中 |
| 健康检查端点实现 | 1.5小时 | 🟡 中 |
| 测试文档编写 | 1小时 | 🟢 低 |
| 迁移文档编写 | 1小时 | 🟢 低 |
| WebSocket测试代码 | 1小时 | 🟢 低 |

**总计(方案A):** 5小时 (1个工作日)
**总计(方案B):** 3小时 (分析工作)

---

## 推荐执行顺序

### 立即执行 (今天上午)

1. 🚀 **安装uv包管理器** (5-10分钟)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source ~/.bashrc
   ```

2. 📦 **同步项目依赖** (2-3分钟)
   ```bash
   cd /home/code/ai_story
   uv sync
   ```

3. ✅ **运行测试验证** (5-10分钟)
   ```bash
   cd backend
   ./verify_pytest.sh
   ```

### 下午执行 (今天下午)

4. 📝 **配置结构化日志** (1.5小时)
   - 安装python-json-logger
   - 创建JSONFormatter
   - 更新Django settings
   - 验证JSON输出

5. 🏥 **实现健康检查端点** (1.5小时)
   - 创建health_check视图
   - 配置URL路由
   - 编写测试用例
   - 验证响应时间<200ms

### 可选执行 (等待环境准备时)

6. 📚 **编写测试文档** (1小时)
7. 📚 **编写迁移文档** (1小时)
8. 💻 **编写WebSocket测试代码** (1小时)

---

## 故障排查

### 问题1: uv安装失败

**错误:** `curl: command not found`

**解决方案:**
```bash
# 使用wget
wget -qO- https://astral.sh/uv/install.sh | sh
```

### 问题2: pytest导入错误

**错误:** `ModuleNotFoundError: No module named 'pytest'`

**解决方案:**
```bash
# 检查uv是否正确安装
uv --version

# 重新同步依赖
cd /home/code/ai_story
uv sync
```

### 问题3: Django迁移失败

**错误:** `django.db.utils.OperationalError: no such table`

**解决方案:**
```bash
# 应用所有迁移
uv run python manage.py migrate

# 或使用--run-syncdb选项
uv run python manage.py migrate --run-syncdb
```

### 问题4: 健康检查端点404

**错误:** 访问`/api/v1/core/health/`返回404

**解决方案:**
1. 检查`apps/core/urls.py`是否存在
2. 检查`config/urls.py`是否包含core URLs
3. 重启Django服务器

---

## 下一步行动

### Day 3准备

**假设Day 2完成:**

1. **Epic 1继续**
   - Story 1.4: 核心模块单元测试
   - Story 1.5: API集成测试

2. **Epic 3启动**
   - Story 3.1: WebSocket连接验证
   - Story 3.2: 进度推送延迟测试

3. **Epic 2继续**
   - Story 2.3: 日志中间件
   - Story 2.4: API响应时间监控

---

## 总结

**Day 2核心目标:**
1. 🚀 解决环境问题(安装uv)
2. ✅ 验证测试框架并建立基准
3. 📝 配置结构化日志(JSON格式)
4. 🏥 实现健康检查端点(<200ms)

**预期成果:**
- 测试覆盖率>70%
- 结构化日志输出
- 健康检查端点可用
- 为Day 3做好准备

**关键成功因素:**
- 环境准备顺利完成
- 测试框架验证通过
- 健康检查端点性能达标

---

*本计划基于Day 1状态分析,2026-01-27*
