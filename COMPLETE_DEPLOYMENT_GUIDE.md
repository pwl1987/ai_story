# AI Story 完整部署操作手册

> 版本: 1.1.0
> 适用场景: 测试环境完整部署
> 预计耗时: 30-45分钟
> 前置条件: Docker环境已就绪、基础配置已验证

---

## 前置条件检查

### 1. 环境要求

- [x] Docker 20.10+
- [x] Docker Compose v2.0+
- [x] 内存 ≥4GB
- [x] 磁盘 ≥10GB
- [x] 端口80/443/8000/5432/6379可用

### 2. 配置文件检查

- [x] docker-compose.prod.yml（已验证）
- [x] .env文件（已配置）
- [x] backend/Dockerfile.prod（已创建）
- [x] deploy/nginx配置（已创建）

---

## 部署步骤

### 步骤1：启动后端服务（5-10分钟）

**目标：** 启动Django ASGI服务器和Celery工作进程

**操作命令：**
```bash
# 启动backend和celery服务
docker compose -f docker-compose.prod.yml up -d backend celery_worker celery_beat
```

**预期输出：**
```
✓ Pulling backend image (or building from scratch)
✓ Creating ai_story_backend
✓ Creating ai_story_celery_worker
✓ Creating ai_story_celery_beat
✓ Starting ai_story_backend
✓ Starting ai_story_celery_worker
✓ Starting ai_story_celery_beat
```

**验证方法：**
```bash
# 检查容器状态
docker compose -f docker-compose.prod.yml ps

# 预期输出：
# NAME                      STATUS
# ai_story_backend           Up 30 seconds (healthy)
# ai_story_celery_beat       Up 30 seconds
# ai_story_celery_worker     Up 30 seconds
# ai_story_postgres          Up 5 minutes (healthy)
# ai_story_redis             Up 5 minutes (healthy)
```

**故障排查：**
```bash
# 查看backend日志
docker compose -f docker-compose.prod.yml logs backend

# 查看celery日志
docker compose -f docker-compose.prod.yml logs celery_worker

# 常见错误：
# 1. "Connection refused" → PostgreSQL未就绪，等待30秒后重试
# 2. "Module not found" → requirements.txt缺少依赖，添加后重新构建
# 3. "Permission denied" → 检查文件权限，docker compose down后重新up
```

---

### 步骤2：构建前端静态文件（5-10分钟）

**目标：** 构建Vue生产环境静态文件

**操作命令：**
```bash
# 进入前端目录
cd frontend

# 安装依赖（如果未安装）
npm install

# 构建生产环境静态文件
npm run build
```

**预期输出：**
```
✓ Building for production...
✓ Hashed files
✓ Generated dist directory
✓ Build complete in 45.23s
```

**验证方法：**
```bash
# 检查dist目录
ls -lh dist/

# 预期输出：
# total 1.2M
# -rw-r--r-- 1 root root 1.2M Jan 27 15:00 index.html
# drwxr-xr-x 3 root root 4.0K Jan 27 15:00 static
```

**故障排查：**
```bash
# 常见错误：
# 1. "npm: command not found" → 安装Node.js 16+
# 2. "Cannot resolve dependency" → 删除node_modules后重新npm install
# 3. "Build failed" → 检查Node.js版本是否符合package.json要求
```

---

### 步骤3：启动前端服务（2分钟）

**目标：** 启动Nginx服务，提供前端静态文件和API反向代理

**操作命令：**
```bash
# 返回项目根目录
cd ..

# 启动frontend服务
docker compose -f docker-compose.prod.yml up -d frontend
```

**预期输出：**
```
✓ Creating ai_story_frontend
✓ Starting ai_story_frontend
```

**验证方法：**
```bash
# 检查所有服务状态
docker compose -f docker-compose.prod.yml ps

# 预期输出：
# NAME                      STATUS          PORTS
# ai_story_backend           Up 2 minutes (healthy)   0.0.0.0:8000->8000/tcp
# ai_story_celery_beat       Up 2 minutes               0.0.0.0:5555->5555/tcp
# ai_story_celery_worker     Up 2 minutes
# ai_story_frontend         Up 10 seconds             0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
# ai_story_postgres          Up 10 minutes (healthy)    0.0.0.0:5432->5432/tcp
# ai_story_redis             Up 10 minutes (healthy)    0.0.0.0:6379->6379/tcp
```

---

### 步骤4：数据库初始化（3分钟）

**目标：** 应用数据库迁移并创建超级用户

**操作命令：**
```bash
# 运行数据库迁移
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 创建超级用户
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

**预期输出（migrate）：**
```
✓ Running migrations:
✓ Applying content.0001_initial... OK
✓ Applying content.0002_***... OK
...
✓ Applying projects.0001_initial... OK
✓ Applying sessions.0001_initial... OK
```

**预期输出（createsuperuser）：**
```
Username (leave blank to use 'admin'): admin
Email address: admin@example.com
Password: ********
Password (again): ********
✓ Superuser created successfully.
```

**验证方法：**
```bash
# 检查迁移记录
docker compose -f docker-compose.prod.yml exec backend python manage.py showmigrations

