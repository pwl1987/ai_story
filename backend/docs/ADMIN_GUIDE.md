# Django Admin 操作指南

> **Epic 8 Story 8.12: Admin操作手册**
>
> 最后更新: 2026-01-30
>
> 本文档面向系统管理员，介绍如何使用 Django Admin 后台管理 AI Story 系统。

---

## 目录

1. [快速开始](#快速开始)
2. [用户管理](#用户管理)
3. [全局资源配置](#全局资源配置)
4. [数据隔离说明](#数据隔离说明)
5. [审计日志](#审计日志)
6. [常见问题FAQ](#常见问题faq)

---

## 快速开始

### 访问 Admin 后台

**URL**: `http://your-domain/admin`

**登录要求**:
- 必须是 `is_staff=True` 的用户
- 非管理员用户访问会返回 403 Forbidden

**登录步骤**:
1. 使用管理员账号登录
2. 登录成功后自动跳转到 Admin 首页
3. 首页显示所有可管理的模型和统计信息

### Admin 首页概览

Admin 首页包含以下模块:

| 模块 | 描述 | 权限要求 |
|------|------|----------|
| **用户管理** | 用户账号、用户资料 | `is_staff` |
| **项目管理** | 项目、分镜、场景、镜头 | `is_staff` |
| **内容管理** | 文案、图像、视频 | `is_staff` |
| **提示词管理** | 提示词集、模板、全局变量 | `is_staff` |
| **模型管理** | AI模型提供商、使用日志 | `is_staff` |
| **审计日志** | 系统操作记录 | `is_staff` (只读) |

---

## 用户管理

### 1. 查看用户列表

**路径**: `/admin/users/`

**列表显示字段**:
- 用户名
- 邮箱
- 员工状态 (`is_staff`)
- 超级管理员 (`is_superuser`)
- 活跃状态 (`is_active`)
- 强制修改密码 (`must_change_password`)
- 加入时间 (`date_joined`)

**搜索功能**:
- 按用户名搜索
- 按邮箱搜索

**过滤选项**:
- 员工状态 (`is_staff`)
- 超级管理员 (`is_superuser`)
- 活跃状态 (`is_active`)

### 2. 创建新用户

**步骤**:
1. 点击"用户" → "Add user"
2. 填写必填信息:
   - **用户名**: 唯一标识
   - **邮箱**: 必须唯一
   - **密码**: 使用"生成密码"按钮创建安全密码
3. 设置权限:
   - **员工状态 (`is_staff`)**: 勾选后可访问 Admin 后台
   - **超级管理员 (`is_superuser`)**: 拥有所有权限
   - **活跃状态 (`is_active`)**: 取消勾选可禁用用户
4. 点击"保存"

**注意事项**:
- 创建用户时会自动记录 `created_by` 字段
- 建议使用强密码（至少12位，包含大小写字母、数字、特殊字符）

### 3. 编辑用户信息

**步骤**:
1. 在用户列表中点击要编辑的用户
2. 修改需要更新的字段
3. 点击"保存"

**可编辑字段**:
- 邮箱
- 员工状态
- 超级管理员
- 活跃状态
- 强制修改密码
- 用户资料 (`UserProfile`)

### 4. 重置用户密码

**方法一：通过 Admin Action**

**步骤**:
1. 在用户列表中勾选需要重置密码的用户
2. 选择操作"重置密码并强制下次修改"
3. 点击"执行"
4. 系统会生成12位临时随机密码，**请立即复制保存**
5. 临时密码**只显示一次**，请妥善保管

**注意事项**:
- 重置后用户下次登录时**必须修改密码**
- 临时密码格式: 12位随机字符串（大小写字母+数字）
- 重置操作会记录到审计日志

**方法二：编辑用户**

在用户编辑页面，点击"生成新密码"按钮，然后保存。

### 5. 禁用/启用用户

**禁用用户**:
1. 编辑用户
2. 取消勾选 `is_active`
3. 保存

**效果**:
- 用户无法登录系统
- 用户的所有数据仍然保留
- 可随时重新启用

**批量禁用**:
1. 在用户列表中勾选多个用户
2. 选择操作"批量禁用"
3. 点击"执行"

### 6. 删除用户

**重要警告** ⚠️

删除用户会触发**级联删除**，以下数据将被永久删除:
- 用户创建的所有项目
- 用户创建的分镜、场景、镜头
- 用户创建的文案、图像、视频
- 用户创建的提示词集
- 用户创建的模型配置

**系统级资源处理**:
- 用户创建的系统级模型 (`is_system_default=True`) → 所有权转移到其他超级管理员
- 用户创建的系统级提示词集 → 所有权转移到其他超级管理员
- 用户级资源 → **直接删除**

**限制**:
- 不能删除最后一个超级用户
- 删除前系统会显示警告信息

**删除步骤**:
1. 编辑用户
2. 滚动到页面底部
3. 点击"删除"
4. 确认删除操作

---

## 全局资源配置

### 系统级资源 vs 用户级资源

**核心概念**:
- **系统级资源** (`is_system_default=True`): 所有用户可见，但只有创建者可编辑
- **用户级资源** (`is_system_default=False`): 仅创建者可见

**视觉标记**:
- 🌟 系统级 - 金色星标
- 👤 用户级 - 灰色用户图标

### 模型管理 (ModelProvider)

**路径**: `/admin/models/modelprovider/`

**列表显示字段**:
- 资源类型 (系统级 🌟 / 用户级 👤)
- 名称
- 提供商类型 (`provider_type`)
- 执行器类 (`executor_class`)
- 活跃状态 (`is_active`)
- 优先级 (`priority`)
- 创建时间

**创建系统级模型**:
1. 点击"Add model provider"
2. 填写基本信息:
   - **名称**: 例如 "OpenAI GPT-4"
   - **提供商类型**: LLM / Text2Image / Image2Video
   - **执行器类**: 选择对应的执行器
3. **勾选 "系统级默认资源" (`is_system_default`)**
4. 保存

**效果**:
- 所有用户都能看到此模型
- 所有用户都能使用此模型
- 只有创建者可以编辑/删除

**权限规则**:
- **创建者**: 可以编辑和删除
- **其他管理员**: 只能查看，不能编辑或删除
- **超级管理员**: 可以编辑和删除任何资源

### 提示词集管理 (PromptTemplateSet)

**路径**: `/admin/prompts/prompttemplateset/`

**列表显示字段**:
- 资源类型 (系统级 🌟 / 用户级 👤)
- 名称
- 活跃状态 (`is_active`)
- 是否默认 (`is_default`)
- 创建者
- 创建时间

**创建系统级提示词集**:
1. 点击"Add prompt template set"
2. 填写基本信息:
   - **名称**: 例如 "科幻风格提示词集"
   - **描述**: 详细说明用途
3. **勾选 "系统级默认资源" (`is_system_default`)**
4. 保存

**效果**:
- 所有用户都能看到此提示词集
- 所有用户都能使用此提示词集
- 只有创建者可以编辑/删除

### 资源所有权机制

**设计原则**:
- 使用 `created_by` 字段记录资源创建者
- `created_by` 设置为 `PROTECT` 约束（不能删除创建了资源的用户）

**编辑权限检查**:
```python
def can_edit(user):
    if is_system_default:
        return created_by == user or user.is_superuser
    return created_by == user
```

**删除权限检查**:
```python
def can_delete(user):
    return created_by == user or user.is_superuser
```

---

## 数据隔离说明

### 权限分级系统

**两级权限**:
1. **普通用户** (`is_staff=False`): 只能访问自己的数据
2. **管理员** (`is_staff=True`): 可以访问所有数据

**超级管理员** (`is_superuser=True`):
- 拥有所有权限
- 可以绕过所有权限制
- 可以编辑/删除任何系统级资源

### API 层面数据隔离

**普通用户**:
- 只能看到自己创建的项目
- 只能看到自己创建的内容
- 只能看到用户级的模型和提示词集
- 可以看到系统级的模型和提示词集（但只读）

**管理员**:
- 可以看到所有用户的项目
- 可以看到所有用户的内容
- 可以看到所有模型和提示词集

### Admin 层面数据隔离

**访问控制**:
- 非 `is_staff` 用户访问 Admin 返回 403 Forbidden
- `StaffAdminSite` 自动检查用户权限

**数据展示**:
- 管理员在 Admin 中可以看到所有数据
- 列表页显示 `created_by` 字段，便于识别创建者

### 安全测试建议

**验证数据隔离**:
1. 使用普通用户登录
2. 访问 API 端点，确认只能看到自己的数据
3. 尝试访问其他用户的数据，应该返回 403 或 404

**验证管理员权限**:
1. 使用管理员登录
2. 访问 Admin 后台
3. 确认可以看到所有用户的数据

---

## 审计日志

### 查看审计日志

**路径**: `/admin/users/auditlog/`

**审计日志记录以下操作**:
- ✅ 创建 (Create)
- ✅ 更新 (Update)
- ✅ 删除 (Delete)

**列表显示字段**:
- 创建时间
- 操作用户
- 操作类型
- 模型名称
- 对象表示
- 变更消息

**搜索和过滤**:
- 按操作类型过滤
- 按模型名称过滤
- 按时间范围过滤
- 按操作用户过滤

### 审计日志特性

**只读模式**:
- 审计日志**不能手动添加**
- 审计日志**不能修改**
- 审计日志**不能删除**

**自动记录**:
- 所有 Admin 操作自动记录
- 使用 `AuditLogMixin` 的 Admin 类自动记录日志
- 记录内容包括操作用户、操作类型、对象信息

**日志保留**:
- 审计日志永久保留
- 建议定期归档旧日志（如6个月前）

---

## 常见问题FAQ

### Q1: 忘记管理员密码怎么办？

**A**: 有以下方法恢复:

1. **使用 Django 管理命令**:
   ```bash
   cd backend
   uv run python manage.py changepassword <admin_username>
   ```

2. **通过数据库直接修改**（不推荐，仅在紧急情况下使用）:
   ```python
   from django.contrib.auth.models import User
   user = User.objects.get(username='admin')
   user.set_password('new_password')
   user.save()
   ```

3. **创建新的超级管理员**:
   ```bash
   uv run python manage.py createsuperuser
   ```

### Q2: 如何批量管理用户？

**A**: Admin 支持 Actions 功能:

1. 在用户列表中勾选多个用户
2. 选择要执行的操作:
   - 批量禁用
   - 批量启用
   - 重置密码并强制修改
3. 点击"执行"

### Q3: 系统级资源可以升级为用户级资源吗？

**A**: 可以，但不推荐。

**操作方法**:
1. 编辑资源
2. 取消勾选 `is_system_default`
3. 保存

**效果**:
- 资源变为仅创建者可见
- 其他用户将无法看到此资源

### Q4: 用户级资源可以升级为系统级资源吗？

**A**: 可以。

**操作方法**:
1. 编辑资源
2. 勾选 `is_system_default`
3. 保存

**效果**:
- 所有用户立即可见此资源
- 所有用户可以使用此资源
- 其他管理员可以查看，但不能编辑

### Q5: 如何查看用户创建了哪些资源？

**A**: 有以下方法:

1. **在 Admin 列表中查看**:
   - 所有模型都显示 `created_by` 字段
   - 使用过滤器按创建者筛选

2. **使用搜索功能**:
   - 在审计日志中搜索用户名
   - 查看该用户的所有操作记录

3. **数据库查询**（高级用户）:
   ```python
   from apps.models.models import ModelProvider
   from apps.prompts.models import PromptTemplateSet
   from apps.projects.models import Project

   user = User.objects.get(username='username')
   models = ModelProvider.objects.filter(created_by=user)
   prompts = PromptTemplateSet.objects.filter(created_by=user)
   projects = Project.objects.filter(user=user)
   ```

### Q6: 删除用户时的所有权转移逻辑是什么？

**A**: 系统按以下规则处理:

**系统级资源** (`is_system_default=True`):
- 所有权转移到**第一个可用的超级管理员**
- 如果没有其他超级管理员，则报错

**用户级资源** (`is_system_default=False`):
- **级联删除**，不转移所有权

**限制**:
- 不能删除最后一个超级用户

### Q7: 如何设置默认的模型和提示词集？

**A**: 使用 `is_default` 字段:

1. 编辑模型或提示词集
2. 勾选 `is_default`
3. 保存

**效果**:
- 系统会优先使用标记为默认的资源
- 建议每个类型只设置一个默认资源

### Q8: 审计日志占用空间太大怎么办？

**A**: 可以定期归档:

1. **导出旧日志**:
   ```python
   from apps.users.models import AuditLog
   import csv

   logs = AuditLog.objects.filter(created_at__lt='2025-07-01')
   # 导出到 CSV 或其他格式
   ```

2. **删除旧日志**（谨慎操作）:
   ```python
   logs.delete()
   ```

3. **设置自动归档任务**（使用 Celery Beat）:
   ```python
   # 定期归档6个月前的日志
   ```

### Q9: 用户登录后必须修改密码，但忘记密码怎么办？

**A**: 这种情况下无法自助解决，需要管理员介入:

1. 管理员在 Admin 中重置该用户密码
2. 生成新的临时密码
3. 告知用户临时密码
4. 用户使用临时密码登录后，再次被要求修改密码

### Q10: 如何备份 Admin 配置和数据？

**A**: 有以下方法:

1. **数据库备份**:
   ```bash
   # SQLite
   cp db.sqlite3 db.sqlite3.backup

   # PostgreSQL
   pg_dump -U username -d dbname > backup.sql
   ```

2. **导出 Admin 注册信息**:
   ```python
   from config import admin
   # 导出 staff_admin_site 的注册信息
   ```

3. **备份自定义代码**:
   - `apps/users/admin.py`
   - `apps/models/admin.py`
   - `apps/prompts/admin.py`
   - `core/admin_mixins.py`

---

## 附录

### 相关文档

- [Django Admin 官方文档](https://docs.djangoproject.com/en/3.2/ref/contrib/admin/)
- [Epic 8 技术规格](../_bmad-output/implementation-artifacts/epic-8-admin-backend-system.md)
- [项目 CLAUDE.md](../CLAUDE.md)

### 技术支持

如有问题，请:
1. 查阅本文档
2. 查看 Epic 8 技术规格文档
3. 查看相关测试文件 (`apps/users/tests/`)
4. 联系技术团队

### 更新记录

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-01-30 | 1.0 | 初始版本，覆盖 Stories 8.1-8.11 所有功能 |

---

**文档结束**

如有疑问或建议，请联系技术团队。
