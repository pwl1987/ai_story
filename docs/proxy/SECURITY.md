# 代理管理系统 - 安全指南

**版本:** 1.0.0
**最后更新:** 2026-01-31
**Epic:** Epic 9 - 代理管理系统

---

## 📋 概述

本文档详细说明代理管理系统的安全最佳实践和潜在风险。

---

## 🔐 密码加密安全

### Fernet 加密机制

代理密码使用 **Fernet 对称加密**（基于 AES-128-CBC）。

**加密流程:**
```python
# 1. 保存时自动加密
proxy.password = "my_password"
proxy.save()  # → password_encrypted (加密)
# → password = None (明文清空)

# 2. 使用时自动解密
proxy_url = proxy.get_proxy_url()  # 内部解密密码
```

**密钥要求:**
- 长度: 44 字节（URL安全的base64编码）
- 格式: `gAAAAAB<40字符>`
- 存储: `.env` 文件的 `PROXY_ENCRYPTION_KEY`

### 密钥生成

**生成强密钥（推荐）:**
```bash
cd backend
uv run python scripts/generate_proxy_key.py
```

**验证密钥:**
```bash
uv run python -c "from cryptography.fernet import Fernet; key = Fernet.generate_key(); print(len(key), key)"
```

预期输出: `44 b'gAAAAAB...'`

### 密钥管理最佳实践

| 环境 | 密钥策略 | 存储方式 |
|------|----------|----------|
| **开发环境** | 临时密钥 | `.env` 文件（不提交到Git） |
| **生产环境** | 强随机密钥 | 密钥管理服务（AWS KMS、HashiCorp Vault） |
| **测试环境** | 固定测试密钥 | 环境变量或CI/CD秘密变量 |

**⚠️ 禁止:**
- ❌ 将密钥硬编码到代码中
- ❌ 将密钥提交到版本控制系统
- ❌ 使用弱密钥（如全0、全1）
- ❌ 在日志中打印密钥

---

## 🔑 权限控制

### Django Admin 权限

**默认权限:** `IsAdminUser`

| 操作 | 超级用户 | 管理员 | 普通用户 |
|------|----------|--------|----------|
| 查看代理列表 | ✅ | ✅ | ❌ |
| 创建代理 | ✅ | ✅ | ❌ |
| 编辑代理 | ✅ | ✅ | ❌ |
| 删除代理 | ✅ | ✅ | ❌ |
| 测试连接 | ✅ | ✅ | ❌ |
| 查看使用日志 | ✅ | ✅ | ❌ |

**自定义权限:**

如需自定义权限，修改 `apps/proxy/admin.py`:

```python
class ProxyConfigAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # 限制创建权限
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # 限制删除权限
        return request.user.is_superuser
```

### API 权限

| 端点 | 匿名用户 | 普通用户 | 管理员 |
|------|----------|----------|--------|
| `GET /api/v1/proxy/config/` | ❌ | ❌ | ✅ |
| `POST /api/v1/proxy/config/` | ❌ | ❌ | ✅ |
| `PUT /api/v1/proxy/config/{id}/` | ❌ | ❌ | ✅ |
| `DELETE /api/v1/proxy/config/{id}/` | ❌ | ❌ | ✅ |
| `GET /api/v1/proxy/select/` | ❌ | ✅ | ✅ |
| `POST /api/v1/proxy/{id}/test_connection/` | ❌ | ✅ | ✅ |

**权限配置位置:** `apps/proxy/views.py`

```python
# 代理配置CRUD（仅管理员）
class ProxyConfigViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]

# 代理选择器（登录用户只读）
class ProxySelectViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

# 测试连接（登录用户）
class TestConnectionView(APIView):
    permission_classes = [IsAuthenticated]
```

---

## 🛡️ 网络安全

### 代理服务器验证

**推荐检查清单:**

1. **验证代理服务器身份**
   - 使用HTTPS协议
   - 验证SSL证书
   - 检查代理服务商信誉

2. **限制代理访问范围**
   - 仅用于AI API调用
   - 禁止访问内网资源
   - 配置白名单

3. **监控代理流量**
   - 记录所有代理调用
   - 监控异常流量
   - 设置流量告警

### API 安全

**HTTPS（生产环境必需）:**

```nginx
# Nginx 配置
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

**CORS 配置:**

```python
# config/settings/base.py
CORS_ALLOWED_ORIGINS = [
    "https://example.com",
    "https://www.example.com",
]

CORS_ALLOW_CREDENTIALS = True
```

---

## 🔍 日志安全

### 敏感信息过滤

**自动过滤的敏感字段:**

```python
# config/celery.py
SENSITIVE_FIELDS = {
    "password", "api_key", "apikey", "secret", "token",
    "authorization", "csrf_token", "access_token", "refresh_token"
}
```

**日志示例:**

```json
// 错误：日志中包含明文密码
{
  "proxy": "美国代理-01",
  "password": "my_password"  // ❌ 不要这样做
}

