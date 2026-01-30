# Epic 8: 管理员后台系统 - 技术规格需求

**状态**: Ready for Development
**创建日期**: 2026-01-30
**最后更新**: 2026-01-30
**Party Mode**: ✅ 完成 - 6位专家协作完成需求分析

---

## 📊 需求概览

**目标**: 在现有Django Admin基础上，增强管理员后台功能，实现用户管理、全局资源配置、数据隔离和系统管理功能。

**Epic级别**: Epic 8（新增）
**预估工作量**: 13个工作日
**测试覆盖率**: 85%

---

## 🎯 核心需求确认

### 1. 权限分级系统
**决策**: 使用Django内置`is_staff`字段区分2级权限
- 普通用户（`is_staff=False`）：只能访问自己的数据
- 管理员（`is_staff=True`）：可访问Admin后台，查看所有数据
- 保留`is_superuser`字段以备将来扩展

### 2. 管理员登录
**决策**: 共用API登录，Admin后台检查`is_staff`
- 管理员通过`/api/v1/users/login/`登录
- 访问`/admin/`时检查`request.user.is_staff`
- 非`is_staff`用户访问Admin返回403

### 3. 用户管理功能
- ✅ 查看所有用户列表（搜索、过滤）
- ✅ 创建新用户
- ✅ 编辑用户信息
- ✅ 删除用户（级联删除所有项目）
- ✅ 禁用/启用用户（`is_active`）

### 4. 密码重置功能
- **流程**: Admin生成12位临时随机密码 → 设置`must_change_password=True` → 显示给管理员
- **强制修改**: 用户下次登录时，检测`must_change_password=True`，强制修改密码后才能访问系统

### 5. 全局资源配置
- **系统级默认模型**: 所有用户可见，但不可完全编辑（除创建者）
- **系统级默认提示词集**: 所有用户可见，但不可完全编辑（除创建者）
- **资源优先级**: 系统级资源 > 用户级资源
- **立即生效**: 用户级资源升级为系统级后，所有用户立即可见

### 6. 资源所有权机制
- **创建者确认**: 编辑或删除系统级资源时，需要资源创建者确认（即使都是管理员）
- **保护创建者**: `created_by`字段设置`on_delete=models.PROTECT`
- **权限检查**: Admin层面检查`obj.can_edit(request.user)`

### 7. 用户删除策略
**决策**: 级联删除所有项目
- 使用Django的`on_delete=models.CASCADE`
- 删除前显示警告，列出将被删除的项目

### 8. Admin界面优化
**决策**: 优化现有Django Admin，不重新开发
- ✅ 系统级资源用金色标记（🌟）
- ✅ 添加Admin统计信息显示
- ✅ 自定义actions（批量操作）
- ✅ 优化list_display和list_filter

---

## 📋 Story分解

### Story 8.1: 用户权限区分
**描述**: 实现基于`is_staff`的权限分级

**工作量**: 1天

**验收标准**:
- ✅ User模型使用`is_staff`区分管理员
- ✅ Admin后台只允许`is_staff=True`用户访问
- ✅ API层面数据隔离验证（已实现）

**技术实现**:
```python
# StaffAdminSite权限检查
class StaffAdminSite(AdminSite):
    def has_permission(self, request):
        return request.user.is_authenticated and request.user.is_staff
```

---

### Story 8.2: 用户管理Admin
**描述**: 创建UserAdmin配置，实现用户CRUD

**工作量**: 1.5天

**验收标准**:
- ✅ 管理员可查看所有用户列表
- ✅ 管理员可创建新用户
- ✅ 管理员可编辑用户信息
- ✅ 管理员可禁用/启用用户（`is_active`）
- ✅ 优化的列表显示（用户名、邮箱、权限、状态、加入时间）
- ✅ 搜索和过滤功能

**技术实现**:
- 创建`apps/users/admin.py`
- 自定义`list_display`, `list_filter`, `search_fields`
- 添加自定义actions（批量禁用/启用）
- 添加Admin统计信息

---

### Story 8.3: 密码重置功能
**描述**: 实现管理员重置用户密码功能

**工作量**: 1.5天

**验收标准**:
- ✅ Admin action：重置密码
- ✅ 生成12位临时随机密码
- ✅ 设置`must_change_password=True`
- ✅ 显示临时密码给管理员（安全考虑，只显示一次）
- ✅ 记录密码重置操作日志

