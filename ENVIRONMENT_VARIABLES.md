# 环境变量配置文档

> 最后更新: 2026-01-27
> 版本: 1.0.0

---

## 快速开始

1. **复制示例配置文件**
   ```bash
   cp .env.example .env
   ```

2. **编辑 `.env` 文件**
   - 修改所有标记为 `[REQUIRED]` 的变量
   - 根据实际情况调整其他变量

3. **验证配置**
   ```bash
   docker-compose -f docker-compose.prod.yml config
   ```

---

## 核心配置项

### 1. Django基础配置

| 变量名 | 必需 | 默认值 | 说明 | 生成方法 |
|--------|------|--------|------|---------|
| `SECRET_KEY` | ✅ | 无 | Django密钥 | `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | ✅ | `False` | 调试模式 | 生产环境必须为False |
| `ALLOWED_HOSTS` | ✅ | `localhost,127.0.0.1` | 允许的主机 | 逗号分隔，包含实际域名 |

**示例：**
```bash
SECRET_KEY=django-insecure-#your-generated-key-here
DEBUG=False
ALLOWED_HOSTS=ai-story.example.com,www.ai-story.example.com
```

---

### 2. 数据库配置 (PostgreSQL)

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `POSTGRES_DB` | ✅ | `ai_story` | 数据库名称 |
| `POSTGRES_USER` | ✅ | `ai_story` | 数据库用户名 |
| `POSTGRES_PASSWORD` | ✅ | 无 | 数据库密码（强密码） |
| `POSTGRES_HOST` | ❌ | `postgres` | 数据库主机（Docker服务名） |
| `POSTGRES_PORT` | ❌ | `5432` | 数据库端口 |

**密码生成：**
```bash
openssl rand -base64 32
```

**示例：**
```bash
POSTGRES_DB=ai_story
POSTGRES_USER=ai_story
POSTGRES_PASSWORD=xK9#mP2$vL8@qR5&wN3
```

---

### 3. Redis配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `REDIS_PASSWORD` | ✅ | 无 | Redis密码（强密码） |
| `REDIS_HOST` | ❌ | `redis` | Redis主机（Docker服务名） |
| `REDIS_PORT` | ❌ | `6379` | Redis端口 |

**用途：**
- 数据库0: Celery任务队列
- 数据库1: Celery结果存储
- 数据库2: Redis Pub/Sub
- 数据库3: Django Channels层
- 数据库4: Django缓存

**示例：**
```bash
REDIS_PASSWORD=yH7#kJ9$pM4@qR2
```

---

### 4. Celery配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `CELERY_BROKER_URL` | ❌ | 自动生成 | Celery消息代理URL |
| `CELERY_RESULT_BACKEND` | ❌ | 自动生成 | Celery结果存储URL |

**说明：** 通常基于Redis配置自动生成，无需手动设置。

**自动生成格式：**
```bash
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/1
```

---

### 5. AI服务配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `OPENAI_API_KEY` | ❌ | 无 | OpenAI API密钥（GPT模型） |
| `ANTHROPIC_API_KEY` | ❌ | 无 | Anthropic API密钥（Claude模型） |
| `STABLE_DIFFUSION_API_URL` | ❌ | 无 | Stable Diffusion API端点 |
| `RUNWAY_API_URL` | ❌ | 无 | Runway API端点 |
| `COMFYUI_API_URL` | ❌ | 无 | ComfyUI API端点 |

**获取API密钥：**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/

**示例：**
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

---

### 6. CORS配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `CORS_ALLOWED_ORIGINS` | ❌ | `http://localhost` | 允许的跨域来源 |

**格式：** 逗号分隔的URL列表

**示例：**
```bash
# 开发环境
CORS_ALLOWED_ORIGINS=http://localhost,http://localhost:3000

# 生产环境
CORS_ALLOWED_ORIGINS=https://ai-story.example.com,https://www.ai-story.example.com
```

---

### 7. 媒体存储配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `STORAGE_ROOT` | ❌ | `/app/media` | 存储根目录 |
| `MAX_UPLOAD_SIZE` | ❌ | `100` | 最大上传大小（MB） |

**说明：** 媒体文件存储在Docker卷中，需定期备份。

---

### 8. 日志配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `LOG_LEVEL` | ❌ | `INFO` | 日志级别 |
| `LOG_FORMAT` | ❌ | `json` | 日志格式（json/text） |

**可用日志级别：**
- `DEBUG`: 详细调试信息
- `INFO`: 一般信息（推荐）
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

**示例：**
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

