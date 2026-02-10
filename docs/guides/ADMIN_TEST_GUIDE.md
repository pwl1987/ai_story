# Django Admin 测试指南

## 🌐 访问地址

### Admin 后台
- **URL**: http://localhost:8000/admin/
- **状态**: ✅ 运行中

### API 基础地址
- **URL**: http://localhost:8000/api/v1/
- **状态**: ✅ 运行中

---

## 👤 测试管理员账号

### 方案 1: 测试管理员账号（推荐）
```
用户名: testadmin
密码: admin123
权限: 超级管理员（Superuser）
```

### 方案 2: 原有管理员账号
```
用户名: admin
密码: (未知，需要重置)
权限: 超级管理员
```

### 方案 3: 普通管理员
```
用户名: staff
密码: (未知，需要重置)
权限: 普通管理员（非Superuser）
```

---

## 📝 测试步骤

### 1. 访问 Admin 后台

#### 方法 1: 浏览器访问（推荐）
1. 打开浏览器
2. 访问: http://localhost:8000/admin/
3. 输入用户名: `testadmin`
4. 输入密码: `admin123`
5. 点击"登录"

#### 方法 2: 命令行测试
```bash
# 测试登录 API
curl -X POST http://localhost:8000/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testadmin", "password": "admin123"}'
```

### 2. 验证 Epic 8 功能

#### ✅ Story 8.1-8.2: 用户权限区分和用户管理
**导航**: Admin 首页 → 用户

**测试步骤**:
1. 点击"用户"
2. 查看用户列表（应显示所有用户）
3. 点击"添加用户"
4. 填写用户信息:
   - 用户名: `testuser01`
   - 邮箱: `testuser01@example.com`
   - 密码: `password123`
   - 员工状态: ✅ (勾选)
   - 超级管理员: ⬜ (不勾选)
5. 点击"保存"

**预期结果**:
- ✅ 新用户创建成功
- ✅ 列表显示新用户
- ✅ 用户状态显示正确

#### ✅ Story 8.3: 密码重置功能
**导航**: 用户列表 → 勾选用户 → 操作 → "重置密码并强制下次修改"

**测试步骤**:
1. 在用户列表中勾选 `testuser01`
2. 选择操作: "重置密码并强制下次修改"
3. 点击"执行"
4. **复制临时密码**（只显示一次！）

**预期结果**:
- ✅ 显示12位临时密码
- ✅ 用户的 `must_change_password` 标志设置为 `True`
- ✅ 审计日志记录操作

#### ✅ Story 8.4: 强制修改密码（前端）
**测试步骤**:
1. 退出登录
2. 使用 `testuser01` 和临时密码登录
3. **应该自动跳转到修改密码页面**: http://localhost:8000/change-password/

**预期结果**:
- ✅ 显示警告: "需要修改密码"
- ✅ 不显示"原密码"输入框（强制模式）
- ✅ 输入新密码后可以正常登录

#### ✅ Story 8.5-8.6: 全局资源配置
**导航**: Admin 首页 → 模型提供商 / 提示词集

**测试步骤**:
1. 点击"模型提供商"
2. 查看列表中的视觉标记:
   - 🌟 系统级（金色）
   - 👤 用户级（灰色）
3. 点击"添加模型提供商"
4. 填写信息:
   - 名称: `测试模型`
   - 提供商类型: `LLM`
   - **勾选 "系统级默认资源"**
5. 保存

**预期结果**:
- ✅ 系统级模型显示金色星标 🌟
- ✅ 普通用户可以看到系统级模型
- ✅ 只有创建者可以编辑系统级模型

#### ✅ Story 8.8: 资源所有权机制
**测试步骤**:
1. 创建一个系统级模型（用 `testadmin` 创建）
2. 退出登录
3. 用 `staff` 账号登录
4. 尝试编辑 `testadmin` 创建的系统级模型

**预期结果**:
- ✅ 可以看到模型（因为 is_staff=True）
- ❌ **不能编辑**（不是创建者）
- ❌ **不能删除**（不是创建者）
- ✅ Superuser 可以编辑任何资源

#### ✅ Story 8.9: 用户删除级联删除
**测试步骤**:
1. 创建一个测试用户
2. 为该用户创建一些项目
3. 删除该用户

**预期结果**:
- ✅ 用户的所有项目被级联删除
- ✅ 系统级资源转移到其他超级管理员
- ✅ 用户级资源被删除
- ❌ 不能删除最后一个超级用户