**技术实现**:
```python
def reset_password_action(self, request, queryset):
    for user in queryset:
        temp_password = get_random_string(length=12)
        user.password = make_password(temp_password)
        user.must_change_password = True
        user.save()
        # 记录日志
    self.message_user(request, f"成功为 {queryset.count()} 个用户重置密码")
```

---

### Story 8.4: 强制修改密码
**描述**: 用户首次登录时强制修改密码

**工作量**: 1天

**验收标准**:
- ✅ 检查`must_change_password`字段
- ✅ 如果为True，跳过其他API，要求修改密码
- ✅ 修改成功后，标记为`False`
- ✅ 修改后才能访问系统其他功能
- ✅ JWT token不包含修改密码功能

**技术实现**:
- 自定义Django Auth后端或中间件
- 在认证流程中检查`must_change_password`
- 前端检测特殊状态码，显示密码修改页面

---

### Story 8.5: 全局资源配置 - 模型
**描述**: ModelProvider添加系统级默认功能

**工作量**: 1.5天

**验收标准**:
- ✅ 添加`is_system_default`字段
- ✅ 添加`created_by`外键（PROTECT保护）
- ✅ 管理员可创建系统级默认模型
- ✅ 普通用户可见但不可编辑系统资源
- ✅ API返回时系统级资源优先
- ✅ Admin标记系统级资源（金色🌟）

**技术实现**:
```python
class ModelProvider(models.Model):
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='created_models'
    )
    is_system_default = models.BooleanField(
        default=False,
        help_text="系统级默认资源：所有用户可见且不可编辑（除创建者）"
    )

    def can_edit(self, user):
        if self.is_system_default:
            return self.created_by == user
        return self.created_by == user
```

---

### Story 8.6: 全局资源配置 - 提示词
**描述**: PromptTemplateSet添加系统级默认功能

**工作量**: 1.5天

**验收标准**:
- ✅ 添加`is_system_default`字段
- ✅ 添加`created_by`外键（PROTECT保护）
- ✅ 管理员可创建系统级默认提示词集
- ✅ 普通用户可见但不可编辑系统资源
- ✅ API返回时系统级资源优先
- ✅ Admin标记系统级资源（金色🌟）

**技术实现**:
- 与Story 8.5类似，在PromptTemplateSet模型中添加相同字段

---

### Story 8.7: 数据隔离验证测试
**描述**: 确保数据隔离正确实施

**工作量**: 2天

**验收标准**:
- ✅ 单元测试：API层面的数据过滤
- ✅ 集成测试：管理员看全部数据
- ✅ 安全测试：普通用户不能访问其他用户数据
- ✅ 测试覆盖率>85%

**测试套件**:
- 权限测试套件（10个测试）
- 用户管理测试套件（8个测试）
- 全局资源测试套件（10个测试）
- 密码流程测试套件（5个测试）

**总计**: 约33个测试用例

---

### Story 8.8: 资源所有权实现
**描述**: 实现资源创建者确认机制

**工作量**: 1天

**验收标准**:
- ✅ 编辑系统级资源需创建者确认
- ✅ 删除系统级资源需创建者确认
- ✅ 超级管理员可以绕过此限制
- ✅ Admin层面权限检查

**技术实现**:
```python
class ModelProviderAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        return obj.can_edit(request.user) or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        return (obj.created_by == request.user
                or request.user.is_superuser)
```

---

### Story 8.9: 用户删除级联删除
**描述**: 实现用户删除时的级联删除功能

**工作量**: 1天

**验收标准**:
- ✅ 用户删除时，所有项目被级联删除
- ✅ 删除前显示警告，列出将被删除的项目
- ✅ 删除操作记录到审计日志（可选）

**技术实现**:
- Project模型的`user`外键已设置为`CASCADE`
- Admin自定义action添加确认页面

---

### Story 8.10: AdminSite权限控制
**描述**: 实现管理员专用AdminSite

**工作量**: 1天

**验收标准**:
- ✅ 创建`StaffAdminSite`
- ✅ 注册所有模型到`StaffAdminSite`
- ✅ 替换默认`admin.site`
- ✅ 非`is_staff`用户访问返回403

**技术实现**:
```python
# backend/config/admin.py
staff_admin_site = StaffAdminSite(name='staffadmin')
staff_admin_site.register(Project, ProjectAdmin)
# ... 注册所有模型
```

