---
stepsCompleted: [1, 2]
inputDocuments:
  - /home/code/ai_story/_bmad-output/planning-artifacts/prd-proxy-management.md
  - /home/code/ai_story/docs/index.md
  - /home/code/ai_story/CLAUDE.md
workflowType: 'architecture'
project_name: 'ai_story'
user_name: 'Root'
date: '2026-01-30'
classification:
  projectType: '系统增强功能'
  domain: 'DevOps/基础设施'
  complexity: '中等'
  projectContext: 'brownfield'
  focus: '代理配置与管理系统'
---

# Architecture Decision Document - 代理管理系统

**Author:** Root
**Date:** 2026-01-30
**Project Type:** 系统增强功能 (Brownfield)
**Focus:** 代理配置与管理系统

---

## Executive Summary

本文档定义AI Story生成系统代理管理功能的技术架构设计。该功能为现有系统添加代理配置和管理能力，支持通过HTTP/HTTPS/SOCKS5代理调用外部AI API。

**架构原则:**
- SOLID原则：单一职责、开闭原则、依赖倒置
- 策略模式：代理提供者可插拔
- 责任链模式：自动降级策略
- 最小惊讶原则：保持向后兼容

---

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

基于PRD的7个故事化用户旅程，系统需要提供以下核心功能：

1. **代理配置管理（F1-F5）**
   - Django Admin完整CRUD界面
   - 多协议支持（HTTP/HTTPS/SOCKS5）
   - 密码Fernet加密存储
   - 代理测试连接功能
   - 依赖检查与批量操作

2. **代理监控与运维（F3-F5）**
   - Celery Beat定时健康检查（5分钟间隔）
   - 使用日志多维度筛选（时间、代理、AI提供商、状态）
   - 统计摘要（成功率、平均响应时间）
   - 健康状态可视化

3. **AI客户端集成（F6-F7）**
   - 与`core/ai_client/`无缝集成
   - 策略模式实现代理提供者（NoProxy、SingleProxy、RoundRobinProxy）
   - 自动降级策略（代理失败→直连）
   - 降级事件记录到日志

4. **前端集成（轻量级）**
   - 项目创建页面添加代理选择器
   - 只读API：`/api/v1/proxy/select/`
   - 测试连接按钮

**Non-Functional Requirements:**

**安全性（架构驱动）:**
- 密码加密解密一致性：100%
- Django Admin权限：IsAdminUser
- API权限：管理员CRUD，普通用户只读
- 审计日志：所有CRUD操作记录

**性能（明确指标）:**
- 代理测试连接：< 3秒
- AI调用额外延迟：< 100ms（相比直连）
- 并发支持：100个并发请求
- 健康检查任务内存：< 50MB

**可靠性（关键）:**
- 自动降级成功率：100%
- 健康检查任务执行成功率：> 99%
- 密码加密算法：Fernet (AES-128)
- 向后兼容：无代理时行为完全一致

**可维护性（质量门禁）:**
- 单元测试覆盖率：> 80%
- 集成测试覆盖：核心路径100%
- SOLID原则：单一职责、开闭原则、依赖倒置
- 代码规范：PEP8合规

### Scale & Complexity

- **Primary domain**: 后端服务（Django + DRF）
- **Complexity level**: 中等
- **Estimated architectural components**: 6个
  1. `apps/proxy/` - 新建Django App
  2. `core/ai_client/` - 修改，添加代理支持
  3. `apps/projects/` - 修改，添加proxy_id外键
  4. Celery Beat定时任务
  5. Django Admin配置
  6. 前端代理选择器（小修改）

### Technical Constraints & Dependencies

**外部依赖:**
- `cryptography` - Fernet对称加密
- `httpx` - 异步HTTP客户端（已集成，需扩展代理支持）
- `httpx[socks]` - SOCKS5协议支持（V2）
- Celery Beat - 定时任务调度器（已有）

**内部依赖:**
- `core/ai_client/base.py` - AI客户端抽象基类，需添加proxy_id参数
- `apps/projects/models.py` - Project模型，需添加proxy_id外键
- Redis - 5个数据库分离（已有）

**集成点:**
- AI客户端异步任务（Celery）中的代理使用
- Pipeline工作流中的AI调用通过代理
- Django Admin与前端的数据同步（通过API）

### Cross-Cutting Concerns Identified

**安全性（贯穿所有层）:**
- **数据层**: ProxyConfig.password_encrypted字段（Fernet加密）
- **服务层**: ProxyManager权限检查
- **视图层**: DRF权限类（IsAdminUser for CRUD, IsAuthenticated for read-only）
- **日志层**: 日志中不得记录明文密码

**可观测性（贯穿所有组件）:**
- **ProxyUsageLog**: 记录所有代理调用（成功/失败、响应时间、降级事件）
- **健康检查**: Celery Beat任务记录执行状态
- **Django Admin**: 操作日志（内置）

**可靠性（端到端）:**
- **自动降级**: AI客户端try-except捕获异常，降级到直连
- **健康恢复**: Celery Beat检测代理恢复，更新is_healthy字段
- **向后兼容**: 无proxy_id时，ProxyManager返回NoProxyProvider

**测试策略（分层次）:**
- **单元测试**: ProxyConfig模型、ProxyManager策略、加密解密
- **集成测试**: 代理配置→AI调用成功、代理失败→自动降级
- **E2E测试**: Django Admin完整流程、前端代理选择器

---

## System Architecture

