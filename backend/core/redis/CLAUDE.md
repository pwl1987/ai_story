# CLAUDE.md - Redis Pub/Sub模块 (redis)

[根目录](../../../CLAUDE.md) > [backend](../../) > [core](../) > **redis**

> 最后更新: 2026-01-26 12:08:52

---

## 模块职责

Redis Pub/Sub模块负责：
- Redis发布器（RedisStreamPublisher）
- Redis订阅器（RedisStreamSubscriber）
- 实时进度推送
- 使用Redis数据库2（独立于Celery）

---

## 入口与启动

### 主要文件

| 文件 | 职责 |
|------|------|
| [publisher.py](./publisher.py) | 发布器（Celery任务使用） |
| [subscriber.py](./subscriber.py) | 订阅器（WebSocket使用） |

---

## 对外接口

### RedisStreamPublisher

```python
class RedisStreamPublisher:
    """Redis发布器"""
    def __init__(self, project_id: str, stage_name: str)
    def publish_token(self, content: str, full_text: str)  # 发布token
    def publish_stage_update(self, status, progress, message)  # 发布阶段更新
    def publish_error(self, error: str)  # 发布错误
```

### RedisStreamSubscriber

```python
class RedisStreamSubscriber:
    """Redis订阅器"""
    def __init__(self, project_id: str, stage_name: str)
    async def subscribe(self)  # 订阅频道
    async def unsubscribe(self)  # 取消订阅
```

---

## 关键配置

```python
# config/settings/base.py
REDIS_PUBSUB_URL = 'redis://localhost:6379/2'  # 数据库2: Pub/Sub专用

# 频道命名规则
channel = f"ai_story:project:{project_id}:stage:{stage_name}"
```

---

## 测试覆盖 (Day 6更新)

- ✅ **Publisher 84%覆盖** - `test_redis_publisher.py` (14个测试) 🏆
- ✅ **Subscriber 55%覆盖** - `test_core_redis.py` (36个测试，包含subscriber测试)
- ✅ **Redis集成测试** - `test_realtime_messaging.py` (11个测试，100%通过)
- ✅ **Celery+Redis测试** - `test_celery_redis.py` (完整异步流程测试)

### 测试文件清单

```
tests/
├── test_redis_publisher.py            # 14个测试，Publisher 84%覆盖
├── test_core_redis.py                 # 36个测试，包含subscriber
└── integration/
    └── test_realtime_messaging.py     # 11个集成测试，真实Redis
```

---

## 变更记录

### 2026-01-26 12:08:52
- 初始化Redis Pub/Sub模块文档
