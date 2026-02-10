# Django Admin 代理配置访问指南

> **更新时间**: 2026-01-31
> **状态**: ✅ 已配置完成

---

## 📱 访问步骤

### 1. 登录 Django Admin

**URL**: http://10.30.5.62:8000/admin/

**登录凭据**:
- 用户名: `simple_admin`
- 密码: `admin123`

---

### 2. 找到代理管理模块

登录成功后，在 Admin 首页的应用列表中查找：

**应用名称**: `Proxy Management`（代理管理）

**包含的模型**:
- **Proxy configs** - 代理配置（添加、编辑、删除代理）
- **Proxy usage logs** - 代理使用日志（只读）

---

### 3. 管理代理配置

点击 **Proxy configs** 进入代理配置列表：

**当前测试数据**:
- `测试代理-HTTP` - http://127.0.0.1:8080
- `测试代理-SOCKS5` - socks5://127.0.0.1:1080

**操作按钮**:
- ➕ **添加代理配置** - 创建新的代理
- ✏️ **编辑** - 修改现有代理配置
- 🗑️ **删除** - 删除不需要的代理
- 🔧 **测试连接** - 批量测试选中的代理

---

### 4. 创建新代理配置

点击 **添加代理配置**，填写以下信息：

#### **基本信息**（必填）
- **名称** (name): 代理的唯一标识（如：OpenAI美国代理-01）
- **协议** (protocol): HTTP / HTTPS / SOCKS5
- **主机** (host): 代理服务器地址
- **端口** (port): 代理服务器端口

#### **认证信息**（可选）
- **用户名** (username): 代理认证用户名
- **密码** (password): 代理认证密码（保存后自动加密）

#### **状态配置**
- **启用** (is_active): 是否激活该代理
- **健康** (is_healthy): 自动更新的健康状态
- **优先级** (priority): 数值越小优先级越高（默认 10）

#### **只读信息**
- **加密密码**: 显示为 •••••••••
- **代理 URL**: 完整的代理 URL（可用于复制）
- **最后使用时间**: 最近一次使用该代理的时间
- **创建/更新时间**: 时间戳

---

### 5. 测试代理连接

在代理配置列表页：
1. 勾选要测试的代理（可多选）
2. 选择操作 **测试连接**
3. 点击 **执行**

**测试流程**:
- ✅ 访问 https://httpbin.org/ip
- ✅ 显示代理 IP 和响应时间
- ✅ 自动更新健康状态
- ✅ 记录到使用日志

---

### 6. 查看使用日志

点击 **Proxy usage logs** 查看代理使用记录：

**显示信息**:
- 代理名称
- AI 提供商（如 OpenAI, Claude）
- 请求端点
- 响应时间
- 成功/失败状态
- 时间戳

**功能**:
- 📊 按代理、提供商、状态筛选
- 🔍 按端点、错误信息搜索
- 📤 导出为 CSV（批量操作）

---

## 🔧 快速创建真实代理

### 示例：创建 HTTP 代理

1. 点击 **Proxy configs** → **添加代理配置**
2. 填写信息：
   ```
   名称: 我的HTTP代理
   协议: HTTP
   主机: proxy.example.com
   端口: 8080
   用户名: user123
   密码: pass123
   启用: ✓
   优先级: 10
   ```
3. 点击 **保存**

### 示例：创建 SOCKS5 代理

```
名称: Shadowsocks代理
协议: SOCKS5
主机: 127.0.0.1
端口: 1080
启用: ✓
优先级: 5
```

---

## 📊 管理界面截图说明

### Admin 首页
```
Django administration
├── Projects
├── Prompts
├── Models
├── Content
├── Users
├── Proxy Management  ← 找这里！
│   ├── Proxy configs
│   └── Proxy usage logs
└── ...
```

### 代理配置列表
```
Proxy configs
选择: _______________  [测试连接 ▼]
─────────────────────────────────────────
名称        │ 协议   │ 地址        │ 状态 │ 健康 │ 优先级
─────────────────────────────────────────
测试代理-HTTP│ HTTP   │127.0.0.1:8080│ ✓   │ ✓   │ 10
测试代理-SOCKS│SOCKS5 │127.0.0.1:1080│ ✗   │ ✓   │ 20
─────────────────────────────────────────
[1] 2 项 │ 2 / 2 已选择
```

---

## ❓ 常见问题

### Q1: Admin 首页看不到 "Proxy Management"？

**解决方案**:
1. **强制刷新浏览器** (Ctrl+F5)
2. **确认用户权限** - 使用超级用户或 staff 账户
3. **重启 Django 服务器**
   ```bash
   # 停止当前服务
   kill $(cat /tmp/admin.pid)

   # 重新启动
   cd /home/code/ai_story
   ./start_all.sh
   ```

### Q2: 点击 "Proxy configs" 显示"无数据"？

**原因**: 数据库中没有代理配置记录

**解决**: 已自动创建 2 个测试配置，或手动创建新配置

### Q3: 如何批量导入代理配置？

**方案 1**: 使用 Django Shell
```python
from apps.proxy.models import ProxyConfig

ProxyConfig.objects.create(
    name="代理1",
    protocol="http",
    host="proxy1.example.com",
    port=8080,
    username="user",
    password="pass",  # 自动加密
    is_active=True,
    priority=10
)
```

**方案 2**: 使用 API（需要认证）
```bash
POST /api/v1/proxy/configs/
```

### Q4: 密码安全吗？

**安全措施**:
- ✅ 使用 Fernet 对称加密存储
- ✅ Admin 中显示为 •••••••••
- ✅ 日志中不记录明文密码
- ✅ 支持 `get_proxy_url()` 解密用于实际请求

---

## 🔗 相关文档

- [Epic 9 完整规范](../../_bmad-output/implementation-artifacts/EPIC-9-STORY-SPEC.md)
- [代理管理 API 文档](../../docs/proxy/README.md)
- [代理配置模型](../../backend/apps/proxy/models.py)
- [Admin 代码](../../backend/apps/proxy/admin.py)

---

**文档版本**: v1.0
**维护团队**: AI Story Development Team
