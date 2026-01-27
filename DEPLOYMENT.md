# AI Story 生产环境部署手册

> 版本: 1.0.0
> 最后更新: 2026-01-27
> 预计部署时间: 30-60分钟

---

## 目录

1. [前置要求](#前置要求)
2. [快速开始](#快速开始)
3. [详细配置](#详细配置)
4. [部署步骤](#部署步骤)
5. [验证测试](#验证测试)
6. [日常运维](#日常运维)
7. [故障排查](#故障排查)
8. [常见问题](#常见问题)

---

## 前置要求

### 硬件要求

| 资源 | 最低配置 | 推荐配置 | 说明 |
|------|---------|---------|------|
| CPU | 2核 | 4核+ | AI任务密集，建议多核 |
| 内存 | 4GB | 8GB+ | Celery worker需要内存 |
| 磁盘 | 20GB | 50GB+ | 媒体文件存储 |
| 网络 | 10Mbps | 100Mbps+ | 视频生成需要较高带宽 |

### 软件要求

| 软件 | 版本要求 | 用途 |
|------|---------|------|
| Docker | ≥20.10 | 容器运行时 |
| Docker Compose | ≥2.0 | 服务编排 |
| Git | ≥2.0 | 代码拉取 |
| Nginx | ≥1.18 | 反向代理（可选） |

**安装Docker：**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 验证安装
docker --version
docker-compose --version
```

### 网络要求

- **开放端口：** 80（HTTP）、443（HTTPS）
- **内网通信：** Docker容器间互通
- **外网访问：** 如需外部访问，配置域名和DNS

---

## 快速开始

### 5分钟快速部署（开发/测试环境）

```bash
# 1. 克隆代码
git clone https://github.com/your-org/ai_story.git
cd ai_story

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，修改 [REQUIRED] 变量

# 3. 生成密钥
SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
sed -i "s/SECRET_KEY=\[REQUIRED\]/SECRET_KEY=$SECRET_KEY/" .env

POSTGRES_PASSWORD=$(openssl rand -base64 32)
sed -i "s/POSTGRES_PASSWORD=\[REQUIRED\]/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env

REDIS_PASSWORD=$(openssl rand -base64 32)
sed -i "s/REDIS_PASSWORD=\[REQUIRED\]/REDIS_PASSWORD=$REDIS_PASSWORD/" .env

# 4. 构建并启动
docker-compose -f docker-compose.prod.yml up -d

# 5. 初始化数据库
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# 6. 访问应用
# 前端: http://localhost
# 后端API: http://localhost/api/v1/
# Django Admin: http://localhost/admin/
```

---

## 详细配置

### 1. 环境变量配置

#### 必需配置项

```bash
# .env 文件
SECRET_KEY=your-generated-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

POSTGRES_DB=ai_story
POSTGRES_USER=ai_story
POSTGRES_PASSWORD=your-strong-password

REDIS_PASSWORD=your-strong-redis-password
```

#### 可选配置项

```bash
# AI服务（根据需要配置）
OPENAI_API_KEY=sk-proj-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx

# CORS配置
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# 日志级别
LOG_LEVEL=INFO
```

**详细配置说明请参考：** [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md)

### 2. SSL/TLS配置（生产环境必须）

#### 使用Let's Encrypt

```bash
# 安装certbot
sudo apt-get install certbot

# 停止Nginx（避免80端口冲突）
docker-compose -f docker-compose.prod.yml stop frontend

# 生成证书
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 复制证书
mkdir -p deploy/nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem deploy/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem deploy/nginx/ssl/key.pem

# 设置权限
sudo chmod 644 deploy/nginx/ssl/cert.pem
sudo chmod 600 deploy/nginx/ssl/key.pem

# 重启前端
docker-compose -f docker-compose.prod.yml start frontend
```

#### 自动续期

```bash
# 添加crontab任务
sudo crontab -e

# 添加以下行（每月1号凌晨3点续期）
0 3 1 * * certbot renew --quiet --post-hook "docker-compose -f /path/to/ai_story/docker-compose.prod.yml restart frontend"
```

### 3. 域名和DNS配置

#### DNS记录

| 类型 | 名称 | 值 | TTL |
|------|------|-----|-----|
| A | @ | 你的服务器IP | 600 |
| A | www | 你的服务器IP | 600 |

**验证DNS：**
```bash
nslookup yourdomain.com
ping yourdomain.com
```

---

## 部署步骤

### Step 1: 准备服务器环境

```bash
# 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 创建工作目录
sudo mkdir -p /opt/ai_story
sudo chown $USER:$USER /opt/ai_story
```

### Step 2: 部署代码

```bash
# 克隆代码
cd /opt/ai_story
git clone https://github.com/your-org/ai_story.git .
git checkout develop  # 或使用生产分支

# 配置环境变量
cp .env.example .env
nano .env  # 编辑配置文件
```

### Step 3: 构建镜像

```bash
# 构建所有服务镜像
docker-compose -f docker-compose.prod.yml build

# 验证镜像
docker images | grep ai_story
```

### Step 4: 启动服务

```bash
# 启动所有服务
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 5: 初始化数据库

```bash
# 运行数据库迁移
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# 创建超级用户
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# 加载初始数据（可选）
docker-compose -f docker-compose.prod.yml exec backend python manage.py loaddata initial_data
```

### Step 6: 验证部署

```bash
# 检查服务健康状态
curl http://localhost/health
curl http://localhost/api/v1/health/

# 查看容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs --tail=50
```

---

## 验证测试

### 1. 服务健康检查

```bash
# 检查所有容器状态
docker-compose -f docker-compose.prod.yml ps

# 预期输出：
# NAME                      STATUS
# ai_story_backend          Up (healthy)
# ai_story_celery_beat      Up
# ai_story_celery_worker    Up
# ai_story_frontend         Up
# ai_story_postgres         Up (healthy)
# ai_story_redis            Up (healthy)
```

### 2. 功能测试

#### 前端访问测试
```bash
# 访问前端
curl -I http://localhost/

# 预期输出：HTTP/1.1 200 OK
```

#### 后端API测试
```bash
# 测试API端点
curl http://localhost/api/v1/

# 预期输出：API路由列表
```

#### WebSocket连接测试
```bash
# 使用wscat测试WebSocket
npm install -g wscat
wscat -c ws://localhost/ws/projects/test-project/

# 预期输出：WebSocket连接成功
```

### 3. 性能测试

#### 简单压力测试
```bash
# 安装Apache Bench
sudo apt-get install apache2-utils

# 测试并发请求
ab -n 1000 -c 10 http://localhost/

# 预期结果：
# - 0个失败请求
# - 90%请求在2秒内完成
```

---

## 日常运维

### 1. 日志查看

```bash
# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f celery_worker

# 查看最近100行日志
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### 2. 数据备份

#### 数据库备份
```bash
# 创建备份目录
mkdir -p /opt/backups/ai_story

# 备份数据库
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U ai_story ai_story > /opt/backups/ai_story/db_$(date +%Y%m%d_%H%M%S).sql

# 定时备份（crontab）
0 2 * * * docker-compose -f /opt/ai_story/docker-compose.prod.yml exec -T postgres pg_dump -U ai_story ai_story > /opt/backups/ai_story/db_$(date +\%Y\%m\%d).sql
```

#### 媒体文件备份
```bash
# 备份媒体文件
docker run --rm -v ai_story_backend_media:/data -v /opt/backups/ai_story:/backup alpine tar czf /backup/media_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

#### 恢复备份
```bash
# 恢复数据库
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U ai_story ai_story < /opt/backups/ai_story/db_20260127.sql

# 恢复媒体文件
docker run --rm -v ai_story_backend_media:/data -v /opt/backups/ai_story:/backup alpine tar xzf /backup/media_20260127.tar.gz -C /data
```

### 3. 服务重启

```bash
# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart celery_worker
```

### 4. 更新部署

```bash
# 拉取最新代码
git pull origin develop

# 重新构建镜像
docker-compose -f docker-compose.prod.yml build

# 重启服务（零停机）
docker-compose -f docker-compose.prod.yml up -d --no-deps --build backend

# 运行数据库迁移
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### 5. 资源监控

```bash
# 查看容器资源使用
docker stats

# 查看磁盘使用
docker system df

# 清理未使用的资源
docker system prune -a --volumes
```

---

## 故障排查

### 问题1: 容器无法启动

**症状：**
```bash
docker-compose ps
# 显示 Exit 1 或 Restarting
```

**排查步骤：**
```bash
# 1. 查看容器日志
docker-compose -f docker-compose.prod.yml logs backend

# 2. 检查配置文件
docker-compose -f docker-compose.prod.yml config

# 3. 验证环境变量
docker-compose -f docker-compose.prod.yml exec backend env | grep SECRET_KEY
```

**常见原因：**
- 环境变量未配置或配置错误
- 端口冲突
- 磁盘空间不足
- 内存不足

---

### 问题2: 数据库连接失败

**症状：**
```
django.db.utils.OperationalError: could not connect to server
```

**排查步骤：**
```bash
# 1. 检查PostgreSQL容器状态
docker-compose -f docker-compose.prod.yml ps postgres

# 2. 测试数据库连接
docker-compose -f docker-compose.prod.yml exec backend python manage.py dbshell

# 3. 检查数据库日志
docker-compose -f docker-compose.prod.yml logs postgres
```

**解决方案：**
- 确认 `POSTGRES_PASSWORD` 配置正确
- 等待PostgreSQL完全启动（健康检查通过）
- 检查网络连接

---

### 问题3: Celery任务不执行

**症状：**
- 任务提交后无响应
- 任务状态一直是 `PENDING`

**排查步骤：**
```bash
# 1. 检查Celery Worker状态
docker-compose -f docker-compose.prod.yml logs celery_worker

# 2. 检查Redis连接
docker-compose -f docker-compose.prod.yml exec celery_worker celery -A config inspect active

# 3. 查看队列长度
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a [REDIS_PASSWORD] -n 0 LLEN celery
```

**解决方案：**
- 确认 `CELERY_BROKER_URL` 配置正确
- 重启Celery Worker
- 检查任务队列是否堵塞

---

### 问题4: WebSocket连接失败

**症状：**
- 前端无法建立WebSocket连接
- 浏览器控制台显示 `WebSocket connection failed`

**排查步骤：**
```bash
# 1. 测试WebSocket端点
wscat -c ws://localhost/ws/projects/test/

# 2. 检查Nginx配置
docker-compose -f docker-compose.prod.yml exec frontend nginx -t

# 3. 查看后端WebSocket日志
docker-compose -f docker-compose.prod.yml logs backend | grep WebSocket
```

**解决方案：**
- 确认Nginx配置中 `/ws/` 路径正确
- 检查防火墙是否允许WebSocket连接
- 确认Django Channels已正确配置

---

### 问题5: 磁盘空间不足

**症状：**
```
ERROR: no space left on device
```

**排查步骤：**
```bash
# 查看磁盘使用
df -h

# 查看Docker占用
docker system df
```

**解决方案：**
```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的容器
docker container prune

# 清理未使用的卷
docker volume prune

# 清理媒体文件旧数据
docker-compose -f docker-compose.prod.yml exec backend python manage.py cleanup_old_media
```

---

## 常见问题

### Q1: 如何修改系统配置？

**A:** 编辑 `.env` 文件，然后重启服务：
```bash
nano .env
docker-compose -f docker-compose.prod.yml restart
```

### Q2: 如何查看Celery任务执行情况？

**A:** 使用Flower监控工具：
```bash
# 添加flower服务到docker-compose.prod.yml
# 访问 http://localhost:5555
```

### Q3: 如何优化性能？

**A:** 参考以下优化建议：
1. 增加Celery Worker并发数
2. 启用Redis缓存
3. 配置Nginx Gzip压缩
4. 使用CDN加速静态资源

### Q4: 如何配置HTTPS？

**A:** 参考 [SSL/TLS配置](#2-ssltls配置生产环境必须) 章节。

### Q5: 如何升级到新版本？

**A:**
```bash
git pull origin main
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

---

## 参考资源

- [Docker Compose文档](https://docs.docker.com/compose/)
- [Django部署指南](https://docs.djangoproject.com/en/4.2/howto/deployment/)
- [Nginx配置指南](https://nginx.org/en/docs/)
- [环境变量配置](./ENVIRONMENT_VARIABLES.md)

---

## 技术支持

如遇到问题，请：
1. 查看本文档的 [故障排查](#故障排查) 章节
2. 查看日志文件：`docker-compose logs`
3. 提交Issue到GitHub仓库

---

## 变更记录

### 2026-01-27
- 初始化部署手册
- 添加完整部署流程
- 添加故障排查指南
- 添加常见问题解答
