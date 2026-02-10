# Sub-Epic 11.3: 引擎监控与配置

**Epic:** Epic 11 - 流程和UI优化
**Sub-Epic ID:** 11.3
**状态:** 📋 规划中
**创建日期:** 2026-02-09
**优先级:** ⭐⭐⭐⭐
**预计工作量:** 1周 (4.5天)
**Story数量:** 3个

---

## 📋 文档版本历史

| 版本 | 日期 | 更新内容 | 更新人 |
|------|------|---------|--------|
| v1.0 | 2026-02-09 | Sub-Epic 11.3 完整规划文档创建 | AI Assistant |

---

## 📋 目录

- [概述](#概述)
- [业务价值](#业务价值)
- [Story 11.3.1: EngineConfig 数据模型](#story-1131-engineconfig-数据模型)
- [Story 11.3.2: 引擎健康检查](#story-1132-引擎健康检查)
- [Story 11.3.3: 引擎配置前端界面](#story-1133-引擎配置前端界面)
- [数据模型设计](#数据模型设计)
- [API设计](#api设计)
- [UI设计](#ui设计)
- [实施计划](#实施计划)
- [测试策略](#测试策略)
- [DoD检查清单](#dod检查清单)

---

## 概述

### 背景

当前AI Story系统已集成多个AI引擎:
- **LLM引擎**: Ollama (本地) / OpenAI (云端)
- **Image引擎**: ComfyUI (本地) / DALL-E (云端)
- **TTS引擎**: Edge-TTS (本地) / ElevenLabs (云端)

但存在以下痛点:

1. **引擎状态不可见** - 无法实时监控Ollama/ComfyUI/Edge-TTS是否在线
2. **Fallback机制不透明** - 用户不知道何时切换到云端备份引擎
3. **成本统计缺失** - 无法统计本地引擎节省了多少API费用
4. **健康检查缺失** - 引擎故障时无法自动切换和报警

### 目标

实现完整的引擎监控与配置系统,提供:
- ✅ 统一的引擎配置管理
- ✅ 实时健康状态监控
- ✅ 可视化Fallback机制
- ✅ 成本统计和使用分析
- ✅ 自动故障切换

### 技术栈

**后端:**
- Django REST Framework (API)
- Celery (异步健康检查)
- Redis (缓存健康状态)
- Channels (WebSocket实时推送)

**前端:**
- Vue 2.7
- daisyUI 4.12.23
- Chart.js (成本统计图表)

---

## 业务价值

### 对用户的价值

1. **系统管理员**
   - 实时掌握所有引擎状态
   - 快速发现和解决引擎故障
   - 可视化成本统计和优化建议

2. **漫剧创作者**
   - 了解当前使用的引擎
   - 查看生成进度和失败原因
   - 获得友好的错误提示

### 对项目的价值

1. **降低运营成本** - 统计本地引擎节省的费用
2. **提高系统稳定性** - 自动故障切换,减少人工干预
3. **优化用户体验** - 减少等待焦虑,提供清晰的错误信息
4. **数据驱动决策** - 根据使用统计优化引擎配置

---

## Story 11.3.1: EngineConfig 数据模型

**状态:** 📋 待开发
**优先级:** P0 (核心)
**工作量:** 1.5天
**依赖:** 无

---

### 用户故事

```
作为 系统管理员
我想要 统一配置所有AI引擎 (LLM/Image/TTS)
以便 灵活切换主引擎和备份引擎
```

---

### 验收标准 (Acceptance Criteria)

#### AC 1: 支持三种引擎类型
**Given** 引擎配置模型
**When** 创建引擎配置
**Then** 可以选择引擎类型:
  - `llm` - LLM文本生成引擎
  - `image` - 图像生成引擎
  - `tts` - 语音合成引擎

#### AC 2: 主引擎和备份引擎配置
**Given** 引擎配置模型
**When** 配置LLM引擎
**Then** 可以设置:
  - 主引擎提供商 (`primary_provider`: 'ollama')
  - 主引擎配置 (`primary_config`: JSON)
  - 备份引擎提供商 (`fallback_provider`: 'openai')
  - 备份引擎配置 (`fallback_config`: JSON)

#### AC 3: Fallback策略配置
**Given** 引擎配置模型
**When** 配置Fallback策略
**Then** 可以设置:
  - 失败阈值 (`fallback_threshold`: 失败3次后切换)
  - 超时时间 (`fallback_timeout`: 30秒超时)
  - 自动启用/禁用Fallback

#### AC 4: 引擎配置示例
```python
# LLM引擎配置示例
{
    "engine_type": "llm",
    "primary_provider": "ollama",
    "primary_config": {
        "base_url": "http://localhost:11434",
        "model": "llama2:7b",
        "temperature": 0.7,
        "max_tokens": 2000
    },
    "fallback_provider": "openai",
    "fallback_config": {
        "api_key": "sk-xxx",
        "model": "gpt-4",
        "temperature": 0.7
    },
    "fallback_threshold": 3,
    "fallback_timeout": 30
}
```

#### AC 5: Django Admin集成
**Given** Django Admin后台
**When** 访问引擎配置页面
**Then** 可以:
  - 查看所有引擎配置
  - 创建/编辑/删除引擎配置
  - 测试引擎连接
  - 导出/导入配置 (JSON格式)

---

### 任务拆分

- [ ] **Task 1: 创建EngineConfig模型** (4小时)
  - [ ] 1.1 定义模型字段 (engine_type, primary_provider, fallback_provider等)
  - [ ] 1.2 添加验证逻辑 (primary和fallback不能相同)
  - [ ] 1.3 添加方法 `get_active_provider()` 返回当前应使用的引擎
  - [ ] 1.4 添加方法 `should_fallback()` 判断是否需要切换

- [ ] **Task 2: Django Admin集成** (3小时)
  - [ ] 2.1 注册EngineConfig到Admin
  - [ ] 2.2 配置list_display显示关键信息
  - [ ] 2.3 添加"测试连接"自定义action
  - [ ] 2.4 添加导出/导入功能

- [ ] **Task 3: 数据库迁移** (1小时)
  - [ ] 3.1 生成迁移文件
  - [ ] 3.2 执行迁移
  - [ ] 3.3 创建默认引擎配置 (开发环境)

- [ ] **Task 4: 单元测试** (4小时)
  - [ ] 4.1 测试引擎配置CRUD
  - [ ] 4.2 测试get_active_provider()逻辑
  - [ ] 4.3 测试should_fallback()判断
  - [ ] 4.4 测试Admin导出/导入功能

---

### 开发者注意事项

#### 相关架构模式

- **单一职责 (SRP):** EngineConfig只负责配置存储,不包含健康检查逻辑
- **开闭原则 (OCP):** 通过JSON配置支持新引擎,无需修改模型
- **依赖倒置 (DIP):** 依赖抽象的provider标识,不依赖具体实现

#### 需要接触的源代码

**新增文件:**
- `backend/apps/engines/models.py` - 引擎配置模型
- `backend/apps/engines/admin.py` - Django Admin配置

**修改文件:**
- `backend/config/urls.py` - 添加engines app路由
- `backend/config/settings/base.py` - 注册engines app

**测试文件:**
- `backend/apps/engines/tests/test_models.py` - 模型单元测试

#### 测试标准

- **单元测试覆盖率**: >90% (模型方法)
- **集成测试**: 验证Admin CRUD流程
- **数据验证**: 测试primary和fallback不能相同

---

## Story 11.3.2: 引擎健康检查

**状态:** 📋 待开发
**优先级:** P0 (核心)
**工作量:** 1.5天
**依赖:** Story 11.3.1

---

### 用户故事

```
作为 系统管理员
我想要 实时监控所有引擎的健康状态
以便 快速发现和解决问题
```

---

### 验收标准 (Acceptance Criteria)

#### AC 1: 实时健康状态监控
**Given** 引擎健康检查服务
**When** 定期检查引擎状态
**Then** 更新引擎状态:
  - `online` - 引擎正常响应
  - `offline` - 引擎无法连接
  - `error` - 引擎响应异常

#### AC 2: 自动健康检查
**Given** Celery Beat定时任务
**When** 每5分钟执行一次
**Then** 自动检查所有引擎:
  - 发送测试请求
  - 测量响应时间
  - 更新健康状态
  - 记录失败次数

#### AC 3: 故障自动切换
**Given** 主引擎连续失败N次
**When** 失败次数达到阈值
**Then** 自动切换到备份引擎:
  - 更新当前引擎为fallback_provider
  - 发送通知给管理员
  - 记录切换事件

#### AC 4: 使用统计和成本追踪
**Given** 引擎使用记录
**When** 每次API调用
**Then** 记录统计信息:
  - 总请求数 (`total_requests`)
  - 成功次数 (`success_count`)
  - 失败次数 (`failure_count`)
  - 平均响应时间 (`avg_response_time`)
  - 实际花费 (`total_cost`)
  - 节省金额 (`saved_cost`)

#### AC 5: 通知机制
**Given** 引擎故障
**When** 检测到offline或error状态
**Then** 发送通知:
  - WebSocket实时推送到前端
  - 记录到系统日志
  - (可选) 邮件通知管理员

---

### 任务拆分

- [ ] **Task 1: 创建健康检查服务** (4小时)
  - [ ] 1.1 实现`HealthCheckService`类
  - [ ] 1.2 实现`check_engine_health()`方法
  - [ ] 1.3 实现`record_usage()`方法
  - [ ] 1.4 实现`calculate_cost()`方法

- [ ] **Task 2: Celery定时任务** (2小时)
  - [ ] 2.1 创建`engines/tasks.py`
  - [ ] 2.2 实现`periodic_health_check()`任务
  - [ ] 2.3 配置Celery Beat每5分钟执行

- [ ] **Task 3: 故障自动切换** (3小时)
  - [ ] 3.1 实现`FallbackService`类
  - [ ] 3.2 实现`should_trigger_fallback()`方法
  - [ ] 3.3 实现`switch_to_fallback()`方法
  - [ ] 3.4 记录Fallback事件日志

- [ ] **Task 4: WebSocket实时推送** (3小时)
  - [ ] 4.1 创建`engines/consumers.py`
  - [ ] 4.2 实现`EngineHealthConsumer`
  - [ ] 4.3 健康状态变化时自动推送

- [ ] **Task 5: 单元测试** (4小时)
  - [ ] 5.1 测试健康检查逻辑
  - [ ] 5.2 测试故障切换逻辑
  - [ ] 5.3 测试成本计算逻辑
  - [ ] 5.4 测试WebSocket推送

---

### 开发者注意事项

#### 相关架构模式

- **策略模式:** 不同引擎类型使用不同的健康检查策略
- **观察者模式:** 健康状态变化时通知所有订阅者
- **单一职责:** 健康检查、故障切换、通知分离

#### 需要接触的源代码

**新增文件:**
- `backend/apps/engines/services.py` - 健康检查和Fallback服务
- `backend/apps/engines/tasks.py` - Celery异步任务
- `backend/apps/engines/consumers.py` - WebSocket消费者
- `backend/apps/engines/models.py` - EngineHealthLog模型 (新增)

**修改文件:**
- `backend/config/celery.py` - 添加engines任务
- `backend/config/routing.py` - 添加engines WebSocket路由

**测试文件:**
- `backend/apps/engines/tests/test_services.py` - 服务单元测试
- `backend/apps/engines/tests/test_tasks.py` - 任务单元测试

#### 测试标准

- **单元测试覆盖率**: >85% (服务层)
- **Mock策略:** Mock引擎API调用
- **集成测试:** 验证Celery任务执行

---

## Story 11.3.3: 引擎配置前端界面

**状态:** 📋 待开发
**优先级:** P1 (重要)
**工作量:** 1.5天
**依赖:** Story 11.3.1, Story 11.3.2

---

### 用户故事

```
作为 系统管理员
我想要 在可视化面板查看和配置引擎
以便 直观掌握系统状况
```

---

### 验收标准 (Acceptance Criteria)

#### AC 1: 引擎配置表单
**Given** 引擎配置页面
**When** 创建/编辑引擎
**Then** 表单包含:
  - 引擎类型选择 (LLM/Image/TTS)
  - 主引擎提供商选择
  - 主引擎配置表单 (动态表单,根据提供商变化)
  - 备份引擎提供商选择
  - Fallback策略配置
  - [保存] [测试连接] [取消] 按钮

#### AC 2: 实时状态监控面板
**Given** 引擎监控页面
**When** 打开页面
**Then** 显示:
  - 卡片式展示每个引擎 (LLM/Image/TTS)
  - 引擎类型、提供商、状态图标 (🟢在线/🔴离线/⚠️异常)
  - 主引擎和备份引擎状态
  - 实时更新 (WebSocket推送,无需刷新)
  - [手动刷新] 按钮

#### AC 3: Fallback策略设置
**Given** 引擎配置页面
**When** 配置Fallback策略
**Then** 可以设置:
  - 失败阈值 (1-10次)
  - 超时时间 (10-120秒)
  - 自动启用/禁用Fallback
  - 显示Fallback历史记录

#### AC 4: 成本统计图表
**Given** 引擎监控页面
**When** 查看成本统计
**Then** 显示:
  - 今日/本周/本月请求数
  - 成功率统计
  - 节省金额 (相比纯云端)
  - 趋势图表 (Chart.js折线图)
  - 按引擎分类统计

#### AC 5: Fallback事件日志
**Given** 引擎监控页面
**When** 发生Fallback事件
**Then** 记录并显示:
  - 时间戳
  - 切换前引擎
  - 切换后引擎
  - 切换原因 (超时/失败/手动)
  - 影响的请求数

---

### 任务拆分

- [ ] **Task 1: 引擎监控页面布局** (3小时)
  - [ ] 1.1 创建`EngineMonitor.vue`组件
  - [ ] 1.2 实现三栏布局 (LLM/Image/TTS)
  - [ ] 1.3 添加引擎卡片组件
  - [ ] 1.4 添加状态图标和颜色

- [ ] **Task 2: 引擎配置表单** (4小时)
  - [ ] 2.1 创建`EngineConfigForm.vue`组件
  - [ ] 2.2 实现动态表单 (根据提供商类型变化)
  - [ ] 2.3 添加表单验证
  - [ ] 2.4 实现测试连接功能

- [ ] **Task 3: WebSocket实时更新** (3小时)
  - [ ] 3.1 连接WebSocket (`/ws/engines/health/`)
  - [ ] 3.2 监听健康状态更新
  - [ ] 3.3 实时更新UI状态
  - [ ] 3.4 处理断连和重连

- [ ] **Task 4: 成本统计图表** (2小时)
  - [ ] 4.1 集成Chart.js
  - [ ] 4.2 实现请求数趋势图
  - [ ] 4.3 实现成本统计图
  - [ ] 4.4 添加时间范围选择器

- [ ] **Task 5: 组件测试** (4小时)
  - [ ] 5.1 测试引擎配置表单
  - [ ] 5.2 测试WebSocket连接
  - [ ] 5.3 测试图表渲染
  - [ ] 5.4 E2E测试 (Cypress)

---

### 开发者注意事项

#### 相关架构模式

- **组件化设计:** 引擎卡片、配置表单、图表组件独立
- **响应式布局:** 支持桌面和移动端
- **实时通信:** WebSocket长连接

#### 需要接触的源代码

**新增文件:**
- `frontend/src/views/engines/EngineMonitor.vue` - 监控页面
- `frontend/src/components/engines/EngineCard.vue` - 引擎卡片组件
- `frontend/src/components/engines/EngineConfigForm.vue` - 配置表单组件
- `frontend/src/components/engines/CostChart.vue` - 成本图表组件

**修改文件:**
- `frontend/src/router/index.js` - 添加引擎管理路由
- `frontend/src/store/modules/engines.js` - Vuex状态管理

**测试文件:**
- `frontend/tests/unit/engines/EngineCard.spec.js` - 组件单元测试
- `frontend/tests/e2e/engines.spec.js` - E2E测试

#### UI/UX规范

- **颜色规范:**
  - 🟢 在线: `success` (green)
  - 🔴 离线: `error` (red)
  - ⚠️ 异常: `warning` (yellow)

- **卡片样式:** 使用daisyUI Card组件
- **表单样式:** 使用daisyUI Form组件
- **图表样式:** Chart.js自定义配色

---

## 数据模型设计

### EngineConfig 模型

```python
from django.db import models
from django.core.exceptions import ValidationError

class EngineConfig(models.Model):
    """引擎配置模型"""

    ENGINE_TYPES = [
        ('llm', 'LLM文本生成'),
        ('image', '图像生成'),
        ('tts', '语音合成'),
    ]

    # 基础配置
    engine_type = models.CharField(
        max_length=10,
        choices=ENGINE_TYPES,
        unique=True,
        help_text="引擎类型 (每种类型只能有一个配置)"
    )

    # 主引擎配置
    primary_provider = models.CharField(
        max_length=50,
        help_text="主引擎提供商 (如: ollama, openai)"
    )
    primary_config = models.JSONField(
        default=dict,
        help_text="主引擎配置参数"
    )

    # 备份引擎配置
    fallback_provider = models.CharField(
        max_length=50,
        blank=True,
        help_text="备份引擎提供商"
    )
    fallback_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="备份引擎配置参数"
    )

    # Fallback策略
    fallback_threshold = models.IntegerField(
        default=3,
        help_text="失败多少次后切换到备份引擎"
    )
    fallback_timeout = models.IntegerField(
        default=30,
        help_text="超时时间 (秒)"
    )
    auto_fallback = models.BooleanField(
        default=True,
        help_text="是否自动启用Fallback"
    )

    # 状态管理
    is_active = models.BooleanField(default=True)
    current_provider = models.CharField(
        max_length=50,
        blank=True,
        help_text="当前使用的引擎"
    )
    health_status = models.CharField(
        max_length=20,
        default='unknown',
        choices=[
            ('online', '在线'),
            ('offline', '离线'),
            ('error', '异常'),
            ('unknown', '未知')
        ]
    )
    last_health_check = models.DateTimeField(auto_now=True)

    # 统计信息
    total_requests = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)

    # 成本追踪
    total_cost = models.FloatField(default=0.0)  # 实际花费 (美元)
    saved_cost = models.FloatField(default=0.0)  # 节省金额 (美元)

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "引擎配置"
        verbose_name_plural = "引擎配置"
        ordering = ['engine_type']

    def __str__(self):
        return f"{self.get_engine_type_display()} - {self.primary_provider}"

    def clean(self):
        """验证配置"""
        # 主引擎和备份引擎不能相同
        if self.primary_provider == self.fallback_provider:
            raise ValidationError({
                'fallback_provider': '备份引擎不能与主引擎相同'
            })

        # 验证配置JSON不为空
        if not self.primary_config:
            raise ValidationError({
                'primary_config': '主引擎配置不能为空'
            })

    def get_active_provider(self):
        """获取当前应使用的引擎"""
        if not self.auto_fallback:
            return self.primary_provider

        # 如果当前引擎在线,继续使用
        if self.health_status == 'online' and self.current_provider:
            return self.current_provider

        # 否则使用主引擎
        return self.primary_provider

    def should_fallback(self):
        """判断是否需要切换到备份引擎"""
        if not self.auto_fallback:
            return False

        if not self.fallback_provider:
            return False

        # 连续失败次数达到阈值
        recent_failures = self.failure_count % self.fallback_threshold
        return recent_failures >= self.fallback_threshold

    def calculate_success_rate(self):
        """计算成功率"""
        if self.total_requests == 0:
            return 0.0
        return (self.success_count / self.total_requests) * 100
```

### EngineHealthLog 模型

```python
class EngineHealthLog(models.Model):
    """引擎健康检查日志"""

    engine = models.ForeignKey(
        EngineConfig,
        on_delete=models.CASCADE,
        related_name='health_logs'
    )

    # 检查结果
    status = models.CharField(
        max_length=20,
        choices=[
            ('online', '在线'),
            ('offline', '离线'),
            ('error', '异常'),
        ]
    )
    response_time = models.FloatField(
        null=True,
        blank=True,
        help_text="响应时间 (毫秒)"
    )

    # 错误信息
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=50, blank=True)

    # 时间戳
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "引擎健康日志"
        verbose_name_plural = "引擎健康日志"
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['engine', '-checked_at']),
        ]

    def __str__(self):
        return f"{self.engine.engine_type} - {self.status} @ {self.checked_at}"
```

### EngineUsageLog 模型

```python
class EngineUsageLog(models.Model):
    """引擎使用日志"""

    engine = models.ForeignKey(
        EngineConfig,
        on_delete=models.CASCADE,
        related_name='usage_logs'
    )

    # 请求信息
    provider = models.CharField(max_length=50)  # 实际使用的提供商
    request_type = models.CharField(max_length=20)  # 'llm'/'image'/'tts'
    success = models.BooleanField(default=True)

    # 性能指标
    response_time = models.FloatField(help_text="响应时间 (毫秒)")
    token_count = models.IntegerField(null=True, blank=True)

    # 成本信息
    cost = models.FloatField(default=0.0, help_text="实际花费 (美元)")
    saved_cost = models.FloatField(default=0.0, help_text="节省金额 (美元)")

    # 关联信息
    project_id = models.UUIDField(null=True, blank=True)
    shot_id = models.UUIDField(null=True, blank=True)

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "引擎使用日志"
        verbose_name_plural = "引擎使用日志"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['engine', '-created_at']),
            models.Index(fields=['success', '-created_at']),
        ]

    def __str__(self):
        return f"{self.engine.engine_type} - {self.provider} - {'✓' if self.success else '✗'}"
```

### FallbackEventLog 模型

```python
class FallbackEventLog(models.Model):
    """Fallback事件日志"""

    engine = models.ForeignKey(
        EngineConfig,
        on_delete=models.CASCADE,
        related_name='fallback_logs'
    )

    # 切换信息
    from_provider = models.CharField(max_length=50)
    to_provider = models.CharField(max_length=50)

    # 切换原因
    reason = models.CharField(
        max_length=20,
        choices=[
            ('timeout', '超时'),
            ('failure', '连续失败'),
            ('manual', '手动切换'),
            ('error', '引擎异常'),
        ]
    )
    reason_detail = models.TextField(blank=True)

    # 影响范围
    affected_requests = models.IntegerField(default=0)

    # 时间戳
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fallback事件日志"
        verbose_name_plural = "Fallback事件日志"
        ordering = ['-occurred_at']

    def __str__(self):
        return f"{self.engine.engine_type}: {self.from_provider} → {self.to_provider}"
```

---

## API设计

### 1. 引擎配置API

#### GET /api/v1/engines/config/
**描述:** 获取所有引擎配置列表

**响应:**
```json
{
    "count": 3,
    "results": [
        {
            "id": "uuid",
            "engine_type": "llm",
            "primary_provider": "ollama",
            "fallback_provider": "openai",
            "health_status": "online",
            "success_rate": 98.5,
            "total_requests": 1234,
            "saved_cost": 24.50
        }
    ]
}
```

#### POST /api/v1/engines/config/
**描述:** 创建引擎配置

**请求体:**
```json
{
    "engine_type": "llm",
    "primary_provider": "ollama",
    "primary_config": {
        "base_url": "http://localhost:11434",
        "model": "llama2:7b"
    },
    "fallback_provider": "openai",
    "fallback_config": {
        "api_key": "sk-xxx",
        "model": "gpt-4"
    },
    "fallback_threshold": 3,
    "fallback_timeout": 30
}
```

#### PUT /api/v1/engines/config/{id}/
**描述:** 更新引擎配置

#### DELETE /api/v1/engines/config/{id}/
**描述:** 删除引擎配置

#### POST /api/v1/engines/config/{id}/test/
**描述:** 测试引擎连接

**响应:**
```json
{
    "success": true,
    "provider": "ollama",
    "response_time": 123.5,
    "message": "连接成功"
}
```

### 2. 健康状态API

#### GET /api/v1/engines/health/
**描述:** 获取所有引擎健康状态

**响应:**
```json
{
    "llm": {
        "status": "online",
        "provider": "ollama",
        "response_time": 1.2,
        "last_check": "2026-02-09T10:30:00Z"
    },
    "image": {
        "status": "online",
        "provider": "comfyui",
        "response_time": 15.3,
        "last_check": "2026-02-09T10:30:00Z"
    },
    "tts": {
        "status": "online",
        "provider": "edge",
        "response_time": 0.3,
        "last_check": "2026-02-09T10:30:00Z"
    }
}
```

#### POST /api/v1/engines/health/check/
**描述:** 手动触发健康检查

**响应:**
```json
{
    "success": true,
    "message": "健康检查已启动"
}
```

### 3. 统计数据API

#### GET /api/v1/engines/stats/
**描述:** 获取引擎统计数据

**查询参数:**
- `date_range`: today/week/month
- `engine_type`: llm/image/tts (可选)

**响应:**
```json
{
    "total_requests": 15234,
    "success_rate": 97.8,
    "total_cost": 12.50,
    "saved_cost": 298.12,
    "by_engine": {
        "llm": {
            "requests": 5234,
            "cost": 5.20,
            "saved": 124.50
        },
        "image": {
            "requests": 456,
            "cost": 7.30,
            "saved": 18.24
        },
        "tts": {
            "requests": 9544,
            "cost": 0.00,
            "saved": 155.38
        }
    },
    "timeline": [
        {
            "date": "2026-02-01",
            "requests": 1234,
            "cost": 1.20
        }
    ]
}
```

### 4. Fallback事件API

#### GET /api/v1/engines/fallback-logs/
**描述:** 获取Fallback事件日志

**查询参数:**
- `limit`: 返回数量 (默认20)
- `engine_type`: 引擎类型 (可选)

**响应:**
```json
{
    "count": 10,
    "results": [
        {
            "id": "uuid",
            "engine_type": "llm",
            "from_provider": "ollama",
            "to_provider": "openai",
            "reason": "timeout",
            "reason_detail": "连续3次超时",
            "affected_requests": 5,
            "occurred_at": "2026-02-09T10:15:00Z"
        }
    ]
}
```

### 5. WebSocket API

#### 连接: ws://localhost:8000/ws/engines/health/
**描述:** 实时接收健康状态更新

**消息格式:**
```json
{
    "type": "health_update",
    "data": {
        "engine_type": "llm",
        "status": "offline",
        "provider": "ollama",
        "timestamp": "2026-02-09T10:30:00Z"
    }
}
```

---

## UI设计

### 引擎监控主页面

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚙️  引擎监控与配置                                  [刷新] [配置] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 📊 总体统计                                                   │ │
│ │ ├─ 今日请求数: 1,234                                         │ │
│ │ ├─ 成功率: 97.8%                                             │ │
│ │ ├─ 实际花费: $12.50                                          │ │
│ │ └─ 节省金额: $298.12 💰                                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🤖 LLM 引擎                                                  │ │
│ │ ├─ 主引擎: Ollama (llama2:7b)                               │ │
│ │ │   状态: 🟢 在线 | 响应: 1.2s | 成功率: 98.5%              │ │
│ │ ├─ 备份引擎: OpenAI (gpt-4)                                 │ │
│ │ │   状态: 🟢 在线 | 响应: 0.8s                             │ │
│ │ ├─ 今日请求数: 5234 | 节省: $124.50                        │ │
│ │ ├─ [查看详情] [测试连接] [编辑配置]                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🎨 Image 引擎                                                │ │
│ │ ├─ 主引擎: ComfyUI (SDXL)                                   │ │
│ │ │   状态: 🟢 在线 | 响应: 15.3s | 成功率: 92.1%             │ │
│ │ ├─ 备份引擎: DALL-E 3                                       │ │
│ │ │   状态: 🟢 在线                                           │ │
│ │ ├─ 今日请求数: 456 | 节省: $18.24                          │ │
│ │ └─ [查看详情] [测试连接] [编辑配置]                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🔊 TTS 引擎                                                  │ │
│ │ ├─ 主引擎: Edge-TTS (免费)                                  │ │
│ │ │   状态: 🟢 在线 | 响应: 0.3s | 成功率: 99.9%              │ │
│ │ ├─ 备份引擎: ElevenLabs                                     │ │
│ │ │   状态: 🟡 配置中                                        │ │
│ │ ├─ 今日请求数: 9544 | 节省: $155.38                        │ │
│ │ └─ [查看详情] [测试连接] [编辑配置]                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 📈 成本统计                                                  │ │
│ │ ├─ 时间范围: [今日▼] [本周] [本月] [自定义]                 │ │
│ │ └─ [图表区域: 折线图显示请求趋势和成本趋势]                 │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 引擎配置表单

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚙️  引擎配置: LLM                                    [保存] [取消] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 引擎类型: LLM文本生成                                           │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🤖 主引擎配置                                                │ │
│ │ ├─ 提供商: [Ollama ▼] (OpenAI, Anthropic, Ollama...)      │ │
│ │ ├─ API地址: [http://localhost:11434        ]                │ │
│ │ ├─ 模型名称: [llama2:7b                     ]                │ │
│ │ ├─ 温度: [====|====] 0.7                                    │ │
│ │ ├─ 最大Token: [2000                      ]                  │ │
│ │ └─ [测试连接]                                                │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🔄 Fallback策略                                              │ │
│ │ ├─ [✓] 启用自动Fallback                                     │ │
│ │ ├─ 备份引擎: [OpenAI ▼]                                     │ │
│ │ ├─ API密钥: [sk-xxx                          ]              │ │
│ │ ├─ 模型名称: [gpt-4                          ]              │ │
│ │ ├─ 失败阈值: [3] 次后切换                                   │ │
│ │ ├─ 超时时间: [30] 秒                                        │ │
│ │ └─ [测试连接]                                                │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ [保存配置] [测试所有引擎] [取消]                                │
└─────────────────────────────────────────────────────────────────┘
```

### Fallback事件日志

```
┌─────────────────────────────────────────────────────────────────┐
│ 📜 Fallback事件日志                                    [导出]    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 时间              引擎    切换路径              原因    影响     │
│ ──────────────────────────────────────────────────────────────│
│ 2026-02-09 10:15  LLM     Ollama → OpenAI     超时    5次      │
│ 2026-02-09 09:30  Image   ComfyUI → DALL-E    失败    12次     │
│ 2026-02-09 08:45  LLM     OpenAI → Ollama     手动    -        │
│ 2026-02-08 23:20  TTS     Edge → ElevenLabs   异常    3次      │
│                                                                 │
│ [加载更多...]                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 实施计划

### 时间线 (1周)

```
Day 1-2: Story 11.3.1 - EngineConfig 数据模型
  ├─ Day 1: 模型设计 + Django Admin
  └─ Day 2: 单元测试 + 集成测试

Day 3-4: Story 11.3.2 - 引擎健康检查
  ├─ Day 3: 健康检查服务 + Celery任务
  └─ Day 4: Fallback服务 + WebSocket推送

Day 5: Story 11.3.3 - 引擎配置前端界面
  ├─ 上午: 监控页面布局 + 引擎卡片
  ├─ 下午: 配置表单 + 实时更新

Day 6-7: 集成测试 + Bug修复
  ├─ Day 6: 端到端测试 + 性能优化
  └─ Day 7: Bug修复 + 文档更新
```

### 并行执行策略

```
并行组1 (后端):
  - Story 11.3.1 (数据模型)
  - Story 11.3.2 (健康检查服务)

并行组2 (前端):
  - Story 11.3.3 (监控界面)
  - 可在Day 3开始,等待后端API完成
```

---

## 测试策略

### 单元测试

**后端:**
- `test_models.py` - 测试EngineConfig模型方法
  - `test_get_active_provider()`
  - `test_should_fallback()`
  - `test_calculate_success_rate()`

- `test_services.py` - 测试健康检查和Fallback服务
  - `test_check_engine_health()`
  - `test_should_trigger_fallback()`
  - `test_switch_to_fallback()`

**前端:**
- `EngineCard.spec.js` - 测试引擎卡片组件
- `EngineConfigForm.spec.js` - 测试配置表单
- `CostChart.spec.js` - 测试图表组件

### 集成测试

**后端:**
- 测试Celery任务执行
- 测试WebSocket连接和推送
- 测试API端点

**前端:**
- 测试WebSocket实时更新
- 测试表单提交流程
- 测试图表数据渲染

### E2E测试 (Cypress)

```
场景1: 创建引擎配置
  Given 访问引擎配置页面
  When 填写表单并保存
  Then 配置成功创建

场景2: 监控引擎状态
  Given 打开引擎监控页面
  When 引擎状态变化
  Then 页面实时更新

场景3: 测试引擎连接
  Given 点击"测试连接"按钮
  When 测试完成
  Then 显示测试结果

场景4: 查看成本统计
  Given 打开成本统计页面
  When 选择时间范围
  Then 显示对应统计数据
```

---

## DoD检查清单

### Story 11.3.1: EngineConfig 数据模型

- [ ] EngineConfig模型实现完整
- [ ] 支持三种引擎类型 (llm/image/tts)
- [ ] 主引擎和备份引擎配置正常工作
- [ ] Fallback策略配置正常工作
- [ ] Django Admin集成完成
- [ ] 导出/导入功能正常
- [ ] 单元测试覆盖率 >90%
- [ ] 集成测试通过

### Story 11.3.2: 引擎健康检查

- [ ] 健康检查服务实现完整
- [ ] Celery定时任务正常运行 (每5分钟)
- [ ] 实时健康状态监控正常工作
- [ ] 故障自动切换逻辑正确
- [ ] WebSocket实时推送正常
- [ ] 使用统计和成本追踪正常
- [ ] 通知机制正常工作
- [ ] 单元测试覆盖率 >85%

### Story 11.3.3: 引擎配置前端界面

- [ ] 引擎监控页面布局完成
- [ ] 引擎卡片组件正常工作
- [ ] 配置表单功能完整
- [ ] WebSocket实时更新正常
- [ ] 成本统计图表正常显示
- [ ] Fallback事件日志正常显示
- [ ] 响应式布局支持移动端
- [ ] E2E测试通过

### 总体验收

- [ ] 所有3个Story完成
- [ ] 代码质量检查通过 (Ruff + Pre-commit)
- [ ] 文档更新完成
- [ ] 性能测试通过 (响应时间 <500ms)
- [ ] 安全测试通过 (API密钥加密存储)
- [ ] 用户验收测试通过

---

## 风险与缓解

### 风险1: WebSocket连接不稳定

**影响:** 实时更新失败
**缓解措施:**
- 实现断线重连机制
- 添加心跳检测
- 降级为轮询模式

### 风险2: 健康检查误报

**影响:** 不必要的Fallback切换
**缓解措施:**
- 连续N次失败才切换
- 添加手动确认机制
- 记录详细日志供排查

### 风险3: 成本计算不准确

**影响:** 统计数据失真
**缓解措施:**
- 使用官方API定价
- 定期校准计算逻辑
- 提供手动修正功能

### 风险4: Celery任务堆积

**影响:** 健康检查延迟
**缓解措施:**
- 使用专用队列
- 监控任务执行时间
- 添加告警机制

---

## 参考资料

- **设计文档:** [docs/manhua-production-system-v3.md](../../docs/manhua-production-system-v3.md)
- **Epic 11规划:** [_bmad-output/planning-artifacts/epic-11-planning-v3.md](../planning-artifacts/epic-11-planning-v3.md)
- **现有模型:** [backend/apps/models/models.py](../../backend/apps/models/models.py)
- **代理管理系统:** [_bmad-output/implementation-artifacts/9-1-proxy-config-model.md](../implementation-artifacts/9-1-proxy-config-model.md)

---

**Sub-Epic状态:** ready-for-dev
**预计开始日期:** 2026-02-10
**预计完成日期:** 2026-02-16
**下一个Sub-Epic:** Sub-Epic 11.4 - 可视化进度系统