### High-Level Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend Layer"
        VueApp[Vue 2.7.14 App]
        ProxySelector[代理选择器]
        TestButton[测试连接按钮]
    end

    subgraph "API Layer (Django REST Framework)"
        AdminAPI[Django Admin<br/>/admin/proxy/]
        PublicAPI[Public API<br/>/api/v1/proxy/select/]
        TestAPI[Test Connection API<br/>/api/v1/proxy/{id}/test_connection/]
    end

    subgraph "Business Logic Layer"
        ProxyService[ProxyManager<br/>代理管理器]
        ProxyProvider[ProxyProvider<br/>策略模式实现]
        ProxyHealth[HealthChecker<br/>健康检查服务]
    end

    subgraph "Data Layer"
        ProxyConfig[(ProxyConfig<br/>代理配置表)]
        ProxyUsageLog[(ProxyUsageLog<br/>使用日志表)]
        Project[Project表<br/>扩展proxy_id]
        Encryption[Fernet加密<br/>密码保护]
    end

    subgraph "Integration Layer"
        AIClient[core/ai_client/<br/>BaseAIClient]
        Pipeline[Pipeline工作流<br/>任务执行]
        Celery[Celery Beat<br/>定时任务]
    end

    subgraph "External Services"
        OpenAI[OpenAI API]
        Claude[Claude API]
        ProxyServer[代理服务器<br/>HTTP/HTTPS/SOCKS5]
    end

    VueApp -->|选择代理| ProxySelector
    ProxySelector -->|GET /api/v1/proxy/select/| PublicAPI
    TestButton -->|POST test_connection| TestAPI

    AdminAPI -->|CRUD| ProxyService
    ProxyService -->|get_provider()| ProxyProvider
    ProxyProvider -->|读取配置| ProxyConfig
    ProxyConfig -->|加密/解密| Encryption

    TestAPI -->|测试连接| ProxyService
    ProxyService -->|httpx请求| ProxyServer

    AIClient -->|使用代理| ProxyProvider
    Pipeline -->|AI调用| AIClient
    AIClient -->|API请求| OpenAI
    AIClient -->|API请求| Claude

    Celery -->|定时执行| ProxyHealth
    ProxyHealth -->|更新状态| ProxyConfig

    AIClient -->|记录日志| ProxyUsageLog

    style ProxyConfig fill:#e1f5ff
    style ProxyProvider fill:#fff3e0
    style AIClient fill:#f3e5f5
    style Encryption fill:#ffebee
```

### Component Interaction

#### 1. Django Admin管理界面交互流程

```mermaid
sequenceDiagram
    participant Admin as 管理员
    participant DjangoAdmin as Django Admin
    participant ProxyService as ProxyManager
    participant ProxyConfig as ProxyConfig Model
    participant Encryption as Fernet Encryption
    participant ProxyServer as 代理服务器

    Admin->>DjangoAdmin: 1. 打开代理列表
    DjangoAdmin->>ProxyConfig: 2. 查询所有代理配置
    ProxyConfig-->>DjangoAdmin: 3. 返回代理列表

    Admin->>DjangoAdmin: 4. 点击"Add Proxy Config"
    DjangoAdmin->>Admin: 5. 显示表单（名称、协议、主机、端口、用户名、密码）

    Admin->>DjangoAdmin: 6. 填写表单并提交
    DjangoAdmin->>Encryption: 7. 加密密码
    Encryption-->>DjangoAdmin: 8. 返回密文
    DjangoAdmin->>ProxyConfig: 9. 保存ProxyConfig（password_encrypted）

    Admin->>DjangoAdmin: 10. 点击"Test Connection"
    DjangoAdmin->>ProxyService: 11. test_connection(proxy_id)
    ProxyService->>ProxyConfig: 12. 获取代理配置
    ProxyConfig-->>ProxyService: 13. 返回配置（host, port, protocol）
    ProxyService->>Encryption: 14. 解密密码
    Encryption-->>ProxyService: 15. 返回明文密码
    ProxyService->>ProxyServer: 16. httpx测试请求（GET https://httpbin.org/ip）
    ProxyServer-->>ProxyService: 17. 返回响应（包含代理IP）
    ProxyService-->>DjangoAdmin: 18. 显示测试结果
    DjangoAdmin-->>Admin: 19. "✓ 连接成功！IP: 203.0.113.42"
```

#### 2. AI客户端代理使用流程（含自动降级）

```mermaid
sequenceDiagram
    participant Task as Celery Task
    participant AIClient as BaseAIClient
    participant ProxyProvider as ProxyProvider
    participant ProxyConfig as ProxyConfig Model
    participant ProxyUsageLog as UsageLog
    participant OpenAI as OpenAI API
    participant DirectAPI as 直连API

    Task->>AIClient: 1. 调用AI API（传递proxy_id）
    AIClient->>ProxyProvider: 2. get_proxy(proxy_id)
    ProxyProvider->>ProxyConfig: 3. 查询代理配置
    ProxyConfig-->>ProxyProvider: 4. 返回配置（is_active, is_healthy）

    alt 代理可用且健康
        ProxyProvider-->>AIClient: 5a. 返回代理URL
        AIClient->>OpenAI: 6a. 通过代理发送请求
        OpenAI-->>AIClient: 7a. 返回响应
        AIClient->>ProxyUsageLog: 8a. 记录日志（success=true, 使用代理）
    else 代理不可用或不健康
        ProxyProvider-->>AIClient: 5b. 返回None
        AIClient->>DirectAPI: 6b. 直连发送请求（降级）
        DirectAPI-->>AIClient: 7b. 返回响应
        AIClient->>ProxyUsageLog: 8b. 记录日志（success=true, 直连降级）
    end

    AIClient-->>Task: 9. 返回AI响应

    Note over AIClient,ProxyUsageLog: 所有操作都记录到日志中
