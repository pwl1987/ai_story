# CLAUDE.md - 提示词管理域 (prompts)

[根目录](../../CLAUDE.md) > [backend](../) > [apps](../) > **prompts**

> 最后更新: 2026-01-26 12:08:52

---

## 模块职责

提示词管理域负责：
- 提示词集管理（PromptTemplateSet）
- 提示词模板管理（PromptTemplate）
- 全局变量管理（GlobalVariable）
- 支持Jinja2模板语法

---

## 入口与启动

### 主要文件

| 文件 | 职责 |
|------|------|
| [models.py](./models.py) | 提示词数据模型（3个模型） |
| [views.py](./views.py) | 提示词API视图 |
| [services.py](./services.py) | 提示词渲染服务 |
| [serializers.py](./serializers.py) | DRF序列化器 |
| [urls.py](./urls.py) | URL配置 |

---

## 对外接口

### 数据模型

- **PromptTemplateSet** - 提示词集（可复用）
- **PromptTemplate** - 提示词模板（支持Jinja2）
- **GlobalVariable** - 全局变量

### API端点

- GET/POST `/api/v1/prompts/sets/` - 提示词集列表/创建
- GET/PUT/DELETE `/api/v1/prompts/sets/{id}/` - 提示词集详情
- GET/POST `/api/v1/prompts/templates/` - 模板列表/创建
- GET/POST `/api/v1/prompts/variables/` - 全局变量列表/创建

---

## 关键依赖

```python
# 依赖的模块
from apps.projects.models import Project
from apps.models.models import ModelProvider
from jinja2 import Template
```

---

## 测试覆盖

- ❌ 无单元测试
- 需要添加提示词管理测试

---

## 变更记录

### 2026-01-26 12:08:52
- 初始化提示词管理域文档