# 登录Django Admin验证
curl -I http://localhost:8000/admin/
# 预期：HTTP/1.1 200 OK 或 302 Found
```

---

### 步骤5：功能验证测试（5分钟）

**目标：** 验证所有核心功能正常工作

**5.1 前端访问测试**

```bash
# 测试前端首页
curl -I http://localhost/

# 预期输出：
# HTTP/1.1 200 OK
# Content-Type: text/html
```

**5.2 后端API测试**

```bash
# 测试健康检查端点
curl http://localhost:8000/api/v1/health/

# 预期输出：
# {"status":"healthy","timestamp":"2026-01-27T15:00:00Z"}
```

**5.3 WebSocket连接测试**

```bash
# 使用wscat测试（需要先安装：npm install -g wscat）
wscat -c ws://localhost:8000/ws/projects/test-project/

# 预期输出：
# Connected (press Ctrl+C to quit)
# > {"type":"connected","project_id":"test-project"}
```

**5.4 创建测试项目**

```bash
# 通过Web界面访问
open http://localhost

# 操作步骤：
# 1. 点击"创建项目"
# 2. 填写项目信息
# 3. 点击"保存"
# 4. 验证项目创建成功
```

---

## 部署验证清单

### 服务状态检查

- [ ] 所有6个容器运行中
- [ ] backend服务健康（HTTP 200）
- [ ] frontend服务响应（首页可访问）
- [ ] postgres服务健康（可连接）
- [ ] redis服务健康（可ping通）
- [ ] celery_worker运行中（日志无错误）

### 功能验证检查

- [ ] 前端首页可访问
- [ ] Django Admin可登录（http://localhost:8000/admin/）
- [ ] API健康检查端点返回200
- [ ] 可创建新项目
- [ ] 数据库迁移无错误
- [ ] 静态文件正确加载

### 日志检查

- [ ] backend日志无ERROR级别
- [ ] celery_worker日志无ERROR级别
- [ ] nginx访问日志正常
- [ ] postgres日志无WARNING

---

## 常见问题快速修复

### 问题1：backend容器启动失败

**症状：** backend容器状态为Restarting

**排查：**
```bash
docker compose -f docker-compose.prod.yml logs backend
```

**常见原因与修复：**
1. 数据库未就绪 → 等待30秒后重启
2. 环境变量错误 → 检查.env文件
3. 端口8000被占用 → 停止占用进程

### 问题2：前端404错误

**症状：** 访问http://localhost返回404

**排查：**
```bash
docker compose -f docker-compose.prod.yml logs frontend
ls -lh frontend/dist/
```

**修复：**
```bash
# 重新构建前端
cd frontend
npm run build
cd ..

# 重启frontend服务
docker compose -f docker-compose.prod.yml restart frontend
```

### 问题3：数据库迁移失败

**症状：** migrate命令返回错误

**排查：**
```bash
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U ai_story
```

**修复：**
```bash
# 等待数据库完全启动
sleep 30

# 重新运行迁移
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

---

## 回滚操作

如果部署遇到无法解决的问题，执行以下回滚步骤：

```bash
# 1. 停止所有服务
docker compose -f docker-compose.prod.yml down

# 2. 清理容器和网络（保留数据卷）
docker compose -f docker-compose.prod.yml rm -fv

# 3. 检查日志
docker compose -f docker-compose.prod.yml logs > logs/debug.log

# 4. 重新部署（修复问题后）
./scripts/deploy-all.sh
```

---

## 附录：一键部署脚本

### 完整部署脚本（deploy-all.sh）

```bash
#!/bin/bash
set -e

echo "=========================================="
echo "AI Story - 一键部署脚本"
echo "=========================================="
echo ""

# 步骤1：启动后端服务
echo "步骤1：启动后端服务..."
docker compose -f docker-compose.prod.yml up -d backend celery_worker celery_beat
echo "等待服务启动..."
sleep 30

# 步骤2：验证后端服务
echo ""
echo "步骤2：验证后端服务..."
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs backend | tail -10

# 步骤3：构建前端
echo ""
echo "步骤3：构建前端静态文件..."
cd frontend
npm install
npm run build
cd ..

# 步骤4：启动前端服务
echo ""
echo "步骤4：启动前端服务..."
docker compose -f docker-compose.prod.yml up -d frontend

# 步骤5：数据库初始化
echo ""
echo "步骤5：数据库初始化..."
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
echo "请手动创建超级用户："
echo "docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser"

# 步骤6：验证部署
echo ""
echo "步骤6：验证部署..."
./scripts/validate-config.sh

echo ""
echo "=========================================="
echo "✓ 部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  前端：http://localhost"
echo "  后端API：http://localhost:8000/api/v1/"
echo "  Django Admin：http://localhost:8000/admin/"
```

---

## 下一步操作

部署完成后，建议执行以下操作：

1. **访问应用**（通过浏览器）
   - 前端：http://localhost
   - Django Admin：http://localhost:8000/admin/

2. **创建测试项目**
   - 登录系统
   - 创建新项目
   - 配置提示词和模型
   - 启动工作流

3. **监控系统**
   - 查看容器状态：`docker compose ps`
   - 查看日志：`docker compose logs -f`
   - 查看资源：`docker stats`

4. **记录部署时间**
   - 总耗时：_____分钟
   - 遇到问题：_____
   - 解决方案：_____