```

#### 3. 健康检查流程（Celery Beat）

```mermaid
sequenceDiagram
    participant Beat as Celery Beat
    participant HealthTask as check_proxy_health
    participant ProxyConfig as ProxyConfig Model
    participant ProxyServer as 代理服务器
    participant UsageLog as ProxyUsageLog

    loop 每5分钟执行一次
        Beat->>HealthTask: 1. 触发健康检查任务
        HealthTask->>ProxyConfig: 2. 查询所有is_active=True的代理
        ProxyConfig-->>HealthTask: 3. 返回代理列表

        par 遍历每个代理
            HealthTask->>ProxyServer: 4. 测试连接（GET https://httpbin.org/ip）
            alt 代理响应成功
                ProxyServer-->>HealthTask: 5a. 返回200 OK
                HealthTask->>ProxyConfig: 6a. 更新is_healthy=True
                HealthTask->>UsageLog: 7a. 记录健康检查成功
            else 代理超时或失败
                ProxyServer-->>HealthTask: 5b. 返回错误
                HealthTask->>ProxyConfig: 6b. 更新is_healthy=False
                HealthTask->>UsageLog: 7b. 记录健康检查失败
            end
        end
    end
```

---

## Data Model Design

### Entity Relationship Diagram

```mermaid
erDiagram
    PROXYCONFIG ||--o{ PROXYUSAGELOG : "records"
    PROJECT ||--o{ PROXYCONFIG : "uses"

    PROXYCONFIG {
        int id PK
        string name "代理名称"
        string protocol "HTTP/HTTPS/SOCKS5"
        string host "代理主机"
        int port "端口"
        string username "用户名(可选)"
        string password_encrypted "加密密码"
        bool is_active "是否启用"
        bool is_healthy "健康状态"
        int priority "优先级"
        string description "描述"
        datetime created_at "创建时间"
        datetime updated_at "更新时间"
        datetime last_used_at "最后使用时间"
    }

    PROXYUSAGELOG {
        int id PK
        int proxy_id FK
        string ai_provider "AI提供商"
        string endpoint "API端点"
        int response_time_ms "响应时间ms"
        bool success "是否成功"
        string error_message "错误信息"
        datetime timestamp "时间戳"
    }

    PROJECT {
        int id PK
        string name "项目名称"
        int proxy_id FK "代理ID(可选)"
        ... "其他字段"
    }
```

### Database Schema

#### apps/proxy/models.py

```python
from django.db import models
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
from django.conf import settings

class ProxyProtocol(models.TextChoices):
    HTTP = 'http', 'HTTP'
    HTTPS = 'https', 'HTTPS'
    SOCKS5 = 'socks5', 'SOCKS5'

class ProxyConfig(models.Model):
    """
    代理配置聚合根
    单一职责：管理单个代理服务器的配置信息
    """
    # 基础配置
    name = models.CharField(max_length=100, unique=True, verbose_name='代理名称')
    protocol = models.CharField(
        max_length=10,
        choices=ProxyProtocol.choices,
        verbose_name='协议类型'
    )
    host = models.CharField(max_length=255, verbose_name='代理主机')
    port = models.PositiveIntegerField(verbose_name='端口')

    # 认证信息（加密存储）
    username = models.CharField(max_length=100, blank=True, null=True)
    password_encrypted = models.TextField(blank=True, null=True)

    # 状态管理
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    is_healthy = models.BooleanField(default=True, verbose_name='健康状态')

    # 元数据
    priority = models.PositiveIntegerField(default=0, verbose_name='优先级')
    description = models.TextField(blank=True, verbose_name='描述')

    # 审计字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-priority', 'name']
        verbose_name = '代理配置'
        verbose_name_plural = '代理配置'
        indexes = [
            models.Index(fields=['is_active', 'is_healthy']),
            models.Index(fields=['-last_used_at']),
        ]

    def clean(self):
        """验证逻辑"""
        if not 1 <= self.port <= 65535:
            raise ValidationError({'port': '端口号必须在1-65535之间'})

    def get_proxy_url(self):
        """构建httpx代理URL"""
        if self.username and self.password_encrypted:
            password = self.decrypt_password()
            return f"{self.protocol}://{self.username}:{password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"

    def encrypt_password(self, password):
        """密码加密"""
        f = Fernet(settings.PROXY_ENCRYPTION_KEY)
        return f.encrypt(password.encode()).decode()

    def decrypt_password(self):
        """密码解密"""
        if not self.password_encrypted:
            return ''
        f = Fernet(settings.PROXY_ENCRYPTION_KEY)
        return f.decrypt(self.password_encrypted.encode()).decode()

class ProxyUsageLog(models.Model):
    """
    代理使用日志（值对象）
    单一职责：记录代理使用统计
    """
    proxy = models.ForeignKey(
        ProxyConfig,
        on_delete=models.CASCADE,
        related_name='usage_logs'
    )

    # 使用信息
    ai_provider = models.CharField(max_length=50)  # 'openai', 'claude', etc.
    endpoint = models.CharField(max_length=255)

    # 性能指标
    response_time_ms = models.PositiveIntegerField()
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    # 时间戳
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['proxy', '-timestamp']),
            models.Index(fields=['ai_provider', '-timestamp']),
            models.Index(fields=['success', '-timestamp']),
        ]
        verbose_name = '代理使用日志'
        verbose_name_plural = '代理使用日志'
