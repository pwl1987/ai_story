# AI Story 项目人工检查清单

> **检查日期**: 2026-01-31
> **检查人**: 开发团队
> **目的**: 验证项目启动后所有功能正常运行

---

## 🎯 快速检查（5分钟）

### 1. 服务状态检查

```bash
# 检查所有服务进程
ps aux | grep -E "runserver|daphne|celery|webpack|redis" | grep -v grep

# 检查端口监听
lsof -i :8000 -i :8010 -i :3000 -i :6379 | grep LISTEN
```

**预期结果**：
- ✅ python3 runserver进程运行（端口8000 - Admin + 静态文件）
- ✅ daphne进程运行（端口8010 - WebSocket + API）
- ✅ celery worker进程运行（4个子进程）
- ✅ webpack进程运行（端口3000）
- ✅ redis容器运行（端口6379）

---

### 2. 健康检查端点

```bash
curl http://localhost:8010/api/v1/health/ | python3 -m json.tool
```

**预期结果**：
```json
{
    "status": "healthy",
    "checks": {
        "database": {"status": "healthy"},
        "redis_broker": {"status": "healthy"},
        "celery_workers": {"status": "healthy"}
    }
}
```

**注意**：健康检查端点运行在 8010 端口（ASGI服务器）

---

### 3. 访问前端应用

**打开浏览器访问**:
- 前端应用: http://localhost:3000/
- Admin后台: http://localhost:8000/admin/ (完整静态文件支持)
- 后端API文档: http://localhost:8010/api/schema/swagger-ui/

**预期结果**：
- ✅ 前端页面加载，显示登录界面
- ✅ Admin后台有完整样式（CSS/JS正常加载）
- ✅ API文档页面可访问

---

## 📋 详细功能检查（15分钟）

### 1. 用户登录功能

#### Step 1: 访问登录页面
1. 打开 http://localhost:3000/
2. 应该看到登录表单

#### Step 2: 使用Demo账户登录
- **用户名**: `demo_user`
- **密码**: `demo123456`

#### Step 3: 验证登录成功
- ✅ 登录后跳转到项目列表页
- ✅ 页面顶部显示用户名

**如果登录失败**，检查：
```bash
# 检查Demo用户是否存在
cd backend
uv run python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
print('Demo用户存在:', User.objects.filter(username='demo_user').exists())
"
```

---

### 2. 项目管理功能

#### Step 1: 查看项目列表
- 登录后应该看到项目列表
- 如果没有项目，列表为空

#### Step 2: 创建新项目
1. 点击"创建项目"按钮
2. 填写项目信息：
   - 项目名称: `测试项目`
   - 项目描述: `人工测试项目`
3. 点击"确定"

**预期结果**：
- ✅ 项目创建成功
- ✅ 项目出现在列表中
- ✅ 项目状态显示为"待开始"

#### Step 3: 启动工作流
1. 点击项目的"启动"按钮
2. 观察项目状态变化

**预期结果**：
- ✅ 项目状态变为"进行中"
- ✅ 实时显示进度更新
- ✅ WebSocket连接正常（进度实时推送）

---

### 3. Mock AI功能测试

#### Step 1: 测试文案改写
1. 进入项目详情
2. 在"故事主题"输入: `测试主题`
3. 点击"生成文案"

**预期结果**：
- ✅ 文案自动生成（使用Mock AI）
- ✅ 响应快速（<3秒）
- ✅ 显示生成的文案内容

#### Step 2: 测试完整工作流
1. 依次点击各个阶段的"启动"按钮：
   - 文案改写 ✅
   - 分镜生成 ✅
   - 文生图 ✅
   - 运镜生成 ✅
   - 图生视频 ✅

**预期结果**：
- ✅ 每个阶段都能正常完成
- ✅ 进度实时更新
- ✅ WebSocket连接稳定

---

### 4. 管理员后台检查

#### Step 1: 访问Admin后台
```
URL: http://localhost:8000/admin/
```

**注意**：Admin后台使用端口8000，该端口提供完整的静态文件服务

#### Step 2: 登录管理员账户
**创建管理员账户**（如果不存在）：
```bash
cd backend
uv run python manage.py createsuperuser
```

#### Step 3: 检查数据模型
在Admin后台验证：
- ✅ Users - 用户管理
- ✅ Projects - 项目管理
- ✄ Scenes - 分镜管理
- ✅ Prompts - 提示词管理
- ✄ AI Models - AI模型管理
- ✅ Proxy Configs - 代理配置（Epic 9）

**Epic 9功能检查**：
1. 点击"Proxy configs"
2. 应该能看到代理配置列表
3. 可以测试代理连接（如果有配置）

---

### 5. WebSocket实时通信检查

#### Step 1: 打开浏览器开发者工具
- F12 → Network → WS (WebSocket)

#### Step 2: 观察WebSocket连接
**预期看到**：
- ✅ 连接到 `ws://localhost:8010/ws/projects/{project_id}/`
- ✅ 心跳消息正常发送
- ✅ 进度推送消息正常接收

#### Step 3: 测试断线重连
1. 停止后端服务: `pkill -f daphne`
2. 观察前端反应：
   - ✅ 显示连接断开提示
   - ✅ 自动尝试重连
3. 重启后端服务
   - ✅ 自动重新连接
   - ✅ 恢复实时更新

---

### 6. Celery异步任务检查

