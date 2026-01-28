# 端到端测试快速开始指南

> **快速启动您的端到端测试环境**

---

## 🚀 5分钟快速开始

### Step 1: 配置Mock环境（30秒）

```bash
cd backend
uv run python scripts/setup_mock_env.py
uv run python scripts/create_test_project.py
```

### Step 2: 启动服务（1分钟）

```bash
# 终端1: Redis
docker run -d -p 6379:6379 redis:latest

# 终端2: Celery Worker
cd backend
uv run celery -A config worker -Q llm,image,video -l info

# 终端3: Django ASGI
cd backend
./run_asgi.sh
```

### Step 3: 运行测试（3分钟）

```bash
cd backend
uv run python scripts/test_e2e_workflow.py
```

**预期输出**:
```
============================================================
端到端工作流测试
============================================================

✓ 登录成功
✓ 找到测试项目
✓ 工作流已启动
  进度: [██████████] 5/5 | 状态: completed

✓ 工作流完成！

============================================================
✓ 端到端测试通过
============================================================
```

---

## 📋 验收清单

运行测试前，请确认：

- [ ] Redis运行中：`docker ps | grep redis`
- [ ] Celery运行中：`ps aux | grep celery`
- [ ] Django运行中：`ps aux | grep daphne`
- [ ] Mock环境已配置：`uv run python scripts/setup_mock_env.py`
- [ ] 测试项目已创建：`uv run python scripts/create_test_project.py`

---

## 🔧 常用命令

### 配置环境

```bash
# 配置Mock环境
uv run python scripts/setup_mock_env.py

# 创建测试项目
uv run python scripts/create_test_project.py
```

### 运行测试

```bash
# 端到端工作流测试
uv run python scripts/test_e2e_workflow.py

# 完整验证
uv run python scripts/verify_e2e_complete.py
```

### 运行单元测试

```bash
# Pipeline适配器测试
uv run pytest apps/projects/tests/test_pipeline_adapters.py -v

# WebSocket连接测试
uv run pytest tests/websocket/test_websocket_connection.py -v

# 性能基准测试
uv run pytest tests/benchmarks/benchmark_full_workflow.py -v
```

---

## 📚 文档索引

- [Mock环境配置指南](docs/deployment/03-mock-environment.md) - 详细的Mock环境配置
- [脚本使用指南](scripts/README.md) - 所有脚本的详细说明
- [实施总结](IMPLEMENTATION_SUMMARY.md) - 完整的实施总结报告

---

## 🐛 故障排查

### 问题: Redis连接失败

```bash
# 检查Redis是否运行
docker ps | grep redis

# 重启Redis
docker restart <container_id>
```

### 问题: Celery Worker无法启动

```bash
# 检查环境变量
echo $REDIS_URL

# 手动启动（详细日志）
uv run celery -A config worker -Q llm,image,video -l debug
```

### 问题: Django ASGI无法启动

```bash
# 检查端口占用
lsof -i :8000

# 重启ASGI
./run_asgi.sh
```

### 问题: 测试项目不存在

```bash
# 重新创建测试项目
uv run python scripts/create_test_project.py
```

---

## ✨ 高级用法

### 自定义测试项目

```python
from apps.projects.models import Project
from apps.models.models import ModelProvider

# 创建自定义项目
project = Project.objects.create(
    name='My Test Project',
    original_topic='自定义主题',
    user=user
)

# 配置Mock Providers
config = ProjectModelConfig.objects.create(project=project)
config.rewrite_providers.add(
    ModelProvider.objects.get(name='Mock LLM for E2E Test')
)
```

### 监控Celery任务

```bash
# 查看任务队列
redis-cli -n 0
> LLEN celery
> LRANGE celery 0 -1

# 查看任务结果
redis-cli -n 1
> GET celery-task-meta-<task_id>
```

### WebSocket测试

```javascript
// 在浏览器控制台测试WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/projects/PROJECT_ID/');

ws.onopen = () => console.log('已连接');
ws.onmessage = (event) => console.log('收到消息:', JSON.parse(event.data));

// 发送心跳
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() / 1000 }));
}, 30000);
```

---

## 🎯 下一步

1. **阅读文档**: 查看[实施总结](IMPLEMENTATION_SUMMARY.md)了解完整功能
2. **自定义配置**: 根据需求修改Mock响应和测试数据
3. **集成CI/CD**: 将测试集成到持续集成流程
4. **性能优化**: 参考性能测试结果进行优化

---

**需要帮助？** 查看[故障排查](#-故障排查)或[文档索引](#-文档索引)

**祝测试顺利！** 🎉
