# 端到端测试脚本使用指南

本目录包含端到端测试所需的自动化脚本。

---

## 脚本列表

### 1. setup_mock_env.py
**功能**: 创建Mock环境的ModelProvider

**创建内容**:
- Mock LLM Provider
- Mock Text2Image Provider
- Mock Image2Video Provider

**运行方式**:
```bash
cd backend
uv run python scripts/setup_mock_env.py
```

**输出**:
```
============================================================
Mock环境配置
============================================================
✓ 创建 Mock LLM Provider: Mock LLM for E2E Test
✓ 创建 Mock Text2Image Provider: Mock Text2Image for E2E Test
✓ 创建 Mock Image2Video Provider: Mock Image2Video for E2E Test

============================================================
✓ Mock环境配置完成
============================================================
```

---

### 2. create_test_project.py
**功能**: 创建端到端测试项目

**创建内容**:
- 测试用户（e2e_test_user）
- PromptTemplateSet（包含5个模板）
- 测试项目（E2E Test Project）
- 5个项目阶段
- ProjectModelConfig（关联Mock Providers）

**依赖**: 需要先运行 `setup_mock_env.py`

**运行方式**:
```bash
cd backend
uv run python scripts/create_test_project.py
```

**输出**:
```
============================================================
创建E2E测试项目
============================================================
1. 创建/获取测试用户...
− 已存在用户: e2e_test_user

2. 创建PromptTemplateSet...
− 已存在提示词集: E2E Test Prompt Set

3. 创建/更新5个PromptTemplate...
  ✓ 创建模板: rewrite
  ✓ 创建模板: storyboard
  ✓ 创建模板: image_generation
  ✓ 创建模板: camera_movement
  ✓ 创建模板: video_generation

4. 获取Mock Providers...
✓ 获取Mock Providers成功

5. 创建测试项目...
✓ 创建项目: E2E Test Project (ID: xxx)

6. 创建5个项目阶段...
  ✓ 创建阶段: rewrite
  ✓ 创建阶段: storyboard
  ✓ 创建阶段: image_generation
  ✓ 创建阶段: camera_movement
  ✓ 创建阶段: video_generation

7. 配置项目模型...
✓ 配置模型完成

============================================================
✓ 测试项目创建完成
============================================================
```

---

### 3. test_e2e_workflow.py
**功能**: 测试完整工作流执行

**测试流程**:
1. 获取认证token
2. 获取测试项目
3. 调用 `execute_full_pipeline` API
4. 监控工作流进度
5. 验证5个阶段依次执行

**依赖**:
- 需要先运行 `setup_mock_env.py`
- 需要先运行 `create_test_project.py`
- 需要启动Redis
- 需要启动Celery Worker
- 需要启动Django ASGI

**运行方式**:
```bash
cd backend
uv run python scripts/test_e2e_workflow.py
```

**输出**:
```
============================================================
端到端工作流测试
============================================================

1. 获取认证token...
✓ 登录成功

2. 获取测试项目...
✓ 找到测试项目: E2E Test Project (ID: xxx)
  状态: draft
  阶段数: 5

3. 启动工作流...
✓ 工作流已启动
  任务ID: xxx
  频道: ai_story:project:xxx:pipeline
  项目ID: xxx

4. 监控工作流进度...
  进度: [██████████] 5/5 | 状态: processing | 已用时: 15秒

✓ 工作流完成！

  阶段详情:
    - rewrite: completed
    - storyboard: completed
    - image_generation: completed
    - camera_movement: completed
    - video_generation: completed

============================================================
✓ 端到端测试通过
============================================================
```

---

## 完整测试流程

### Step 1: 准备Mock环境
```bash
cd backend
uv run python scripts/setup_mock_env.py
```

### Step 2: 创建测试项目
```bash
cd backend
uv run python scripts/create_test_project.py
```

### Step 3: 启动服务

**终端1**: 启动Redis
```bash
docker run -d -p 6379:6379 redis:latest
```

**终端2**: 启动Celery Worker
```bash
cd backend
uv run celery -A config worker -Q llm,image,video -l info
```

**终端3**: 启动Django ASGI
```bash
cd backend
./run_asgi.sh
```

### Step 4: 运行测试
```bash
cd backend
uv run python scripts/test_e2e_workflow.py
```

---

## 故障排查

### Q: Django setup失败，提示"No module named 'config'"？

A: 确保在backend目录下运行脚本：
```bash
cd backend
uv run python scripts/setup_mock_env.py
```

### Q: Redis连接失败？

A: 检查Redis是否运行：
```bash
docker ps | grep redis
redis-cli ping  # 应返回 PONG
```

### Q: Celery Worker无法启动？

A: 检查配置：
```bash
# 确保在backend目录下
cd backend

# 检查环境变量
echo $REDIS_URL  # 应该设置为 redis://localhost:6379/0

# 启动Worker（详细日志）
uv run celery -A config worker -Q llm,image,video -l debug
```

### Q: API调用返回401 Unauthorized？

A: 检查认证：
```bash
# 确保用户存在
uv run python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(username='e2e_test_user').exists()
```

### Q: 工作流卡在processing状态？

A: 检查Celery任务：
```bash
# 查看Celery日志
# 应该看到任务执行日志

# 检查Redis队列
redis-cli -n 0
> LLEN celery  # 查看任务队列长度
> LRANGE celery 0 -1  # 查看队列中的任务
```

---

## 验收清单

- [ ] 3个Mock ModelProvider已创建
- [ ] PromptTemplateSet和5个PromptTemplate已创建
- [ ] 测试项目已创建并关联Mock配置
- [ ] Redis运行中
- [ ] Celery Worker运行中
- [ ] Django ASGI运行中
- [ ] execute_full_pipeline API调用成功（202状态码）
- [ ] 阶段1: rewrite完成
- [ ] 阶段2: storyboard完成
- [ ] 阶段3: image_generation完成
- [ ] 阶段4: camera_movement完成
- [ ] 阶段5: video_generation完成
- [ ] 项目状态: completed

---

## 清理测试数据

如需清理测试数据：
```bash
cd backend
uv run python manage.py shell
```

```python
from apps.projects.models import Project
from django.contrib.auth import get_user_model

User = get_user_model()

# 删除测试项目
Project.objects.filter(name='E2E Test Project').delete()

# 删除测试用户
User.objects.filter(username='e2e_test_user').delete()

# 退出
exit()
```
