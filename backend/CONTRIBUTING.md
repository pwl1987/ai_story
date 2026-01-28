# 贡献者指南

> **Epic 7.4: 贡献者指南**
> **更新时间**: 2026-01-28

---

## 欢迎贡献

感谢您对AI Story生成系统的关注！我们欢迎各种形式的贡献。

---

## 贡献类型

### 1. 代码贡献

- Bug修复
- 新功能开发
- 性能优化
- 代码重构
- 测试补充

### 2. 文档贡献

- 文档改进
- 示例代码
- 翻译
- 教程编写

### 3. 其他贡献

- 问题报告
- 功能建议
- 代码审查
- 社区支持

---

## 开发环境设置

### 前置要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git
- uv (Python包管理器)

### 后端开发环境

```bash
# 克隆仓库
git clone https://github.com/your-org/ai_story.git
cd ai_story/backend

# 安装依赖
uv sync

# 运行迁移
uv run python manage.py migrate

# 创建管理员
uv run python manage.py createsuperuser

# 启动开发服务器
./run_asgi.sh
```

### 前端开发环境

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### Celery Worker

```bash
cd backend

# 启动Celery Worker
uv run celery -A config worker -Q llm,image,video -l info
```

### Redis

```bash
# 使用Docker启动Redis
docker run -d --name happy-redis -p 6379:6379 redis:7-alpine
```

---

## 开发工作流

### 1. Fork和Clone

```bash
# Fork仓库到你的GitHub账号
# Clone你的fork
git clone https://github.com/your-username/ai_story.git
cd ai_story
```

### 2. 创建分支

```bash
# 从develop分支创建你的功能分支
git checkout develop
git checkout -b feature/your-feature-name
```

**分支命名规范**:
- `feature/xxx` - 新功能
- `fix/xxx` - Bug修复
- `refactor/xxx` - 代码重构
- `docs/xxx` - 文档更新
- `test/xxx` - 测试相关

### 3. 编写代码

遵循项目的编码规范（详见下文）。

### 4. 编写测试

```bash
cd backend

# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest apps/projects/tests/

# 生成覆盖率报告
uv run pytest --cov=apps.projects --cov-report=html
```

### 5. 提交代码

```bash
git add .
git commit -m "feat: add user authentication feature"
```

**Commit Message规范**:
- `feat:` 新功能
- `fix:` Bug修复
- `docs:` 文档更新
- `style:` 代码格式（不影响功能）
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

### 6. 推送并创建Pull Request

```bash
git push origin feature/your-feature-name
```

然后在GitHub上创建Pull Request。

---

## 编码规范

### Python代码规范 (PEP 8)

#### 命名规范

```python
# 类名：PascalCase
class UserService:
    pass

# 函数/变量：snake_case
def get_user_profile(user_id):
    pass

# 常量：UPPER_CASE
MAX_RETRY_COUNT = 3

# 私有成员：前导下划线
def _internal_method(self):
    pass
```

#### 导入顺序

```python
# 1. 标准库
import os
from datetime import datetime

# 2. 第三方库
import django
from rest_framework import serializers

# 3. 本地应用
from apps.projects.models import Project
from core.pipeline.base import PipelineStage
```

#### 文档字符串

```python
def process_project(project_id: str, user_id: str) -> bool:
    """
    处理项目工作流

    Args:
        project_id: 项目ID
        user_id: 用户ID

    Returns:
        bool: 处理成功返回True，否则返回False

    Raises:
        Project.DoesNotExist: 项目不存在
        ValidationError: 验证失败

    Examples:
        >>> process_project("123", "456")
        True
    """
    pass
```

---

### JavaScript/Vue代码规范

#### 组件命名

```javascript
// PascalCase
export default {
  name: 'UserProfile'
}
```

#### 变量命名

```javascript
// camelCase
const userName = 'John'
const userProfile = {}

// 常量：UPPER_CASE
const MAX_RETRY = 3
```

---

## SOLID原则

项目强制遵循SOLID原则：

### S - 单一职责原则 (SRP)

每个类/模块只负责一项功能。

```python
# ❌ 违反SRP
class User:
    def save_to_db(self): pass
    def send_email(self): pass
    def generate_report(self): pass

# ✅ 符合SRP
class UserRepository:
    def save(self, user): pass

class EmailService:
    def send(self, to, subject): pass

class ReportGenerator:
    def generate(self, user): pass
```

### O - 开闭原则 (OCP)

对扩展开放，对修改封闭。

```python
# ✅ 使用抽象基类
class BaseStorageBackend(ABC):
    @abstractmethod
    def save(self, file): pass

class S3StorageBackend(BaseStorageBackend):
    def save(self, file): pass  # 扩展而不修改
```

### L - 里氏替换原则 (LSP)