---

### Story 8.11: 系统资源视觉标记
**描述**: Admin界面系统级资源视觉优化

**工作量**: 0.5天

**验收标准**:
- ✅ 系统级资源用金色标记（🌟）
- ✅ 用户级资源用灰色标记
- ✅ Admin列表页面视觉区分明显

**技术实现**:
- `list_display`添加`system_resource_badge`方法
- 使用Django的`format_html`显示彩色标记

---

### Story 8.12: Admin操作手册
**描述**: 创建管理员操作手册

**工作量**: 1天

**验收标准**:
- ✅ 创建`docs/ADMIN_GUIDE.md`
- ✅ 包含用户管理章节
- ✅ 包含全局资源配置章节
- ✅ 包含数据隔离说明
- ✅ 包含常见问题FAQ

---

## 🔧 技术实现要点

### 数据模型扩展（3个新增字段）
```python
# User扩展
must_change_password = BooleanField(default=False)

# ModelProvider扩展
is_system_default = BooleanField(default=False)
created_by = ForeignKey('users.User', on_delete=PROTECT)

# PromptTemplateSet扩展
is_system_default = BooleanField(default=False)
created_by = ForeignKey('users.User', on_delete=PROTECT)
```

### 权限检查逻辑
```python
# API层面
def get_queryset(self):
    if self.request.user.is_staff:
        return Model.objects.all()
    return Model.objects.filter(user=self.request.user)

# Admin层面
def has_permission(self, request):
    return request.user.is_staff
```

### 资源优先级逻辑
```python
def get_available_models_for_user(user):
    system_models = ModelProvider.objects.filter(is_system_default=True)
    user_models = ModelProvider.objects.filter(
        created_by=user,
        is_system_default=False
    )
    return system_models | user_models

# 使用时：系统级优先
selected = user_models.first() or system_models.first()
```

---

## 🧪 测试策略

### 测试覆盖率目标: **85%**

### 关键测试场景
1. **数据隔离测试** - 确保普通用户只能看到自己的数据
2. **管理员权限测试** - 确保管理员能看到所有数据
3. **资源所有权测试** - 确保创建者确认机制有效
4. **密码重置流程测试** - 确保临时密码和强制修改功能
5. **AdminSite访问控制测试** - 确保非管理员无法访问

### 测试文件结构
```
tests/
├── test_admin_permissions.py
├── test_data_isolation.py
├── test_user_management.py
├── test_password_reset.py
├── test_global_resources.py
└── test_resource_ownership.py
```

---

## 📁 需要创建/修改的文件

### 新建文件
```
backend/apps/users/admin.py
backend/docs/ADMIN_GUIDE.md
backend/apps/users/migrations/0001_add_must_change_password.py
backend/apps/models/migrations/0002_add_system_default_fields.py
backend/apps/prompts/migrations/0001_add_system_default_fields.py
```

### 修改文件
```
backend/config/urls.py  # 添加StaffAdminSite
backend/apps/users/views.py  # 添加用户管理API
backend/apps/users/serializers.py  # 添加用户序列化器
backend/apps/models/admin.py  # 优化Admin显示
backend/apps/prompts/admin.py  # 优化Admin显示
```

---

## 🚀 下一步行动

1. ✅ 需求分析完成
2. ⏭️ **生成完整技术规格文档** (推荐)
3. ⏭️ 开始Story 8.1实施
4. ⏭️ 启动开发工作流

---

## 💡 专家建议总结

- **Winston (Architect)**: "简单胜于复杂。保持架构简洁，基于Django Admin优化是务实选择。"
- **John (PM)**: "需求完整度已达到95%，快速进入实施才是王道！"
- **Amelia (Dev)**: "技术方案扎实，我会提供完整的代码示例和迁移脚本。"
- **Murat (TEA)**: "33个测试用例覆盖核心场景，风险可控。"
- **Sally (UX)**: "最小化UI优化就能达到很好的效果。"

---

**Party Mode Session Complete!** 🎉

感谢您使用BMAD Party Mode进行多Agent协作讨论！

**Agent团队学习了很多** - 这就是多Agent协作的价值！

---

*需求文档已保存，准备进入下一阶段！*

**您可以选择：**
- 运行`create-story`将此需求转为正式Story
- 运行`quick-spec`生成完整技术规格
- 或者其他工作流