```

#### apps/projects/models.py (修改)

```python
# 在现有Project模型中添加
class Project(models.Model):
    # ... 现有字段 ...

    # 新增：代理配置外键
    proxy_config = models.ForeignKey(
        'proxy.ProxyConfig',
        on_delete=models.SET_NULL,  # 代理删除时设为NULL，不删除项目
        null=True,
        blank=True,
        verbose_name='代理配置',
        related_name='projects'
    )

    class Meta:
        # ... 现有Meta ...
        verbose_name = '项目'
        verbose_name_plural = '项目'
```

---

## Service Layer Design

### ProxyManager (服务层门面)

```python
# apps/proxy/services.py

from abc import ABC, abstractmethod
from typing import Optional
from .models import ProxyConfig, ProxyUsageLog

class ProxyProvider(ABC):
    """代理提供者抽象接口"""

    @abstractmethod
    def get_proxy(self) -> Optional[str]:
        """获取代理URL（httpx格式）"""
        pass

    @abstractmethod
    def record_usage(
        self,
        success: bool,
        response_time: int,
        ai_provider: str = '',
        endpoint: str = '',
        error_message: str = ''
    ):
        """记录使用情况"""
        pass

class NoProxyProvider(ProxyProvider):
    """无代理实现（直连）"""

    def __init__(self, project_id=None):
        self.project_id = project_id

    def get_proxy(self) -> Optional[str]:
        return None

    def record_usage(
        self,
        success: bool,
        response_time: int,
        ai_provider: str = '',
        endpoint: str = '',
        error_message: str = ''
    ):
        # 直连不记录代理使用日志
        pass

class SingleProxyProvider(ProxyProvider):
    """单一代理提供者"""

    def __init__(self, proxy_config: ProxyConfig, project_id=None):
        self.proxy_config = proxy_config
        self.project_id = project_id

    def get_proxy(self) -> Optional[str]:
        if not self.proxy_config.is_active:
            return None

        if not self.proxy_config.is_healthy:
            # 代理不健康，返回None触发降级
            return None

        return self.proxy_config.get_proxy_url()

    def record_usage(
        self,
        success: bool,
        response_time: int,
        ai_provider: str = '',
        endpoint: str = '',
        error_message: str = ''
    ):
        ProxyUsageLog.objects.create(
            proxy=self.proxy_config,
            ai_provider=ai_provider,
            endpoint=endpoint,
            response_time_ms=response_time,
            success=success,
            error_message=error_message
        )

        # 更新最后使用时间
        ProxyConfig.objects.filter(
            id=self.proxy_config.id
        ).update(last_used_at=timezone.now())

class ProxyManager:
    """代理管理器（门面模式）"""

    @staticmethod
    def get_provider(proxy_id: Optional[int] = None, project_id: Optional[int] = None) -> ProxyProvider:
        """
        工厂方法：根据proxy_id返回相应的Provider

        Args:
            proxy_id: 代理配置ID
            project_id: 项目ID（用于日志记录）

        Returns:
            ProxyProvider实例
        """
        if proxy_id is None:
            return NoProxyProvider(project_id)

        try:
            proxy_config = ProxyConfig.objects.get(
                id=proxy_id,
                is_active=True
            )
            return SingleProxyProvider(proxy_config, project_id)
        except ProxyConfig.DoesNotExist:
            # 代理不存在或被禁用，降级到直连
            return NoProxyProvider(project_id)
```

### AI客户端集成

```python
# core/ai_client/base.py (修改)

from apps.proxy.services import ProxyManager

class BaseAIClient(ABC):
    """AI客户端基类"""

    def __init__(
        self,
        api_key: str,
        proxy_id: Optional[int] = None,
        **kwargs
    ):
        self.api_key = api_key
        self.project_id = kwargs.get('project_id')  # 从任务上下文获取
        # 🔥 新增：代理支持
        self.proxy_provider = ProxyManager.get_provider(
            proxy_id,
            self.project_id
        )
        self._async_client = None
        self._sync_client = None

    def _get_httpx_config(self) -> dict:
        """获取httpx配置（子类调用）"""
        config = {
            'timeout': 30.0,
            'limits': self._get_connection_limits()
        }

        # 🔥 新增：代理配置
        proxy_url = self.proxy_provider.get_proxy()
        if proxy_url:
            config['proxies'] = {
                'http://': proxy_url,
                'https://': proxy_url,
            }

        return config

    async def _call_api_with_fallback(
        self,
        endpoint: str,
        method: str = 'POST',
        **kwargs
    ):
        """
        调用API（含自动降级）

        降级策略：
        1. 尝试使用代理
        2. 代理失败时自动降级到直连
        3. 记录降级事件到日志
        """
        import time
        import httpx

        start_time = time.time()
        proxy_used = self.proxy_provider.get_proxy() is not None

        try:
            # 尝试调用（可能通过代理或直连）
            config = self._get_httpx_config()
            async with httpx.AsyncClient(**config) as client:
                response = await getattr(client, method.lower())(endpoint, **kwargs)
                response.raise_for_status()

            # 记录成功日志
            response_time = int((time.time() - start_time) * 1000)
            self.proxy_provider.record_usage(
                success=True,
                response_time=response_time,
                ai_provider=self.__class__.__name__,
                endpoint=endpoint
            )

            return response

        except (httpx.ProxyError, httpx.ConnectError, httpx.TimeoutException) as e:
            # 代理相关错误
            if proxy_used:
                # 🔥 自动降级：移除代理配置，重试一次
                config = self._get_httpx_config()
                config.pop('proxies', None)  # 移除代理

                try:
                    async with httpx.AsyncClient(**config) as client:
                        response = await getattr(client, method.lower())(endpoint, **kwargs)
                        response.raise_for_status()

                    # 记录降级成功
                    response_time = int((time.time() - start_time) * 1000)
                    self.proxy_provider.record_usage(
                        success=True,
                        response_time=response_time,
                        ai_provider=self.__class__.__name__,
                        endpoint=endpoint,
                        error_message=f'DEGRADED: {str(e)}'
                    )

                    return response

                except Exception as fallback_error:
                    # 降级也失败，记录错误
                    response_time = int((time.time() - start_time) * 1000)
                    self.proxy_provider.record_usage(
                        success=False,
                        response_time=response_time,
                        ai_provider=self.__class__.__name__,
                        endpoint=endpoint,
                        error_message=f'PROXY_AND_DIRECT_FAILED: {str(fallback_error)}'
                    )
                    raise

            # 直连也失败，记录错误并重新抛出
            response_time = int((time.time() - start_time) * 1000)
            self.proxy_provider.record_usage(
                success=False,
                response_time=response_time,
                ai_provider=self.__class__.__name__,
                endpoint=endpoint,
                error_message=str(e)
            )
            raise