### 9. 端口配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `NGINX_HTTP_PORT` | ❌ | `80` | Nginx HTTP端口 |
| `NGINX_HTTPS_PORT` | ❌ | `443` | Nginx HTTPS端口 |
| `BACKEND_PORT` | ❌ | `8000` | Django后端端口 |
| `POSTGRES_PORT` | ❌ | `5432` | PostgreSQL端口 |
| `REDIS_PORT` | ❌ | `6379` | Redis端口 |

**说明：** 如需修改端口，确保防火墙和安全组规则同步更新。

---

### 10. SSL/TLS配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `SSL_CERT_PATH` | ❌ | `./deploy/nginx/ssl/cert.pem` | SSL证书路径 |
| `SSL_KEY_PATH` | ❌ | `./deploy/nginx/ssl/key.pem` | SSL私钥路径 |
| `FORCE_HTTPS` | ❌ | `True` | 强制HTTPS跳转 |

**获取SSL证书：**

#### 方法1: Let's Encrypt（推荐）
```bash
# 安装certbot
sudo apt-get install certbot

# 生成证书
sudo certbot certonly --standalone -d ai-story.example.com

# 复制证书
sudo cp /etc/letsencrypt/live/ai-story.example.com/fullchain.pem deploy/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/ai-story.example.com/privkey.pem deploy/nginx/ssl/key.pem
```

#### 方法2: 自签名证书（开发/测试）
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deploy/nginx/ssl/key.pem \
  -out deploy/nginx/ssl/cert.pem \
  -subj "/CN=ai-story.local"
```

---

### 11. 监控和告警（可选）

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `SENTRY_DSN` | ❌ | 无 | Sentry错误追踪DSN |
| `HEALTHCHECK_ENABLED` | ❌ | `True` | 启用健康检查 |

**Sentry配置：**
1. 访问 https://sentry.io/
2. 创建新项目
3. 获取DSN
4. 配置到环境变量

**示例：**
```bash
SENTRY_DSN=https://xxxxxxxxxxxxx@sentry.io/xxxxxxx
HEALTHCHECK_ENABLED=True
```

---

### 12. 性能优化

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `DB_POOL_SIZE` | ❌ | `20` | 数据库连接池大小 |
| `CELERY_WORKER_CONCURRENCY` | ❌ | `4` | Celery Worker并发数 |
| `CACHE_TIMEOUT` | ❌ | `3600` | 缓存超时时间（秒） |

**调优建议：**

| 场景 | DB_POOL_SIZE | CELERY_WORKER_CONCURRENCY |
|------|--------------|---------------------------|
| 小型（<100用户） | 10 | 2 |
| 中型（100-500用户） | 20 | 4 |
| 大型（>500用户） | 50 | 8 |

---

## 配置检查清单

### 部署前必检项

- [ ] 所有 `[REQUIRED]` 变量已配置
- [ ] `SECRET_KEY` 已生成并保密
- [ ] 数据库密码足够强（≥16字符，包含大小写字母、数字、特殊字符）
- [ ] Redis密码足够强
- [ ] `DEBUG` 设置为 `False`
- [ ] `ALLOWED_HOSTS` 包含实际域名
- [ ] `CORS_ALLOWED_ORIGINS` 配置正确
- [ ] AI服务API密钥已配置（如需要）
- [ ] SSL证书已配置（生产环境）
- [ ] 日志级别设置为 `INFO` 或 `WARNING`

### 安全检查

- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 所有密码已更新
- [ ] 无硬编码密钥
- [ ] 防火墙规则已配置
- [ ] 数据库仅内网可访问
- [ ] Redis仅内网可访问

---

## 常见问题

### Q1: 忘记配置SECRET_KEY会怎样？
**A:** Django无法启动，会报错"SECRET_KEY not configured"。请生成并配置。

### Q2: 数据库密码可以包含特殊字符吗？
**A:** 可以，但建议避免使用 `$`、`{`、`}` 等可能在配置文件中被解析的字符。

### Q3: 如何验证Redis连接？
**A:** 使用以下命令：
```bash
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a [REDIS_PASSWORD] ping
```

### Q4: 生产环境必须配置SSL吗？
**A:** 是的，生产环境强烈建议配置SSL/TLS，否则数据传输不安全。

### Q5: 如何查看当前生效的环境变量？
**A:** 使用以下命令：
```bash
docker-compose -f docker-compose.prod.yml config
```

---

## 参考资源

- [Django环境变量文档](https://docs.djangoproject.com/en/4.2/topics/settings/#environment-variables)
- [Docker Compose环境变量](https://docs.docker.com/compose/environment-variables/)
- [PostgreSQL环境变量](https://www.postgresql.org/docs/current/libpq-envars.html)
- [Redis配置](https://redis.io/topics/config)

---

## 变更记录

### 2026-01-27
- 初始化环境变量文档
- 添加所有配置项说明
- 添加配置检查清单
- 添加常见问题解答
