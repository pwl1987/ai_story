# CLAUDE.md - 模型管理域 (models)

[根目录](../../CLAUDE.md) > [backend](../) > [apps](../) > **models**

> 最后更新: 2026-01-26 12:08:52

---

## 模块职责

模型管理域负责：
- AI模型提供商管理（ModelProvider）
- 模型使用日志（ModelUsageLog）
- 负载均衡策略
- API连接测试

---

## 入口与启动

### 主要文件

| 文件 | 职责 |
|------|------|
| [models.py](./models.py) | 模型提供商数据模型 |
| [views.py](./views.py) | 模型管理API视图 |
| [services.py](./services.py) | 负载均衡服务 |
| [serializers.py](./serializers.py) | DRF序列化器 |
| [urls.py](./urls.py) | URL配置 |

---

## 对外接口

### 数据模型

- **ModelProvider** - AI模型提供商
  - provider_type: llm, text2image, image2video
  - executor_class: 执行器类路径
  - 负载均衡配置

- **ModelUsageLog** - 使用日志和成本统计

### API端点

- GET/POST `/api/v1/models/providers/` - 模型列表/创建
- GET/PUT/DELETE `/api/v1/models/providers/{id}/` - 模型详情
- POST `/api/v1/models/providers/{id}/test/` - 测试连接

---

## 关键依赖

```python
# 依赖的模块
from core.ai_client.factory import create_ai_client
from apps.projects.models import ProjectModelConfig
```

---

## 测试覆盖

- ❌ 无单元测试
- 需要添加模型管理测试

---

## 变更记录

### 2026-01-26 12:08:52
- 初始化模型管理域文档