```

---

## API Interface Design

### Django REST Framework API

#### apps/proxy/serializers.py

```python
from rest_framework import serializers
from .models import ProxyConfig, ProxyUsageLog

class ProxyConfigSerializer(serializers.ModelSerializer):
    """代理配置序列化器"""

    class Meta:
        model = ProxyConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'last_used_at']

    def to_representation(self, instance):
        """隐藏加密密码"""
        data = super().to_representation(instance)
        if instance.password_encrypted:
            data['password_encrypted'] = '•••••••••'
        return data

class ProxyConfigSelectSerializer(serializers.ModelSerializer):
    """用于前端选择的简化序列化器（只读）"""

    class Meta:
        model = ProxyConfig
        fields = ['id', 'name', 'protocol', 'host', 'port', 'is_healthy']
        read_only_fields = fields

class ProxyUsageLogSerializer(serializers.ModelSerializer):
    """使用日志序列化器"""

    proxy_name = serializers.CharField(source='proxy.name', read_only=True)

    class Meta:
        model = ProxyUsageLog
        fields = '__all__'
```

#### apps/proxy/views.py

```python
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
import httpx
from .models import ProxyConfig, ProxyUsageLog
from .serializers import (
    ProxyConfigSerializer,
    ProxyConfigSelectSerializer,
    ProxyUsageLogSerializer
)

