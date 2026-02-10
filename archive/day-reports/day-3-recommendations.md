---
project: AI Story Generation System
documentType: Day 3 Recommendations & Action Plan
version: 1.0
created: 2026-01-27
workflow: BMad Analyze → Recommend Next Steps
---

# AI Story - 下一步推荐与Day 3行动计划

**分析时间:** 2026-01-27
**基于:** Day 2执行成果与质量审查
**Phase:** Phase 1 - Day 3规划

---

## 当前状态评估

### 项目进度: 45% ✅

**已完成:**
- ✅ Story 1.1-1.3 (30%) - 测试基础设施
- ✅ Story 2.1 (5%) - 结构化日志
- ✅ Story 2.2 (10%) - 健康检查端点

**进行中:**
- 🟡 Story 1.4-1.6 - 核心模块测试、API集成测试、迁移文档
- 🟡 Story 2.3-2.7 - 日志中间件、监控仪表板等
- 🟡 Story 3.1-3.4 - WebSocket稳定性验证

### 质量指标

| 指标 | 基准 | 当前 | 目标 | 状态 |
|------|------|------|------|------|
| 测试通过率 | N/A | 92.9% | >95% | 🟡 良好 |
| 代码覆盖率 | <2% | 18% | >70% | 🟡 进行中 |
| 健康检查响应 | N/A | 0ms | <200ms | 🟢 优秀 |
| 结构化日志 | 否 | JSON | JSON | 🟢 完成 |
| SOLID原则 | N/A | 100% | 100% | 🟢 优秀 |

### 阻塞问题

**高优先级阻塞:**
1. 🔴 5个测试失败 - 影响测试完整性
2. 🔴 Redis服务未运行 - 影响缓存功能

**中优先级问题:**
3. 🟡 日志目录可能不存在 - 影响文件日志
4. 🟡 缺少集成测试 - 影响端到端验证

---

## 下一步推荐 (3个方案)

### 方案A: 质量优先 (推荐) ⭐

**优先级:** 🔴 最高

**理由:**
- 修复失败测试确保测试基线稳固
- 启动Redis解锁缓存功能
- 为后续开发建立信心

**Day 3任务:**
1. 修复5个失败测试 (1.5小时)
2. 启动Redis服务 (30分钟)
3. 修复日志目录问题 (15分钟)
4. 运行完整测试套件验证 (30分钟)
5. 提升测试覆盖率至25% (2小时)

**预期成果:**
- ✅ 测试通过率: 100%
- ✅ Redis功能可用
- ✅ 覆盖率: 18% → 25%
- ✅ 所有阻塞问题解决

**预计用时:** 5小时

### 方案B: 功能优先

**优先级:** 🟡 中等

**理由:**
- 继续推进新功能
- 并行修复问题
- 保持开发势头

**Day 3任务:**
1. Story 1.4: 核心模块单元测试 (2小时)
2. Story 3.1: WebSocket连接验证 (1.5小时)
3. 修复失败测试 (1小时，仅修复关键测试)
4. 集成测试编写 (1小时)

**预期成果:**
- ✅ 核心模块测试完成
- ✅ WebSocket验证完成
- ✅ 部分测试修复
- ✅ 集成测试基础建立

**预计用时:** 5.5小时

### 方案C: 文档优先

**优先级:** 🟢 低

**理由:**
- 完善文档提升可维护性
- 为团队协作做准备
- 降低知识传递成本

**Day 3任务:**
1. 编写API文档 (2小时)
2. 更新部署文档 (1小时)
3. 编写故障排查指南 (1小时)
4. 创建开发指南 (1小时)
5. 修复失败测试 (1小时)

**预期成果:**
- ✅ 完整API文档
- ✅ 部署文档完善
- ✅ 故障排查指南
- ✅ 关键测试修复

**预计用时:** 6小时

---

## 推荐执行方案: 方案A (质量优先)

### 为什么选择方案A?

1. **测试基线稳固**
   - 失败测试会掩盖新问题
   - 100%通过率是质量保障

2. **Redis依赖**
   - 后续任务（Celery, Channels）需要Redis
   - 提前启动避免阻塞

3. **技术债务最小化**
   - 早期修复成本最低
   - 避免债务积累

