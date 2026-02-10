# 代理管理系统 - 文档索引

**版本:** 1.0.0
**最后更新:** 2026-01-31
**Epic:** Epic 9 - 代理管理系统

---

## 📚 文档目录

### 🚀 快速开始

1. **[安装指南](INSTALLATION.md)**
   - 依赖安装
   - 数据库迁移
   - Celery Beat配置
   - 验证安装

### ⚙️ 配置指南

2. **[配置指南](CONFIGURATION.md)**
   - 环境变量配置
   - 数据库字段说明
   - Celery配置
   - Django Admin配置
   - API配置
   - 安全配置

### 📖 使用指南

3. **[使用指南](USAGE.md)**
   - Django Admin操作
   - API使用
   - 项目中配置代理
   - 数据分析
   - 最佳实践

### 🔧 技术文档

4. **[API文档](API.md)**
   - 代理配置API
   - 代理选择器API
   - 测试连接API
   - 使用日志API
   - 权限说明

### 🛠️ 运维指南

5. **[故障排查](TROUBLESHOOTING.md)**
   - 常见问题诊断
   - 错误代码说明
   - 日志分析
   - 高级诊断工具

6. **[部署清单](DEPLOYMENT_CHECKLIST.md)**
   - 部署前检查
   - 数据库部署
   - 应用部署
   - Celery部署
   - 监控配置
   - 升级流程

### 🔐 安全文档

7. **[安全指南](SECURITY.md)**
   - 密码加密机制
   - 权限控制
   - 网络安全
   - 日志安全
   - 安全事件响应

---

## 🎯 按角色查看文档

### 系统管理员

**推荐阅读顺序:**

1. [安装指南](INSTALLATION.md) - 安装系统
2. [使用指南](USAGE.md) - 日常操作
3. [故障排查](TROUBLESHOOTING.md) - 解决问题

### 开发者

**推荐阅读顺序:**

1. [配置指南](CONFIGURATION.md) - 系统配置
2. [API文档](API.md) - API集成
3. [部署清单](DEPLOYMENT_CHECKLIST.md) - 部署流程

### DevOps工程师

**推荐阅读顺序:**

1. [安装指南](INSTALLATION.md) - 安装步骤
2. [部署清单](DEPLOYMENT_CHECKLIST.md) - 部署配置
3. [安全指南](SECURITY.md) - 安全加固
4. [故障排查](TROUBLESHOOTING.md) - 运维问题

---

## 📋 快速参考

### 常用命令

```bash
# 安装依赖
cd backend && uv sync

# 生成加密密钥
uv run python scripts/generate_proxy_key.py

# 运行迁移
uv run python manage.py migrate proxy

# 启动Celery Beat
uv run celery -A config beat -l info

# 测试代理（Django Shell）
uv run python manage.py shell
>>> from apps.proxy.models import ProxyConfig
>>> ProxyConfig.objects.first().test_connection()
```

### 关键文件

| 文件 | 说明 |
|------|------|
| `apps/proxy/models.py` | 代理数据模型 |
| `apps/proxy/admin.py` | Django Admin配置 |
| `apps/proxy/views.py` | API视图 |
| `apps/proxy/tasks.py` | Celery健康检查任务 |
| `config/settings/base.py` | Celery Beat配置 |
| `.env` | 环境变量（密钥） |

### API端点

| 端点 | 权限 | 说明 |
|------|------|------|
| `/api/v1/proxy/config/` | Admin | 代理配置CRUD |
| `/api/v1/proxy/select/` | Authenticated | 代理选择器 |
| `/api/v1/proxy/{id}/test_connection/` | Authenticated | 测试连接 |
| `/api/v1/proxy/logs/` | Admin | 使用日志 |

---

## 🆘 获取帮助

### 问题排查流程

1. 查看相关文档
2. 检查日志文件
3. 使用诊断命令
4. 参考故障排查指南

### 日志位置

```bash
# 应用日志
logs/proxy.log

# Celery日志
/var/log/celery/beat.log
/var/log/celery/worker.log

# Nginx日志
/var/log/nginx/access.log
/var/log/nginx/error.log
```

---

## 📞 联系方式

- **技术支持**: 提交Issue到项目仓库
- **安全问题**: 私信项目管理员
- **功能建议**: 提交Feature Request

---

**文档版本:** 1.0.0
**最后更新:** 2026-01-31
**维护者:** Epic 9 Team