class ProxyConfigViewSet(viewsets.ModelViewSet):
    """代理配置CRUD API（管理员专用）"""

    queryset = ProxyConfig.objects.all()
    serializer_class = ProxyConfigSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        """创建时加密密码"""
        instance = serializer.save()

        # 处理密码加密
        password = serializer.validated_data.get('password')
        if password:
            instance.password_encrypted = instance.encrypt_password(password)
            instance.save()

    def perform_update(self, serializer):
        """更新时处理密码加密"""
        instance = serializer.save()

        # 如果提供了新密码，加密后保存
        password = serializer.validated_data.get('password')
        if password and password != '•••••••••':
            instance.password_encrypted = instance.encrypt_password(password)
            instance.save()

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试代理连接"""
        proxy = self.get_object()

        if not proxy.is_active:
            return Response({
                'success': False,
                'error': '代理未启用'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            proxy_url = proxy.get_proxy_url()

            with httpx.Client(
                proxies={'all://': proxy_url},
                timeout=5.0
            ) as client:
                response = client.get('https://httpbin.org/ip')

            # 解析响应获取代理IP
            result = response.json()
            proxy_ip = result.get('origin', 'Unknown')

            return Response({
                'success': True,
                'proxy_ip': proxy_ip,
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'message': '连接成功'
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def select(self, request):
        """
        只读API：返回启用且健康的代理列表
        普通用户可用，用于项目配置时的代理选择
        """
        proxies = ProxyConfig.objects.filter(
            is_active=True,
            is_healthy=True
        ).values('id', 'name', 'protocol', 'host', 'port')

        return Response({
            'results': list(proxies)
        })

class ProxyUsageLogViewSet(viewsets.ReadOnlyModelViewSet):
    """使用日志只读API"""

    queryset = ProxyUsageLog.objects.select_related('proxy').all()
    serializer_class = ProxyUsageLogSerializer
    permission_classes = [permissions.IsAuthenticated]  # 登录用户可查看

    def get_queryset(self):
        """支持筛选"""
        queryset = super().get_queryset()

        # 时间范围筛选
        time_range = self.request.query_params.get('time_range')
        if time_range == '1h':
            from django.utils import timezone
            cutoff = timezone.now() - timedelta(hours=1)
            queryset = queryset.filter(timestamp__gte=cutoff)
        elif time_range == '24h':
            from django.utils import timezone
            cutoff = timezone.now() - timedelta(days=1)
            queryset = queryset.filter(timestamp__gte=cutoff)

        # 代理筛选
        proxy_id = self.request.query_params.get('proxy_id')
        if proxy_id:
            queryset = queryset.filter(proxy_id=proxy_id)

        # AI提供商筛选
        provider = self.request.query_params.get('ai_provider')
        if provider:
            queryset = queryset.filter(ai_provider=provider)

        # 成功/失败筛选
        success = self.request.query_params.get('success')
        if success is not None:
            queryset = queryset.filter(success=success.lower() == 'true')

        return queryset
```

#### apps/proxy/urls.py

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProxyConfigViewSet, ProxyUsageLogViewSet

router = DefaultRouter()
router.register(r'proxy', ProxyConfigViewSet, basename='proxyconfig')
router.register(r'logs', ProxyUsageLogViewSet, basename='proxyusagelog')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
```

---

## Technical Decisions

### ADR-001: 使用Django Admin作为管理界面

**Status**: Accepted
**Date**: 2026-01-30
**Deciders**: Root, Architect Team

**Context**:
需要为代理管理功能提供用户界面。选项包括：
1. Django Admin（开箱即用）
2. 前端Vue完整管理界面（需要开发8-10天）

**Decision**:
使用Django Admin作为管理界面。

**Rationale**:
- **开发效率**: Django Admin开箱即用，1天vs 10天
- **功能完整**: 列表、搜索、筛选、批量操作全内置
- **权限控制**: IsAdminUser权限简单有效
- **一致性**: 后台管理功能统一使用Django Admin
- **用户群体**: 管理员用户熟悉Django Admin

**Consequences**:
- ✅ 快速上线（1.5天总开发时间）
- ✅ 管理员在Django Admin中完成所有操作
- ✅ 普通用户在前端只能选择代理（符合权限要求）
- ⚠️ 前端无完整管理界面（V2可选）

**Alternatives Considered**:
- 前端Vue完整管理界面：开发成本高，但用户体验更好
- 混合方案：Django Admin + 前端只读视图（已采纳）

---

### ADR-002: 策略模式实现代理提供者

**Status**: Accepted
**Date**: 2026-01-30
**Deciders**: Root, Architect Team

**Context**:
需要支持无代理、单一代理、代理池轮询（V2）等多种代理使用方式。

**Decision**:
使用策略模式实现ProxyProvider接口：
- `NoProxyProvider`: 直连
- `SingleProxyProvider`: 单一代理
- `RoundRobinProxyProvider`: 轮询代理池（V2）

**Rationale**:
- **开闭原则**: 新增代理类型无需修改现有代码
- **单一职责**: 每个Provider只负责一种代理策略
- **可测试性**: 每种策略可独立测试
- **扩展性**: V2轻松添加负载均衡、故障转移

**Code Example**:
```python
# 使用示例
proxy_provider = ProxyManager.get_provider(proxy_id=5)
proxy_url = proxy_provider.get_proxy()  # 返回None或代理URL
```

**Consequences**:
- ✅ AI客户端代码简洁（无需if-else判断）
- ✅ 易于单元测试（Mock不同Provider）
- ✅ V2扩展成本低

---

### ADR-003: Fernet对称加密保护密码

**Status**: Accepted
**Date**: 2026-01-30
**Deciders**: Root, Security Team

**Context**:
代理密码需要安全存储。选项包括：
1. Fernet对称加密
2. Hash单向加密（不可逆）
3. Django的make_password

**Decision**:
使用Fernet对称加密。

**Rationale**:
- **可逆性**: 需要解密后使用代理，Hash不可用
- **安全性**: AES-128加密强度足够
- **性能**: 加密/解密速度快（<1ms）
- **可用性**: Django内置cryptography库

**Key Management**:
- 密钥存储在环境变量：`PROXY_ENCRYPTION_KEY`
- 使用`generate_proxy_key.py`生成密钥
- 密钥丢失后无法解密（文档明确警告）

**Code Example**:
```python
# 加密
f = Fernet(settings.PROXY_ENCRYPTION_KEY)
encrypted = f.encrypt(password.encode()).decode()

# 解密
decrypted = f.decrypt(encrypted.encode()).decode()
```

**Consequences**:
- ✅ 密码安全存储
- ⚠️ 密钥丢失无法恢复（必须有备份流程）
- ⚠️ 环境变量配置（部署文档需说明）

---

### ADR-004: 自动降级策略

**Status**: Accepted
**Date**: 2026-01-30
**Deciders**: Root, Architect Team

**Context**:
代理失败时如何处理？选项包括：
1. 抛出异常
2. 重试N次
3. 自动降级到直连

**Decision**:
自动降级到直连（一次重试）。

**Rationale**:
- **用户体验**: 代理失败时无感知
- **可靠性**: 保证AI调用不中断
- **简单性**: 一次降级，不复杂化逻辑
- **透明性**: 日志记录降级事件

**Implementation**:
```python
try:
    response = await call_with_proxy()
except ProxyError:
    # 自动降级
    response = await call_directly()
    # 记录降级事件
    log_degraded_event()
```

**Consequences**:
- ✅ 服务可用性提升
- ✅ 用户无感知
- ⚠️ 直连可能暴露真实IP（可接受）
- ⚠️ 无法区分代理问题vs真实API问题（日志可追溯）

---

### ADR-005: Celery Beat定时健康检查

**Status**: Accepted
**Date**: 2026-01-30
**Deciders**: Root, DevOps Team

**Context**:
需要监控代理健康状态。选项包括：
1. 被动检查（使用时检查）
2. Celery Beat定时检查
3. 外部监控

**Decision**:
Celery Beat每5分钟检查一次。

**Rationale**:
- **基础设施**: 已有Celery Beat，无需新增依赖
- **及时性**: 5分钟检测间隔合理
- **自动化**: 无需人工干预
- **可观测**: 健康状态实时更新

**Health Check Logic**:
- 5分钟内失败>3次 → 标记为不健康
- 连续3次成功 → 标记为健康
- 不健康的代理不从API返回

**Consequences**:
- ✅ 自动化监控
- ✅ 及时发现问题
- ⚠️ Redis依赖（已有）
- ⚠️ 5分钟延迟（可接受）

---

## Deployment Architecture

### Development Environment

```mermaid
graph TB
    subgraph "Developer Machine"
        VSCode[VSCode Code]
        Terminal[Terminal]
    end

    subgraph "Backend Services"
        Django[Django Runserver<br/>python manage.py runserver]
        Celery[Celery Worker<br/>celery worker -Q llm,image,video]
        CeleryBeat[Celery Beat<br/>celery beat]
    end

    subgraph "Data Layer"
        SQLite[SQLite<br/>db.sqlite3]
        Redis[Redis<br/>docker run -p 6379:6379 redis]
    end

    subgraph "Frontend"
        Vue[Vue Dev Server<br/>npm run dev]
    end

    VSCode -->|manage.py| Django
    Terminal -->|启动| Celery
    Terminal -->|启动| CeleryBeat
    Terminal -->|启动| Vue

    Django -->|ORM| SQLite
    Celery -->|消息队列| Redis
    CeleryBeat -->|任务调度| Redis

    Vue -->|API| Django
```

### Production Environment

```mermaid
graph TB
    subgraph "Load Balancer"
        Nginx[Nginx Reverse Proxy]
    end

    subgraph "Application Servers"
        Gunicorn1[Gunicorn 1<br/>gunicorn config.wsgi:application]
        Gunicorn2[Gunicorn 2<br/>gunicorn config.wsgi:application]
        Gunicorn3[Gunicorn 3<br/>gunicorn config.wsgi:application]
    end

    subgraph "Worker Servers"
        CeleryWorker1[Celery Worker 1<br/>celery worker -Q llm,image,video]
        CeleryWorker2[Celery Worker 2<br/>celery worker -Q llm,image,video]
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL<br/>Production DB)]
        Redis[(Redis<br/>5 Databases)]
    end

    subgraph "External Services"
        OpenAI[OpenAI API]
        ProxyServer[代理服务器]
    end

    Nginx -->|负载均衡| Gunicorn1
    Nginx -->|负载均衡| Gunicorn2
    Nginx -->|负载均衡| Gunicorn3

    Gunicorn1 -->|ORM| PostgreSQL
    Gunicorn2 -->|ORM| PostgreSQL
    Gunicorn3 -->|ORM| PostgreSQL

    CeleryWorker1 -->|ORM| PostgreSQL
    CeleryWorker2 -->|ORM| PostgreSQL

    Gunicorn1 -->|消息队列| Redis
    CeleryWorker1 -->|消息队列| Redis

    Gunicorn1 -->|API调用| OpenAI
    Gunicorn1 -->|通过代理| ProxyServer

    CeleryWorker1 -->|定时任务| Gunicorn1
```

### Environment Variables

**Backend (.env)**
```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_story

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# 🔥 Proxy Encryption (Required for proxy feature)
PROXY_ENCRYPTION_KEY=your-generated-fernet-key-here

# Proxy Health Check
PROXY_HEALTH_CHECK_INTERVAL=300  # seconds
PROXY_HEALTH_CHECK_TIMEOUT=5
PROXY_HEALTH_CHECK_URL=https://httpbin.org/ip

# Proxy Fallback
PROXY_MAX_FAILURES_BEFORE_UNHEALTHY=3
PROXY_FAILURE_TIME_WINDOW=300
```

---

## Testing Strategy

### Test Pyramid

```mermaid
graph TB
    subgraph "E2E Tests (10%)"
        AdminFlow[Django Admin<br/>代理配置流程]
        FrontendFlow[前端<br/>代理选择器]
    end

    subgraph "Integration Tests (30%)"
        APITests[API接口测试]
        AIClientTests[AI客户端<br/>代理集成]
        CeleryTests[健康检查<br/>定时任务]
    end

    subgraph "Unit Tests (60%)"
        ModelTests[ProxyConfig<br/>模型测试]
        ServiceTests[ProxyManager<br/>服务测试]
        EncryptionTests[密码加密<br/>单元测试]
    end

    E2E Tests --> Integration Tests
    Integration Tests --> Unit Tests
```

### Test Coverage Goals

| 组件 | 目标覆盖率 | 关键测试 |
|------|-----------|---------|
| `apps/proxy/models.py` | > 90% | ProxyConfig CRUD、密码加密/解密 |
| `apps/proxy/services.py` | > 85% | ProxyManager、ProxyProvider策略 |
| `apps/proxy/views.py` | > 80% | API endpoints、权限控制 |
| `core/ai_client/base.py` | > 75% | 代理集成、自动降级 |
| `apps/proxy/tasks.py` | > 80% | 健康检查任务 |

### Critical Test Scenarios

**1. 密码加密解密一致性**
```python
def test_password_encryption_decryption_roundtrip():
    proxy = ProxyConfig(name='test', protocol='http', host='localhost', port=8080)
    original = 'Secret@123'

    encrypted = proxy.encrypt_password(original)
    decrypted = proxy.decrypt_password(encrypted)

    assert decrypted == original
```

**2. 代理失败自动降级**
```python
@pytest.mark.asyncio
async def test_proxy_failure_auto_degraded():
    # 配置无效代理
    proxy = ProxyConfig.objects.create(
        name='bad_proxy',
        protocol='http',
        host='192.0.2.1',  # TEST-NET-1（不可路由）
        port=9999
    )

    client = OpenAIClient(api_key='test', proxy_id=proxy.id)
    # 应该自动降级到直连
    # API调用应该成功（或记录降级日志）
```

**3. 健康检查任务**
```python
@patch('apps.proxy.services.httpx.Client')
def test_health_check_success(mock_client):
    # Mock代理响应
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'origin': '203.0.113.42'}
    mock_client.return_value.__enter__.return_value.get.return_value = mock_response

    call_command('check_proxy_health')

    proxy = ProxyConfig.objects.get(name='test-proxy')
    assert proxy.is_healthy == True
```

---

## Migration Plan

### Database Migration

**Step 1: 创建迁移文件**
```bash
cd backend
uv run python manage.py makemigrations proxy
```

**Step 2: 检查迁移文件**
```bash
uv run python manage.py sqlmigrate proxy 0001
```

**Step 3: 执行迁移**
```bash
uv run python manage.py migrate proxy
```

**Step 4: 验证迁移**
```bash
uv run python manage.py showmigrations proxy
uv run python manage.py dbshell
# 在PostgreSQL shell中:
\dt proxy_*  # 查看proxy表
\d proxy_proxyconfig  # 查看表结构
```

### Zero-Downtime Deployment

**Phase 1: 准备（5分钟）**
1. 备份数据库
2. 生成加密密钥：`uv run python generate_proxy_key.py`
3. 配置环境变量

**Phase 2: 代码部署（10分钟）**
1. Pull代码
2. 安装依赖：`uv sync`
3. 执行迁移：`uv run python manage.py migrate`
4. 收集静态文件：`uv run python manage.py collectstatic`
5. 重启Gunicorn：`systemctl reload gunicorn`

**Phase 3: Celery重启（5分钟）**
1. 重启Celery Beat：`systemctl restart celery-beat`
2. 重启Celery Worker：`systemctl restart celery-worker`

**Phase 4: 验证（5分钟）**
1. 检查Django Admin：访问`/admin/proxy/`
2. 检查Celery Beat：查看日志
3. 测试API：`curl /api/v1/proxy/select/`
4. 测试AI客户端：创建测试项目并使用代理

**Total: ~25分钟**

---

## Monitoring & Observability

### Metrics to Track

**业务指标:**
- 代理配置数量
- 代理使用率
- AI调用成功率（使用代理的项目）
- 降级事件次数

**技术指标:**
- 健康检查任务执行成功率
- 代理测试连接响应时间
- AI调用额外延迟
- Celery任务失败率

**Grafana Dashboard建议:**
- Panel 1: 代理健康状态（单值面板）
- Panel 2: AI调用成功率（时间序列图）
- Panel 3: 降级事件计数（时间序列图）
- Panel 4: 代理使用率（饼图）
- Panel 5: 响应时间分布（直连vs代理）

### Alerting Rules

**Critical Alerts:**
- 健康检查任务失败率 > 5%
- 所有代理不可用（is_healthy=False）
- 密钥加密测试失败

**Warning Alerts:**
- 单个代理连续失败10次
- 降级率 > 10%

---

## Security Considerations

### Threat Model

| 威胁 | 影响 | 缓解措施 |
|------|------|---------|
| 密钥泄露导致所有代理密码暴露 | 高 | 密钥存储在环境变量，文档明确警告 |
| 日志中记录明文密码 | 高 | 代码审查+PRD明确禁止 |
| 管理员权限滥用 | 中 | Django Admin审计日志 |
| 代理服务器劫持 | 中 | 测试连接使用可信endpoint (httpbin.org/ip) |
| CSRF攻击 | 低 | Django CSRF保护 + SameSite Cookie |

### Access Control

**Django Admin:**
- 超级用户：所有权限
- 管理员：CRUD权限
- 其他用户：无访问权限

**API:**
- `/api/v1/proxy/` CRUD: IsAdminUser
- `/api/v1/proxy/select/`: IsAuthenticated（所有登录用户）
- `/api/v1/proxy/{id}/test_connection/`: IsAdminUser

---

## Future Enhancements (V2)

### Load Balancing
- 轮询（Round Robin）
- 加权轮询（Weighted Round Robin）
- 最少连接（Least Connections）

### Auto Failover
- 代理间自动切换
- 故障检测和隔离
- 自动恢复

### Advanced Monitoring
- 实时性能仪表盘（Grafana）
- 告警通知（邮件、Slack、Webhook）
- 代理成本统计和优化建议

### SOCKS5 Support
- 安装`httpx[socks]`
- 扩展ProxyProtocol枚举
- 测试SOCKS5代理连接

---

## Appendix

### Glossary

- **Proxy Provider**: 代理提供者，策略模式实现
- **Auto Degradation**: 自动降级，代理失败时自动切换到直连
- **Health Check**: 健康检查，定时测试代理可用性
- **Fernet**: Python对称加密库（AES-128）

### References

- PRD Document: `/home/code/ai_story/_bmad-output/planning-artifacts/prd-proxy-management.md`
- Party Mode Discussion: 专家团队讨论记录
- Django Admin Documentation: https://docs.djangoproject.com/en/stable/ref/contrib/admin/
- httpx Documentation: https://www.python-httpx.org/

---

**Document Version:** 1.0
**Last Updated:** 2026-01-30
**Status:** Complete - Ready for Epics & Stories