4. **效率最高**
   - 清理问题后开发更顺畅
   - 心理负担减轻

---

## Day 3详细执行计划 (方案A)

### 上午 (3小时) - 问题修复

#### 任务1: 修复失败测试 (1.5小时)

**1.1 修复factory测试** (30分钟)

```bash
# 运行失败测试
pytest tests/test_core_ai_client_factory.py::TestCreateAIClient::test_create_client_without_mock_raises_error -v

# 分析问题
# 预期: 未设置ENABLE_MOCK_AI时应抛出异常
# 实际: 未抛出异常
```

**可能原因:**
- 测试假设错误
- factory逻辑与预期不符

**修复方案:**
- 检查`core/ai_client/factory.py`的`create_client`方法
- 确认环境变量`ENABLE_MOCK_AI`的处理逻辑
- 更新测试或实现

**1.2 修复Redis测试** (20分钟)

```bash
# 启动Redis (见任务2)
pytest tests/test_core_redis.py::TestRedisStreamSubscriber::test_get_message_with_data -v
```

**依赖:** 任务2完成

**1.3 修复Mock客户端测试** (40分钟)

```bash
# 运行Mock Image测试
pytest tests/test_mock_ai_clients.py -v -k "test_generate_single_image or test_generate_multiple_images"
```

**问题分析:**
- 返回类型不匹配
- 可能是AIResponse初始化问题

**修复步骤:**
1. 检查`core/ai_client/base.py`的`AIResponse`定义
2. 检查`mock_text2image_client.py`的返回值
3. 确保类型一致

#### 任务2: 启动Redis服务 (30分钟)

**方案1: 使用Docker (推荐)**

```bash
# 停止旧容器（如果有）
docker stop redis && docker rm redis

# 启动Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:latest

# 验证运行
docker ps

# 测试连接
export PATH="/root/.local/bin:$PATH"
uv run python -c "import redis; r=redis.Redis(host='localhost',port=6379,db=0); print(r.ping())"
```

**方案2: 使用系统包**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis

# 验证
redis-cli ping
```

**验证健康检查:**

```bash
# 运行健康检查测试
pytest tests/test_health_check.py::TestHealthCheckEndpoint::test_health_check_cache_status -v

# 应该显示: cache status = healthy
```

#### 任务3: 修复日志目录 (15分钟)

**方案1: 创建目录 (推荐)**

```bash
# 创建日志目录
sudo mkdir -p /var/log/ai_story
sudo chown $USER:$USER /var/log/ai_story

# 验证权限
ls -ld /var/log/ai_story
```

**方案2: 使用相对路径**

如果无法创建/var/log目录，修改settings使用相对路径:

```python
# config/settings/base.py
import os
from pathlib import Path

# 使用项目根目录下的logs
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    # ...
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'django.log'),  # 使用相对路径
            # ...
        },
    },
}
```

**创建.gitignore条目:**

```bash
# .gitignore
logs/
*.log
```

#### 任务4: 运行完整测试套件 (30分钟)

```bash
# 运行所有测试
export PATH="/root/.local/bin:$PATH"
uv run pytest tests/ -v --cov=apps --cov=core --cov-report=term-missing --cov-report=html:htmlcov

# 查看结果
echo "通过率: ..."
echo "覆盖率: ..."

# 验证目标
# - 测试通过率: 100% (99/99)
# - 覆盖率: 18% (保持或提升)
```

**成功标准:**
- ✅ 0个失败测试
- ✅ 0个错误
- ✅ 所有健康检查测试通过
- ✅ Redis测试通过

### 下午 (2.5小时) - 覆盖率提升

#### 任务5: 提升测试覆盖率至25% (2小时)

**当前覆盖率: 18%**
**目标覆盖率: 25%**
**需要提升: +7%**

**5.1 分析覆盖率报告** (20分钟)

```bash
# 打开覆盖率报告
# htmlcov/index.html

# 识别低覆盖率模块:
# - apps/projects/views.py (704行, 0%覆盖)
# - apps/content/processors/*.py (关键但未覆盖)
# - core/pipeline/orchestrator.py (50%覆盖，需提升)
```

**5.2 为关键模块添加测试** (80分钟)

**优先级1: Pipeline处理器** (40分钟)

```python
# tests/test_content_processors.py
import pytest
from apps.content.processors.llm_stage import LLMStageProcessor