#### Step 1: 查看Celery日志
```bash
tail -f /tmp/celery.log
```

**预期看到**：
- ✅ Worker启动信息
- ✅ 任务接收记录
- ✅ 任务执行日志

#### Step 2: 检查任务队列
```bash
cd backend
uv run python manage.py shell
```

```python
from celery import current_app
 inspect = current_app.control.inspect()
 print('Active tasks:', inspect.active())
 print('Scheduled tasks:', inspect.scheduled())
 print('Registered tasks:', inspect.registered())
```

**预期结果**：
- ✅ 显示已注册的任务列表
- ✅ 没有失败的任务

---

## 🔍 性能检查（可选）

### 1. 响应时间检查

```bash
# API响应时间
time curl http://localhost:8010/api/v1/health/

# 前端页面加载时间
# 在浏览器开发者工具中查看Network标签
```

**预期**：
- ✅ 健康检查 < 1秒
- ✅ 前端首屏 < 3秒

### 2. 资源使用检查

```bash
# CPU和内存使用
htop

# 或者使用top
top -p $(pgrep -d',' daphne celery webpack)
```

**预期**：
- ✅ CPU使用率 < 50%（空闲时）
- ✅ 内存使用合理（<2GB）

---

## 📊 测试覆盖率检查

### 1. 运行单元测试

```bash
cd backend
pytest -v
```

**预期**：
- ✅ 所有测试通过
- ✅ 测试覆盖率 > 80%

### 2. 查看覆盖率报告

```bash
# 生成HTML覆盖率报告
pytest --cov=apps/ --cov-report=html

# 打开报告
firefox htmlcov/index.html
```

---

## 🐛 常见问题排查

### 问题1: 前端无法连接后端

**症状**: 浏览器控制台显示连接错误

**检查**:
```bash
# 1. 后端是否运行
lsof -i :8010

# 2. 后端日志是否有错误
tail -f /tmp/daphne.log

# 3. CORS配置是否正确
# 查看backend/config/settings/base.py
```

**解决方案**:
- 确保后端服务运行在8010端口
- 检查CORS设置允许localhost:3000

---

### 问题2: WebSocket连接失败

**症状**: 进度不实时更新

**检查**:
```bash
# 1. WebSocket路由是否配置
curl http://localhost:8010/api/v1/health/ | jq '.checks.redis_channels'

# 2. Channels Redis是否正常
redis-cli -n 3 ping
```

**解决方案**:
- 重启Redis Channels数据库
- 检查config/asgi.py配置

---

### 问题3: Celery任务不执行

**症状**: 任务一直处于"pending"状态

**检查**:
```bash
# 1. Celery Worker是否运行
ps aux | grep celery

# 2. Celery日志
tail -f /tmp/celery.log

# 3. Redis Broker是否正常
redis-cli -n 0 ping
```

**解决方案**:
- 重启Celery Worker
- 清空任务队列: `redis-cli -n 0 flushdb`

---

### 问题4: 登录失败

**症状**: 用户名或密码错误

**检查**:
```bash
# 1. 用户是否存在
cd backend
uv run python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.filter(username='demo_user').first()
print('User:', user)
if user:
    print('Is active:', user.is_active)
    print('Is staff:', user.is_staff)
"

# 2. 如果用户不存在，创建Demo环境
uv run python scripts/init_demo_env.py
```

---

## ✅ 检查完成确认

完成所有检查后，确认以下项目：

- [ ] ✅ 所有服务进程正常运行
- [ ] ✅ 健康检查端点返回healthy
- [ ] ✅ 前端应用可访问
- [ ] ✅ Demo用户登录成功
- [ ] ✅ 项目创建和管理功能正常
- [ ] ✅ Mock AI工作流正常执行
- [ ] ✅ WebSocket实时通信稳定
- [ ] ✅ Celery异步任务正常执行
- [ ] ✅ Admin后台可访问
- [ ] ✅ 测试覆盖率达标

---

## 📝 检查记录

**检查日期**: _______________

**检查人**: _______________

**检查结果**:
- [ ] ✅ 全部通过
- [ ] ⚠️ 部分通过（需记录问题）
- [ ] ❌ 未通过（需详细排查）

**发现的问题**:
1. _______________________________
2. _______________________________
3. _______________________________

**解决方案**:
1. _______________________________
2. _______________________________
3. _______________________________

**后续行动**:
- [ ] 问题已修复
- [ ] 需要进一步调查
- [ ] 需要技术支持

---

## 🆘 获取帮助

如果遇到问题：

1. **查看文档**:
   - [文档中心](../docs/index.md)
   - [故障排查指南](../docs/guides/troubleshooting/)
   - [快速开始](../docs/QUICKSTART.md)

2. **检查日志**:
   - Admin服务器: `tail -f /tmp/admin.log`
   - ASGI服务器: `tail -f /tmp/daphne.log`
   - Celery: `tail -f /tmp/celery.log`
   - 前端: `tail -f /tmp/frontend.log`

3. **重启服务**:
   ```bash
   # 使用一键启动脚本
   ./start_all.sh

   # 或者手动重启
   pkill -f "daphne|celery|webpack"
   ./start_all.sh
   ```

4. **联系团队**:
   - 提交Issue到项目仓库
   - 联系项目维护者

---

**检查清单版本**: v1.0
**最后更新**: 2026-01-31
**维护团队**: AI Story Development Team
