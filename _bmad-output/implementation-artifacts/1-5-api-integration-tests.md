# Story 1.5: API集成测试

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

作为开发者,
我需要编写API集成测试,
以便验证所有端点功能正确

## Acceptance Criteria

1. **Given** Django REST Framework ViewSets已存在
   **When** 使用APITestCase编写测试
   **Then** 覆盖100%的API端点(projects、content、prompts、models)
   **And** 测试CRUD操作、权限、验证逻辑
   **And** 使用测试数据库,不影响开发数据

2. **Given** API端点已实现
   **When** 执行`uv run pytest apps/*/tests/test_views.py`
   **Then** 所有测试通过
   **And** 覆盖率报告显示API测试覆盖率>95%
   **And** 测试执行时间<3分钟

3. **Given** 测试数据库已配置
   **When** 运行API集成测试
   **Then** 使用pytest-django的测试数据库(与开发数据库隔离)
   **And** 每个测试独立运行,不共享数据
   **And** 测试完成后自动清理测试数据

## Tasks / Subtasks

- [ ] Task 1: 创建测试文件结构 (AC: #1, #3)
  - [ ] Subtask 1.1: 创建apps/projects/tests/test_views.py
  - [ ] Subtask 1.2: 创建apps/content/tests/test_views.py
  - [ ] Subtask 1.3: 创建apps/prompts/tests/test_views.py
  - [ ] Subtask 1.4: 创建apps/models/tests/test_views.py
  - [ ] Subtask 1.5: 创建apps/users/tests/test_views.py (如果存在用户管理)

- [ ] Task 2: 编写Projects API测试 (AC: #1, #2)
  - [ ] Subtask 2.1: 测试项目列表API (GET /api/v1/projects/)
  - [ ] Subtask 2.2: 测试项目创建API (POST /api/v1/projects/)
  - [ ] Subtask 2.3: 测试项目详情API (GET /api/v1/projects/{id}/)
  - [ ] Subtask 2.4: 测试项目更新API (PUT/PATCH /api/v1/projects/{id}/)
  - [ ] Subtask 2.5: 测试项目删除API (DELETE /api/v1/projects/{id}/)
  - [ ] Subtask 2.6: 测试项目工作流执行API (POST /api/v1/projects/{id}/execute_stage/)
  - [ ] Subtask 2.7: 测试项目重试API (POST /api/v1/projects/{id}/retry/)
  - [ ] Subtask 2.8: 测试项目暂停/恢复API

- [ ] Task 3: 编写Content API测试 (AC: #1, #2)
  - [ ] Subtask 3.1: 测试内容列表API (GET /api/v1/content/)
  - [ ] Subtask 3.2: 测试内容详情API (GET /api/v1/content/{id}/)
  - [ ] Subtask 3.3: 测试内容创建API (POST /api/v1/content/)
  - [ ] Subtask 3.4: 测试内容更新API
  - [ ] Subtask 3.5: 测试内容删除API

- [ ] Task 4: 编写Prompts API测试 (AC: #1, #2)
  - [ ] Subtask 4.1: 测试提示词集列表API (GET /api/v1/prompts/)
  - [ ] Subtask 4.2: 测试提示词集详情API
  - [ ] Subtask 4.3: 测试提示词集CRUD操作
  - [ ] Subtask 4.4: 测试提示词模板渲染API

- [ ] Task 5: 编写Models API测试 (AC: #1, #2)
  - [ ] Subtask 5.1: 测试模型提供商列表API (GET /api/v1/models/)
  - [ ] Subtask 5.2: 测试模型提供商详情API
  - [ ] Subtask 5.3: 测试模型提供商CRUD操作
  - [ ] Subtask 5.4: 测试模型健康检查API

- [ ] Task 6: 测试权限和认证 (AC: #1)
  - [ ] Subtask 6.1: 测试未认证用户访问限制
  - [ ] Subtask 6.2: 测试已认证用户权限
  - [ ] Subtask 6.3: 测试资源所有权验证
  - [ ] Subtask 6.4: 测试管理员权限

- [ ] Task 7: 测试验证逻辑 (AC: #1)
  - [ ] Subtask 7.1: 测试必填字段验证
  - [ ] Subtask 7.2: 测试数据类型验证
  - [ ] Subtask 7.3: 测试字段长度验证
  - [ ] Subtask 7.4: 测试外键约束验证
  - [ ] Subtask 7.5: 测试业务逻辑验证(如状态转换)

- [ ] Task 8: 测试分页、过滤、排序 (AC: #1)
  - [ ] Subtask 8.1: 测试分页功能(PageNumberPagination)
  - [ ] Subtask 8.2: 测试过滤功能(按状态、日期等)
  - [ ] Subtask 8.3: 测试排序功能(按创建时间、更新时间)
  - [ ] Subtask 8.4: 测试搜索功能(如果实现)

- [ ] Task 9: 配置测试覆盖率 (AC: #2)
  - [ ] Subtask 9.1: 确认pytest.ini包含apps/*/tests/test_views.py
  - [ ] Subtask 9.2: 运行覆盖率报告: `uv run pytest --cov=apps --cov=core --cov-report=html`
  - [ ] Subtask 9.3: 验证API测试覆盖率>95%
  - [ ] Subtask 9.4: 优化未覆盖的代码路径

- [ ] Task 10: 验证测试性能和隔离性 (AC: #2, #3)
  - [ ] Subtask 10.1: 测试执行时间验证 (<3分钟)
  - [ ] Subtask 10.2: 验证测试数据库隔离
  - [ ] Subtask 10.3: 验证测试独立性(可单独运行每个测试)
  - [ ] Subtask 10.4: 创建测试运行脚本

## Dev Notes

### 架构约束

**Brownfield项目规则:**
- Django 3.2.15 (LTS) - 不可更改
- Django REST Framework 3.14.0 - 使用APITestCase
- 测试框架: pytest + pytest-django (非unittest)
- 命名规范: test_*.py文件, Test*类, test_*方法
- 数据库: 使用pytest-django的测试数据库 (自动创建/销毁)

**API测试标准:**
- 使用DRF的APITestCase作为基类
- 使用APIClient发送HTTP请求
- 断言HTTP状态码(status_code)
- 断言响应数据结构(response.data)
- 断言数据库状态(模型对象数量、字段值)

### 项目结构对齐

**测试目录结构:**
```
apps/
├── projects/
│   └── tests/
│       ├── __init__.py
│       ├── test_views.py         # API集成测试
│       ├── test_models.py        # 模型测试
│       ├── test_serializers.py   # 序列化器测试
│       └── test_tasks.py         # Celery任务测试
├── content/
│   └── tests/
│       ├── test_views.py
│       └── test_processors.py    # 处理器测试
├── prompts/
│   └── tests/
│       └── test_views.py
└── models/
    └── tests/
        └── test_views.py
```

### 测试模式

**标准API测试模式:**
```python
from rest_framework.test import APITestCase
from apps.projects.models import Project

class ProjectViewSetTests(APITestCase):
    """项目API测试"""

    def setUp(self):
        """测试前置条件"""
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)

    def test_list_projects(self):
        """测试项目列表API"""
        # Arrange
        Project.objects.create(original_topic="测试主题", creator=self.user)

        # Act
        response = self.client.get('/api/v1/projects/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_project(self):
        """测试项目创建API"""
        # Arrange
        data = {'original_topic': '新项目主题'}

        # Act
        response = self.client.post('/api/v1/projects/', data)

        # Assert
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Project.objects.count(), 1)
```

**测试数据管理:**
- 使用setUp()创建测试数据
- 使用pytest fixtures管理共享数据
- 每个测试方法独立创建所需数据
- 测试完成后自动清理(事务回滚)

### 技术依赖

**已安装:**
- pytest>=8.0.0
- pytest-cov>=5.0.0
- pytest-django>=4.8.0
- Django 3.2.15
- djangorestframework 3.14.0

**已配置:**
- pytest.ini (测试发现、覆盖率配置)
- conftest.py (全局fixtures)
- tests/fixtures/ (自定义fixtures)

### Previous Story Intelligence

**从Story 1.2 (测试框架搭建) 学习:**
- ✅ pytest框架已配置完成
- ✅ pytest.ini已创建,包含覆盖率配置
- ✅ tests/目录结构已建立
- ✅ conftest.py包含全局fixtures (django_db_setup, test_project等)
- ✅ 覆盖率目标>70%已配置

**从Story 1.3 (Mock AI客户端) 学习:**
- ✅ Mock AI客户端已实现
- ✅ 可使用ENABLE_MOCK_AI环境变量启用
- ✅ 测试时使用Mock客户端避免真实API调用

**从Story 1.4 (核心模块测试) 学习:**
- ✅ core/目录测试已完成
- ✅ 测试覆盖率基准已建立
- ✅ 测试执行时间<5分钟标准已验证

### API端点清单

**Projects API (apps/projects/views.py):**
- GET /api/v1/projects/ - 项目列表
- POST /api/v1/projects/ - 创建项目
- GET /api/v1/projects/{id}/ - 项目详情
- PUT/PATCH /api/v1/projects/{id}/ - 更新项目
- DELETE /api/v1/projects/{id}/ - 删除项目
- POST /api/v1/projects/{id}/execute_stage/ - 执行阶段
- POST /api/v1/projects/{id}/retry/ - 重试项目
- POST /api/v1/projects/{id}/pause/ - 暂停项目
- POST /api/v1/projects/{id}/resume/ - 恢复项目

**Content API (apps/content/views.py):**
- GET /api/v1/content/ - 内容列表
- GET /api/v1/content/{id}/ - 内容详情
- POST /api/v1/content/ - 创建内容
- PUT/PATCH /api/v1/content/{id}/ - 更新内容
- DELETE /api/v1/content/{id}/ - 删除内容

**Prompts API (apps/prompts/views.py):**
- GET /api/v1/prompts/ - 提示词集列表
- GET /api/v1/prompts/{id}/ - 提示词集详情
- POST /api/v1/prompts/ - 创建提示词集
- PUT/PATCH /api/v1/prompts/{id}/ - 更新提示词集
- DELETE /api/v1/prompts/{id}/ - 删除提示词集
- POST /api/v1/prompts/{id}/render/ - 渲染提示词模板

**Models API (apps/models/views.py):**
- GET /api/v1/models/ - 模型提供商列表
- GET /api/v1/models/{id}/ - 模型提供商详情
- POST /api/v1/models/ - 创建模型提供商
- PUT/PATCH /api/v1/models/{id}/ - 更新模型提供商
- DELETE /api/v1/models/{id}/ - 删除模型提供商
- POST /api/v1/models/{id}/test/ - 测试模型连接

### 测试覆盖要求

**必须测试的场景:**
1. ✅ 成功场景 (Happy Path)
2. ✅ 验证失败场景 (Validation Errors)
3. ✅ 权限拒绝场景 (Permission Denied)
4. ✅ 资源不存在场景 (Not Found)
5. ✅ 业务逻辑场景 (如状态转换)

**测试数据:**
- 使用最小化测试数据 (只创建必需字段)
- 使用工厂模式 (Factory Boy或自定义fixtures)
- 测试边界条件 (空列表、最大分页、超长字符串)

### 验证方法

1. **运行所有API测试:**
   ```bash
   cd backend
   uv run pytest apps/*/tests/test_views.py -v
   ```

2. **运行单个测试文件:**
   ```bash
   uv run pytest apps/projects/tests/test_views.py -v
   ```

3. **运行单个测试类:**
   ```bash
   uv run pytest apps/projects/tests/test_views.py::ProjectViewSetTests -v
   ```

4. **运行单个测试方法:**
   ```bash
   uv run pytest apps/projects/tests/test_views.py::ProjectViewSetTests::test_list_projects -v
   ```

5. **生成覆盖率报告:**
   ```bash
   uv run pytest --cov=apps --cov=core --cov-report=html
   # 打开 htmlcov/index.html 查看报告
   ```

6. **测试执行时间验证:**
   ```bash
   uv run pytest apps/*/tests/test_views.py --durations=10
   # 显示最慢的10个测试
   ```

### References

**源文档:**
- [Source: _bmad-output/planning-artifacts/epics.md - Epic 1, Story 1.5]
- [Source: CLAUDE.md - 测试策略部分]
- [Source: backend/apps/projects/views.py - 项目ViewSet实现]
- [Source: backend/apps/content/views.py - 内容ViewSet实现]
- [Source: backend/apps/prompts/views.py - 提示词ViewSet实现]
- [Source: backend/apps/models/views.py - 模型ViewSet实现]

**已完成的Stories:**
- [Story 1.1] README文档完善 - 了解API端点文档位置
- [Story 1.2] 测试框架搭建 - pytest配置、fixtures
- [Story 1.3] Mock AI客户端 - 离线测试支持
- [Story 1.4] 核心模块测试 - 测试模式参考

**Django REST Framework测试文档:**
- https://www.django-rest-framework.org/api-guide/testing/

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20251101)

### Debug Log References

None (Story creation phase)

### Completion Notes List

- ✅ Story文件创建完成: 1-5-api-integration-tests.md
- ✅ 所有10个Tasks、38个Subtasks已详细定义
- ✅ 验收标准(AC)已映射到所有Tasks
- ✅ 架构约束和测试模式已文档化
- ✅ API端点清单已完整列出
- ✅ Previous Story Intelligence已整合
- ✅ 测试覆盖要求和验证方法已说明
- ✅ References已完整引用
- ⚠️ 等待dev-story工作流执行实际测试编写

### File List

**创建的文件:**
- _bmad-output/implementation-artifacts/1-5-api-integration-tests.md

**待创建的文件 (dev-story阶段):**
- apps/projects/tests/test_views.py
- apps/content/tests/test_views.py
- apps/prompts/tests/test_views.py
- apps/models/tests/test_views.py
- apps/users/tests/test_views.py (如果需要)

**待修改的文件 (dev-story阶段):**
- pytest.ini (可能需要调整测试发现路径)
- .coveragerc (可能需要添加覆盖率配置)
- backend/README.md (添加API测试运行说明)