子类必须可替换父类。

```python
# ✅ 所有存储后端可互换
storage: BaseStorageBackend = S3StorageBackend()
storage.save(file)  # 可替换为LocalStorageBackend
```

### I - 接口隔离原则 (ISP)

接口专一，避免胖接口。

```python
# ❌ 胖接口
class FileHandler(ABC):
    @abstractmethod
    def read(self): pass
    @abstractmethod
    def write(self): pass
    @abstractmethod
    def delete(self): pass

# ✅ 专一接口
class FileReader(ABC):
    @abstractmethod
    def read(self): pass
```

### D - 依赖倒置原则 (DIP)

依赖抽象而非具体实现。

```python
# ❌ 依赖具体
class ProjectService:
    def __init__(self):
        self.storage = S3StorageBackend()

# ✅ 依赖抽象
class ProjectService:
    def __init__(self, storage: BaseStorageBackend):
        self.storage = storage
```

---

## 测试要求

### 单元测试

```python
import pytest
from apps.projects.tests.factories import ProjectFactory

@pytest.mark.django_db
class TestProjectService:
    def test_create_project(self):
        project = ProjectFactory()
        assert project.status == 'draft'
```

### 测试覆盖率

- 新代码覆盖率要求: **≥ 80%**
- 核心模块覆盖率要求: **≥ 90%**

```bash
# 检查覆盖率
uv run pytest --cov=apps.projects --cov-fail-under=80
```

---

## Pull Request指南

### PR标题格式

```
[Epic X.Y] 简短描述

例如：
[Epic 6.1] 文件上传API实现
[fix] 修复Redis连接问题
```

### PR描述模板

```markdown
## 变更类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 代码重构
- [ ] 文档更新
- [ ] 性能优化

## 变更说明
<!-- 详细描述你的变更 -->

## 相关Issue
<!-- 关联的Issue编号，例如：Closes #123 -->

## 测试
- [ ] 单元测试已通过
- [ ] 集成测试已通过
- [ ] 手动测试已完成

## 截图（如有）
<!-- 添加截图或GIF -->

## Checklist
- [ ] 代码遵循项目编码规范
- [ ] 已添加必要的文档
- [ ] 测试覆盖率≥80%
- [ ] 所有测试通过
- [ ] 已更新CHANGELOG（如有必要）
```

---

## 代码审查

### 审查要点

1. **功能正确性**: 代码是否实现了预期功能
2. **代码质量**: 是否遵循SOLID原则和编码规范
3. **测试覆盖**: 是否有足够的测试
4. **文档完整**: 是否有清晰的文档和注释
5. **性能影响**: 是否有性能问题

### 审查流程

1. 自动化检查（CI/CD）
2. 同行代码审查
3. 维护者审批
4. 合并到develop分支

---

## 问题报告

### Bug报告模板

```markdown
## Bug描述
<!-- 清晰简洁地描述bug -->

## 复现步骤
1. 步骤1
2. 步骤2
3. 步骤3

## 期望行为
<!-- 描述你期望发生什么 -->

## 实际行为
<!-- 描述实际发生了什么 -->

## 环境
- OS: [例如 Ubuntu 22.04]
- Python版本: [例如 3.11.0]
- Django版本: [例如 3.2.15]

## 截图/日志
<!-- 添加相关的截图或日志 -->

## 额外信息
<!-- 任何其他相关信息 -->
```

### 功能请求模板

```markdown
## 功能描述
<!-- 清晰描述你想要的功能 -->

## 问题/需求
<!-- 这个功能解决了什么问题或满足什么需求 -->

## 建议的解决方案
<!-- 描述你认为应该如何实现 -->

## 替代方案
<!-- 描述你考虑过的其他解决方案 -->

## 优先级
- [ ] 高
- [ ] 中
- [ ] 低
```

---

## 社区准则

### 尊重与包容

- 尊重不同观点和经验
- 使用友善和包容的语言
- 接受建设性批评
- 关注对社区最有利的事情

### 协作精神

- 优先考虑社区利益
- 欢迎不同技能水平的贡献者
- 乐于帮助和指导新手
- 分享知识和经验

---

## 获取帮助

### 文档

- [项目README](../README.md)
- [API文档](http://localhost:8000/api/schema/redoc/)
- [架构文档](../CLAUDE.md)

### 沟通渠道

- GitHub Issues: 报告问题和功能请求
- GitHub Discussions: 技术讨论和问答
- Pull Requests: 代码贡献和审查

---

## 许可证

通过贡献代码，你同意你的贡献将使用项目的许可证进行授权。

---

## 致谢

感谢所有贡献者！你的贡献让AI Story生成系统变得更好。

---

*最后更新: 2026-01-28*
*Epic 7.4: 贡献者指南*
