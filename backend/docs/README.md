# 后端文档快速参考

> 📚 **完整文档请访问**: [../../docs/](../../docs/)

---

## 🎯 快速导航

### 📖 项目文档
- [文档中心](../../docs/index.md) - 所有文档的导航入口
- [项目总览](../../docs/overview.md) - 项目简介、技术栈、系统架构
- [快速开始](../../docs/QUICKSTART.md) - 5分钟快速上手

### 👨‍💻 技术文档
- [API文档](../../docs/technical/#api文档) - RESTful API接口说明
- [日志系统](../../docs/technical/logging/) - 日志配置和使用
- [性能监控](../../docs/technical/monitoring/) - 系统性能监控
- [测试文档](../../docs/testing/) - 测试策略和覆盖率

### 🔧 运维指南
- [部署指南](../../docs/guides/deployment/) - 生产环境部署步骤
- [故障排查](../../docs/guides/troubleshooting/) - 常见问题解决方案
- [管理员指南](../../docs/guides/admin/) - Django Admin使用说明

---

## 🔧 常用命令

### 启动服务

```bash
# 开发环境
cd backend
./run_asgi.sh

# 生产环境（使用gunicorn）
gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 数据库操作

```bash
# 运行迁移
python manage.py migrate

# 创建迁移
python manage.py makemigrations

# 检查迁移状态
python manage.py showmigrations
```

### 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest apps/proxy/tests/

# 查看测试覆盖率
pytest --cov=apps/proxy --cov-report=html
```

### Celery任务

```bash
# 启动Celery Worker
celery -A config worker -Q llm,image,video -l info

# 启动Celery Beat（定时任务）
celery -A config beat -l info
```

---

## 📋 后端模块架构

详细的模块架构文档请参考 [CLAUDE.md](../CLAUDE.md)

### 核心模块

- **config/** - Django配置和Celery配置
- **core/** - 核心基础设施
  - `ai_client/` - AI客户端抽象层
  - `pipeline/` - 工作流引擎
  - `redis/` - Redis Pub/Sub
  - `services/` - 共享服务
- **apps/** - 业务领域模块
  - `projects/` - 项目管理域（聚合根）
  - `content/` - 内容生成域
  - `prompts/` - 提示词管理域
  - `models/` - 模型管理域
  - `users/` - 用户管理域
  - `proxy/` - 代理管理域（Epic 9）

---

## 🔗 相关文档链接

### 历史文档（已归档）

以下文档已迁移到项目文档中心，请访问新位置：

| 旧位置 | 新位置 |
|--------|--------|
| `backend/docs/ADMIN_GUIDE.md` | [docs/guides/admin/](../../docs/guides/admin/) |
| `backend/docs/LOGGING.md` | [docs/technical/logging/](../../docs/technical/logging/) |
| `backend/docs/PERFORMANCE_MONITORING.md` | [docs/technical/monitoring/](../../docs/technical/monitoring/) |
| `backend/docs/deployment/` | [docs/guides/deployment/](../../docs/guides/deployment/) |
| `backend/docs/troubleshooting/` | [docs/guides/troubleshooting/](../../docs/guides/troubleshooting/) |
| `backend/_bmad-output/` | [archive/_bmad-output-legacy-backend/](../../archive/_bmad-output-legacy-backend/) |

### 代理管理文档（Epic 9）

完整的代理管理系统文档请参考：
- [安装指南](../docs/proxy/INSTALLATION.md)
- [配置指南](../docs/proxy/CONFIGURATION.md)
- [使用指南](../docs/proxy/USAGE.md)
- [API文档](../docs/proxy/API.md)
- [故障排查](../docs/proxy/TROUBLESHOOTING.md)
- [安全指南](../docs/proxy/SECURITY.md)

---

## 🆘 获取帮助

如果您需要技术支持：
1. 查看 [文档中心](../../docs/index.md)
2. 阅读 [项目总览](../../docs/overview.md)
3. 检查 [常见问题](../../docs/guides/troubleshooting/)
4. 提交Issue到项目仓库

---

**最后更新**: 2026-01-31
**维护者**: AI Story Development Team