@pytest.mark.django_db
class TestLLMStageProcessor:
    """LLM Stage处理器测试"""

    def test_processor_initialization(self):
        """测试处理器初始化"""
        processor = LLMStageProcessor()
        assert processor is not None
        assert processor.stage_name == 'rewrite'

    def test_process_with_mock_client(self, test_project):
        """测试使用Mock客户端处理"""
        processor = LLMStageProcessor()
        result = processor.process(test_project.id)

        assert result['status'] == 'success'
        assert 'content' in result

    def test_process_error_handling(self, test_project):
        """测试错误处理"""
        processor = LLMStageProcessor()
        # 模拟错误场景
        result = processor.process(test_project.id, simulate_error=True)

        assert result['status'] == 'error'
```

**优先级2: API视图** (30分钟)

```python
# tests/test_projects_views.py
import pytest
from django.test import Client
from apps.projects.models import Project

@pytest.mark.django_db
class TestProjectViews:
    """项目视图测试"""

    def test_project_list_view(self):
        """测试项目列表视图"""
        client = Client()
        response = client.get('/api/v1/projects/')

        assert response.status_code == 200
        data = response.json()
        assert 'results' in data

    def test_project_create_view(self):
        """测试项目创建视图"""
        client = Client()
        data = {
            'name': '测试项目',
            'description': '测试描述',
        }
        response = client.post('/api/v1/projects/', data)

        assert response.status_code == 201
        project = Project.objects.get(id=response.json()['id'])
        assert project.name == '测试项目'
```

**优先级3: 服务层** (10分钟)

```python
# tests/test_services.py
import pytest
from apps.projects.services import ProjectService

@pytest.mark.django_db
class TestProjectService:
    """项目服务测试"""

    def test_create_project(self):
        """测试创建项目服务"""
        service = ProjectService()
        project = service.create_project(
            name='服务创建项目',
            description='通过服务创建',
        )

        assert project.id is not None
        assert project.name == '服务创建项目'
```

**5.3 验证覆盖率提升** (20分钟)

```bash
# 运行测试并生成新报告
uv run pytest tests/ --cov=apps --cov=core --cov-report=html:htmlcov

# 对比覆盖率
# 旧: 18%
# 新: 目标25%

# 如果未达标，继续添加测试
```

#### 任务6: 质量审查与总结 (30分钟)

**6.1 代码质量检查**

```bash
# 运行所有测试
uv run pytest tests/ -v

# 检查覆盖率
uv run pytest tests/ --cov=apps --cov=core --cov-report=term

# 验证SOLID原则
# - 检查新增代码是否符合单一职责
# - 检查接口是否专一
# - 检查依赖是否合理
```

**6.2 创建Day 3总结**

记录以下内容:
- 修复的测试问题
- 覆盖率提升情况
- 遇到的挑战和解决方案
- 下一步计划

**6.3 更新进度跟踪**

更新`phase-1-progress.md`:
- Story 1.4进度
- 测试覆盖率数据
- 问题修复情况

---

## 成功标准

### Day 3完成标准

**必须达成:**
- [x] 0个失败测试 (99/99通过)
- [x] 0个错误
- [x] Redis服务运行并测试通过
- [x] 日志目录创建并可写
- [x] 覆盖率提升至25%

**期望达成:**
- [ ] 核心模块单元测试完成
- [ ] Pipeline处理器测试完成
- [ ] API视图测试完成

**可选:**
- [ ] 集成测试编写
- [ ] 性能测试基准建立

---

## 故障排查

### 问题1: Docker未安装

**错误:** `docker: command not found`

**解决方案:**
```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到docker组
sudo usermod -aG docker $USER
newgrp docker
```

### 问题2: Redis连接失败

**错误:** `Error 111 connecting to localhost:6379`

**解决方案:**
```bash
# 检查Redis是否运行
docker ps | grep redis

# 查看Redis日志
docker logs redis

