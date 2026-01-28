# 常见问题排查

> 本文档涵盖常见问题、原因和解决方案

---

## 问题分类

- [启动问题](#启动问题)
- [性能问题](#性能问题)
- [集成问题](#集成问题)
- [测试问题](#测试问题)

---

## 启动问题

### 1. Celery Worker无法接收任务

**现象**：
```
任务状态一直是pending，Celery无日志输出
```

**原因**：
- Celery Worker未启动或崩溃
- 队列名称不匹配
- Redis连接失败

**解决方案**：
```bash
# 1. 检查Celery Worker状态
ps aux | grep celery

# 2. 检查队列配置
grep "task_routes" config/celery.py

# 3. 重启Celery Worker
pkill -f celery
uv run celery -A config worker -Q llm,image,video -l info

# 4. 清除Python缓存（代码更新后）
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} +
rm -rf .venv/lib/python*/site-packages/*/__pycache__

# 5. 使用--purge清除旧任务
uv run celery -A config worker -Q llm,image,video -l info --purge
```

---

### 2. WebSocket连接失败

**现象**：
```
前端WebSocket连接失败，无实时进度推送
```

**原因**：
- 使用了runserver而非ASGI服务器
- Redis Channels配置错误
- 防火墙阻止WebSocket连接

**解决方案**：
```bash
# 1. 使用ASGI服务器
./run_asgi.sh  # 正确
uv run python manage.py runserver  # 错误

# 2. 检查Redis Channels配置
grep "CHANNEL_LAYERS" config/settings/base.py

# 3. 检查Redis是否运行
redis-cli ping

# 4. 检查WebSocket路由
python manage.py show_urls | grep ws/
```

---

### 3. 数据库迁移失败

**现象**：
```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

**原因**：
- 数据库状态与迁移记录不匹配
- 误删迁移文件

**解决方案**：
```bash
# 1. 查看迁移状态
uv run python manage.py showmigrations

# 2. 回滚到指定迁移
uv run python manage.py migrate app_name migration_number

# 3. 伪造迁移（如果数据库已是最新）
uv run python manage.py migrate --fake

# 4. 重建数据库（开发环境）
rm db.sqlite3
uv run python manage.py migrate
```

---

## 性能问题

### 4. 工作流执行缓慢

**现象**：
```
5个阶段执行时间 > 5分钟
```

**原因**：
- 使用真实AI API而非Mock
- 网络延迟
- Celery Worker单线程处理

**解决方案**：
```bash
# 1. 使用Mock环境测试
# 参考 docs/deployment/02-mock-environment.md

# 2. 增加Celery Worker并发数
uv run celery -A config worker -Q llm,image,video -c 4 -l info

# 3. 使用Celery autoscaling
uv run celery -A config worker -Q llm,image,video --autoscale=4,2 -l info

# 4. 优化数据库查询
uv run python manage.py debugsqlshell
```

---

### 5. 内存占用过高

**现象**：
```
Celery Worker内存占用 > 1GB
```

**原因**：
- 任务结果未清理
- ORM查询未使用iterator()
- Django QuerySet缓存

**解决方案**：
```python
# 1. 使用iterator()处理大量数据
for item in Model.objects.iterator():
    process(item)

# 2. 清理旧任务结果
from celery.result import AsyncResult
# 定期清理过期任务

# 3. 使用only()限制查询字段
Model.objects.only('id', 'name')
```

---

## 集成问题

### 6. AI客户端调用失败

**现象**：
```
core.ai_client.base.AIResponse with success=False
```

**原因**：
- API Key无效
- API URL错误
- 超时时间过短

**解决方案**：
```python
# 1. 验证配置
provider = ModelProvider.objects.get(id=xxx)
print(f"API URL: {provider.api_url}")
print(f"API Key: {provider.api_key[:10]}...")

# 2. 测试连接
client = create_ai_client(provider)
await client.health_check()

# 3. 增加超时时间
# 在ModelProvider中配置
provider.timeout = 60  # 60秒
```

---

### 7. Pipeline阶段失败

**现象**：
```
阶段状态: failed
错误: "所有XXX生成都失败了"
```

**原因**：
- 提示词字段不兼容
- Mock响应格式变化
- 缺少必要配置

**解决方案**：
```python
# 1. 检查阶段输出数据
stage = ProjectStage.objects.get(project_id=xxx, stage_type='xxx')
print(stage.output_data)
print(stage.error_message)

# 2. 检查字段兼容性
# 参考 backend/CAMERA_MOVEMENT_FIX_REPORT.md

# 3. 使用端到端测试验证
uv run python scripts/test_e2e_api.py
```

---

## 测试问题

### 8. 测试数据库锁死

**现象**：
```
django.db.utils.OperationalError: database is locked
```

**原因**：
- SQLite并发写入限制
- 测试间未隔离数据库

**解决方案**：
```bash
# 1. 使用--parallel选项
uv run pytest --parallel

# 2. 每个测试使用独立数据库
pytest --create-db

# 3. 使用PostgreSQL（生产）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        ...
    }
}
```

---

### 9. asyncio死锁

**现象**：
```
RuntimeError: Single thread executor already being used, would deadlock
```

**原因**：
- 异步函数中直接调用同步ORM
- sync_to_async嵌套调用

**解决方案**：
```python
# 1. 使用sync_to_async_wrapper包装ORM调用
from apps.projects.utils import sync_to_async_wrapper

async def async_func():
    # 错误 - 直接调用ORM
    obj = MyModel.objects.get(id=1)
    
    # 正确 - 使用sync_to_async_wrapper
    obj = await sync_to_async_wrapper(MyModel.objects.get)(id=1)

# 2. 参考异步ORM验证报告
# backend/ASYNC_ORM_VERIFICATION_REPORT.md
```

---

## 调试技巧

### 查看详细日志

```bash
# Django日志
export DJANGO_LOG_LEVEL=DEBUG

# Celery日志
uv run celery -A config worker -Q llm,image,video -l debug

# 查看特定日志
tail -f logs/celery.log | grep ERROR
```

### 进入Django Shell

```bash
uv run python manage.py shell

# 测试ORM查询
from apps.projects.models import Project
Project.objects.all()

# 测试AI客户端
from core.ai_client.factory import create_ai_client
client = create_ai_client(provider)
await client.generate(prompt='测试')
```

### 监控Redis

```bash
# 查看所有键
redis-cli keys "*"

# 查看队列长度
redis-cli llen "celery:llm"

# 清空队列（危险！）
redis-cli del "celery:llm"
```

---

## 获取帮助

- [文档索引](../../)
- [GitHub Issues](https://github.com/your-repo/issues)
- 技术支持: support@example.com

---

**最后更新**: 2026-01-28
**维护者**: Claude Code