#### ✅ Story 8.10: 操作日志（审计日志）
**导航**: Admin 首页 → 审计日志

**测试步骤**:
1. 点击"审计日志"
2. 查看操作记录
3. 使用过滤器:
   - 按操作类型过滤（创建/更新/删除）
   - 按用户过滤
   - 按时间过滤

**预期结果**:
- ✅ 所有 Admin 操作自动记录
- ✅ 显示操作用户、时间、对象
- ✅ 审计日志是**只读**的（不能手动添加/修改/删除）

#### ✅ Story 8.11: 系统资源视觉标记
**验证**:
- ✅ 系统级模型显示 🌟 (金色 #D4AF37)
- ✅ 用户级模型显示 👤 (灰色 #808080)
- ✅ PromptTemplateSet 和 ModelProvider 使用相同样式

#### ✅ Story 8.12: Admin 操作手册
**文档位置**: `/home/code/ai_story/backend/docs/ADMIN_GUIDE.md`

查看文档:
```bash
cat /home/code/ai_story/backend/docs/ADMIN_GUIDE.md | head -100
```

---

## 🧪 快速测试命令

### 测试 1: 创建测试用户
```bash
curl -X POST http://localhost:8000/api/v1/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "quicktest",
    "email": "quicktest@example.com",
    "password": "Test123456",
    "password_confirm": "Test123456"
  }'
```

### 测试 2: 登录获取 Token
```bash
curl -X POST http://localhost:8000/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testadmin",
    "password": "admin123"
  }'
```

### 测试 3: 查看模型列表（需要 Token）
```bash
# 先登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testadmin", "password": "admin123"}' \
  | jq -r '.data.tokens.access')

# 查看模型列表
curl -X GET http://localhost:8000/api/v1/models/providers/ \
  -H "Authorization: Bearer $TOKEN"
```

### 测试 4: 查看审计日志
```bash
uv run python manage.py shell << 'EOF'
from apps.users.models import AuditLog
logs = AuditLog.objects.all()[:5]
for log in logs:
    print(f"{log.created_at} - {log.user.username} - {log.action} - {log.model_name}")
EOF
```

---

## 🐛 常见问题

### Q1: 登录失败 "用户名或密码错误"
**A**:
- 确认用户名是 `testadmin`
- 确认密码是 `admin123`
- 确认用户 `is_active=True`

### Q2: 访问 /admin/ 返回 403 Forbidden
**A**:
- 确认用户 `is_staff=True`
- 检查是否登录
- 尝试访问 http://localhost:8000/admin/login/

### Q3: 修改密码后无法登录
**A**:
- 修改密码后会自动登出
- 使用新密码重新登录
- 如果是强制修改，需要先登录 → 修改密码 → 自动登出 → 重新登录

### Q4: 看不到系统级资源
**A**:
- 确认资源的 `is_system_default=True`
- 普通用户可以看到系统级资源
- 检查 `created_by` 字段是否正确设置

### Q5: 审计日志为空
**A**:
- 审计日志只记录 Admin 操作
- 需要通过 Admin 进行一些操作（创建/更新/删除）
- 通过 API 操作不会记录到审计日志

---

## 📱 前端访问（如果前端已启动）

### 前端地址
- **URL**: http://localhost:3000 (如果启动)

### 测试流程
1. 访问前端应用
2. 登录 (testadmin / admin123)
3. 查看模型列表
4. 查看提示词集
5. 验证系统级资源显示

---

## ✅ 验收检查清单

- [ ] 可以访问 Admin 后台
- [ ] 使用 testadmin/admin123 登录成功
- [ ] 可以查看用户列表
- [ ] 可以创建新用户
- [ ] 可以重置用户密码
- [ ] 强制修改密码流程正常
- [ ] 系统级资源显示 🌟 标记
- [ ] 用户级资源显示 👤 标记
- [ ] 普通管理员不能编辑其他人的系统资源
- [ ] 删除用户时级联删除其项目
- [ ] 审计日志自动记录操作
- [ ] 审计日志只读（不能手动修改）
- [ ] API 数据隔离正常（普通用户只看自己的+系统级）

---

## 🎯 下一步

测试完成后，您可以：
1. **报告问题**: 如果发现任何 bug
2. **继续开发**: 开始下一个 Epic
3. **部署**: 合并到 main 分支并部署

---

**祝测试愉快！** 🚀