// 正确：密码已被过滤
{
  "proxy": "美国代理-01",
  "password": "***FILTERED***"  // ✅ 安全
}
```

### 日志访问控制

```bash
# 设置日志文件权限
sudo chmod 640 /var/log/celery/*.log
sudo chown celery:celery /var/log/celery/*.log

# 设置日志目录权限
sudo chmod 750 /var/log/celery
sudo chown celery:celery /var/log/celery
```

---

## ⚠️ 常见安全风险

### 风险1: 密钥泄露

**症状:** `.env` 文件被提交到Git

**预防:**
```bash
# 1. 添加到 .gitignore
echo ".env" >> .gitignore

# 2. 从Git历史中移除（如果已提交）
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" --prune-empty --tag-name-filter cat -- --all

# 3. 强制推送
git push origin --force --all
```

### 风险2: SQL注入

**Django ORM 自动防护:**

```python
# ✅ 安全（使用ORM）
ProxyConfig.objects.filter(name=user_input)

# ❌ 不安全（原始SQL）
query = f"SELECT * FROM proxy_proxyconfig WHERE name = '{user_input}'"
```

**如需使用原始SQL:**

```python
from django.db import connection

# ✅ 安全（参数化查询）
cursor = connection.cursor()
cursor.execute("SELECT * FROM proxy_proxyconfig WHERE name = %s", [user_input])
```

### 风险3: 代理劫持

**症状:** 攻击者通过恶意代理窃取AI API密钥

**预防:**
1. **验证代理服务器信誉**
   - 使用知名代理服务商
   - 检查服务商评价
   - 避免免费代理

2. **限制代理使用范围**
   - 仅用于AI API
   - 配置目标白名单

3. **监控异常行为**
   - 代理响应时间异常
   - 代理返回内容异常
   - API调用失败率突增

### 风险4: 未授权访问

**症状:** 非管理员访问代理配置API

**预防:**
1. **检查权限配置**
   ```python
   # apps/proxy/views.py
   class ProxyConfigViewSet(viewsets.ModelViewSet):
       permission_classes = [IsAdminUser]  # 确保正确配置
   ```

2. **测试权限**
   ```bash
   # 使用普通用户Token测试
   curl -X GET http://localhost:8000/api/v1/proxy/config/ \
     -H "Authorization: Bearer NORMAL_USER_TOKEN"

   # 预期: 403 Forbidden
   ```

---

## 🔒 数据安全

### 备份策略

**定期备份数据:**

```bash
# 1. 数据库备份（每天）
pg_dump -U ai_story_user ai_story_prod | gzip > backup_$(date +%Y%m%d).sql.gz

# 2. 代理配置备份（每周）
uv run python manage.py dumpdata proxy > proxy_backup_$(date +%Y%m%d).json

# 3. 加密备份
gpg --encrypt --recipient admin@example.com backup_*.sql.gz
```

### 数据清理

**清理旧日志:**

```python
# Django Shell
from apps.proxy.models import ProxyUsageLog
from datetime import timedelta
from django.utils import timezone

# 删除90天前的日志
cutoff_date = timezone.now() - timedelta(days=90)
ProxyUsageLog.objects.filter(timestamp__lt=cutoff_date).delete()
```

**自动化脚本:**

```bash
# 创建定时任务（crontab）
0 2 * * * cd /path/to/backend && uv run python manage.py shell -c "from apps.proxy.models import ProxyUsageLog; from datetime import timedelta; from django.utils import timezone; ProxyUsageLog.objects.filter(timestamp__lt=timezone.now()-timedelta(days=90)).delete()"
```

---

## 🚨 安全事件响应

### 事件1: 密钥泄露

**响应步骤:**

1. **立即更换密钥**
   ```bash
   uv run python scripts/generate_proxy_key.py
   ```

2. **重新加密所有代理密码**
   ```python
   from apps.proxy.models import ProxyConfig

   for proxy in ProxyConfig.objects.all():
       if proxy.password_encrypted:
           # 临时解密旧密码
           old_password = proxy.decrypt_password(proxy.password_encrypted)
           # 重新保存（使用新密钥加密）
           proxy.password = old_password
           proxy.save()
   ```

3. **检查日志中的异常访问**
   ```bash
   grep -i "proxy" /var/log/celery/*.log | grep -i "error"
   ```

### 事件2: 代理异常

**响应步骤:**

1. **禁用异常代理**
   - Django Admin → 代理详情页
   - 取消勾选 "Is active"

2. **分析使用日志**
   - 筛选该代理的失败日志
   - 检查错误信息模式

3. **联系代理服务商**
   - 报告异常
   - 请求调查

4. **切换到备用代理**
   - 更新项目代理配置
   - 验证正常工作

---

## 📋 安全检查清单

### 日常检查

- [ ] 检查 `.env` 文件权限（600）
- [ ] 检查日志文件权限（640）
- [ ] 查看Celery日志异常
- [ ] 验证所有代理健康状态
- [ ] 监控API调用失败率

### 每周检查

- [ ] 审查代理使用日志
- [ ] 检查未授权访问尝试
- [ ] 验证备份完整性
- [ ] 更新Django和安全补丁

### 每月检查

- [ ] 轮换代理密码（如需要）
- [ ] 审查管理员权限
- [ ] 清理旧日志数据
- [ ] 测试备份恢复流程

---

## 📚 相关资源

- [安装指南](INSTALLATION.md)
- [配置指南](CONFIGURATION.md)
- [故障排查](TROUBLESHOOTING.md)
- Django安全文档: https://docs.djangoproject.com/en/stable/topics/security/

---

**安全支持:** 发现安全漏洞，请立即报告给系统管理员