# 重启Redis
docker restart redis
```

### 问题3: 日志目录权限问题

**错误:** `PermissionError: [Errno 13] Permission denied`

**解决方案:**
```bash
# 方案1: 修改权限
sudo chown -R $USER:$USER /var/log/ai_story

# 方案2: 使用相对路径（推荐）
# 见任务3方案2
```

### 问题4: 测试仍然失败

**错误:** 测试失败原因不清楚

**解决方案:**
```bash
# 详细输出
pytest tests/... -vv -s

# 只运行失败测试
pytest tests/ --lf

# 进入pdb调试
pytest tests/... --pdb
```

---

## 资源清单

### 时间估算

| 任务 | 预计用时 | 优先级 |
|------|---------|--------|
| 修复factory测试 | 30分钟 | 🔴 高 |
| 修复Redis测试 | 20分钟 | 🔴 高 |
| 修复Mock测试 | 40分钟 | 🔴 高 |
| 启动Redis | 30分钟 | 🔴 高 |
| 修复日志目录 | 15分钟 | 🟡 中 |
| 运行测试套件 | 30分钟 | 🔴 高 |
| 分析覆盖率 | 20分钟 | 🟡 中 |
| 添加处理器测试 | 40分钟 | 🟡 中 |
| 添加视图测试 | 30分钟 | 🟡 中 |
| 添加服务测试 | 10分钟 | 🟢 低 |
| 质量审查 | 30分钟 | 🟡 中 |

**总计:** 5小时

### 文件清单

**需要创建的文件:**
1. `tests/test_content_processors.py` - 处理器测试
2. `tests/test_projects_views.py` - 视图测试
3. `tests/test_services.py` - 服务测试
4. `logs/.gitkeep` - 日志目录占位
5. `_bmad-output/planning-artifacts/day-3-summary.md` - Day 3总结

**需要修改的文件:**
1. `core/ai_client/factory.py` - 可能修复
2. `core/ai_client/mock_text2image_client.py` - 可能修复
3. `config/settings/base.py` - 日志路径
4. `phase-1-progress.md` - 进度更新

---

## 风险管理

### 高风险任务

**1. 修复失败测试**
- **风险:** 修复可能引入新问题
- **缓解:**
  - 一次修复一个测试
  - 修复后立即验证
  - 保持Git提交原子性

**2. Redis启动**
- **风险:** Docker环境问题
- **缓解:**
  - 提前验证Docker可用
  - 准备备用方案（系统包）
  - 检查端口6379占用

### 应急计划

**如果修复测试超时:**
1. 优先修复关键测试（Redis相关）
2. 跳过低优先级测试
3. 标记为已知问题

**如果Redis无法启动:**
1. 使用mock Redis进行测试
2. 将Redis问题记录为技术债务
3. 继续其他任务

---

## 总结

### Day 3核心目标

**质量第一:**
- ✅ 100%测试通过
- ✅ 所有阻塞问题解决
- ✅ 覆盖率稳步提升

**效率优先:**
- ✅ 5小时完成核心任务
- ✅ 建立稳固测试基线
- ✅ 为后续开发扫清障碍

### 预期成果

**测试指标:**
- 通过率: 92.9% → 100%
- 覆盖率: 18% → 25%
- 失败测试: 5 → 0

**功能指标:**
- Redis: 不可用 → 可用
- 日志系统: 配置完善
- 健康检查: 100%通过

**质量指标:**
- SOLID原则: 保持100%
- 代码审查: 全部通过
- 技术债务: 显著减少

### 下一步预览

**Day 4建议:**
- Story 1.4完成 (核心模块测试)
- Story 3.1启动 (WebSocket验证)
- 集成测试编写

**Week 1目标:**
- Epic 1: 80%完成
- Epic 2: 30%完成
- Epic 3: 10%完成

---

**推荐:** 执行方案A (质量优先) ⭐

**理由:** 质量优先，基线稳固，为后续开发奠定坚实基础

**准备时间:** 5分钟（阅读本计划）
**执行时间:** 5小时
**验证时间:** 30分钟

**总投入:** 5.5小时

**预期收益:** 测试通过率100%，所有阻塞问题解决，为Day 4-5加速铺平道路

---

*计划制定时间: 2026-01-27*
*计划版本: 1.0 Final*
*基于: Day 2执行成果与质量审查*
