---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics']
inputDocuments:
  - /home/code/ai_story/_bmad-output/planning-artifacts/prd-proxy-management.md
  - /home/code/ai_story/_bmad-output/planning-artifacts/architecture-proxy-management.md
  - /home/code/ai_story/_bmad-output/planning-artifacts/ux-design-specification.md
workflowType: 'epics-and-stories'
project_name: '代理管理系统'
user_name: 'Root'
date: '2026-01-30'
---

# 代理管理系统 - Epic Breakdown

## Overview

本文档将PRD、Architecture和UX的需求分解为可实施的Epic和Story，为开发团队提供清晰的实施路线图。

**项目背景:**
- **类型:** 系统增强功能 (Brownfield)
- **技术栈:** Django 3.2.15 + DRF + Vue 2.7.14 + Fernet + Celery Beat + httpx[socks]
- **开发估算:** Epic 9.0 (14天) + Epic 9.5 (4.5天，可选)
- **团队规模:** 1名全栈开发者

---

## Requirements Inventory

### Functional Requirements

**F1: 代理配置管理 (5个需求)**
- **FR1.1** - 管理员可以通过Django Admin创建新代理配置（必填: name, protocol, host, port; 可选: username, password, description, priority）
- **FR1.2** - Django Admin显示所有代理配置列表（字段: name, protocol, host:port, is_active, is_healthy, priority），支持搜索和筛选
- **FR1.3** - 管理员可以修改代理信息（密码字段显示为占位符，修改后自动加密）
- **FR1.4** - 管理员可以删除未使用的代理（已被项目引用的代理禁止删除，级联保护）
- **FR1.5** - 管理员可以切换is_active状态（禁用的代理不参与AI调用）

**F2: 代理测试 (2个需求)**
- **FR2.1** - Django Admin提供"Test Connection"按钮，测试URL: https://httpbin.org/ip，返回代理IP或错误信息
- **FR2.2** - 项目创建页面提供"测试连接"按钮，AJAX异步请求，不阻塞界面

**F3: 健康检查 (3个需求)**
- **FR3.1** - Celery Beat每5分钟执行一次健康检查，遍历所有启用状态的代理，测试连接并更新is_healthy字段
- **FR3.2** - 5分钟内失败超过3次标记为不健康，不健康的代理不从API返回
- **FR3.3** - 连续3次成功标记为健康，恢复后重新参与代理池

**F4: 使用日志 (2个需求)**
- **FR4.1** - 每次AI调用记录日志到ProxyUsageLog（字段: proxy_id, ai_provider, endpoint, response_time_ms, success, error_message, timestamp）
- **FR4.2** - Django Admin提供日志浏览界面，支持按时间、代理、AI提供商筛选，只读权限

**F5: AI集成 (3个需求)**
- **FR5.1** - Project模型添加proxy_id外键（可为空，表示不使用代理）
- **FR5.2** - BaseAIClient构造函数接受proxy_id参数，通过ProxyManager获取代理配置，自动构建httpx代理URL
- **FR5.3** - 代理失败后自动降级到直连，记录降级事件到日志

**F6: 前端集成 (2个需求)**
- **FR6.1** - 项目创建页面显示代理下拉框，只显示启用且健康的代理，格式: "代理名称 (协议) - 状态"
- **FR6.2** - 前端调用GET /api/v1/proxy/select/获取代理列表，调用POST /api/v1/proxy/{id}/test_connection/测试连接

**F7: 安全性 (3个需求)**
- **FR7.1** - 密码使用Fernet对称加密存储，密钥存储在环境变量PROXY_ENCRYPTION_KEY
- **FR7.2** - Django Admin权限: IsAdminUser；API只读接口: IsAuthenticated；普通用户只能查看，不能修改
- **FR7.3** - 所有CRUD操作记录到Django Admin日志（包含用户、时间、操作类型）

**功能需求总数: 20个**

---

### Non-Functional Requirements

**NFR1: Security (安全性)**
- **NFR1.1** - 密码加密解密一致性 100%
- **NFR1.2** - Django Admin权限: IsAdminUser
- **NFR1.3** - API权限: 管理员CRUD，普通用户只读
- **NFR1.4** - 审计日志: 所有CRUD操作记录

**NFR2: Performance (性能)**
- **NFR2.1** - 代理测试连接 < 5秒
- **NFR2.2** - AI调用额外延迟 < 100ms（相比直连）
- **NFR2.3** - 并发支持: 100个并发AI调用使用同一代理
- **NFR2.4** - 健康检查任务 < 50MB内存

**NFR3: Reliability (可靠性)**
- **NFR3.1** - 代理失败100%降级到直连
- **NFR3.2** - 数据一致性: 密码加密解密一致，日志记录原子性
- **NFR3.3** - 错误处理: 所有代理错误记录到日志，用户看到友好错误提示
- **NFR3.4** - 向后兼容: 无代理配置时，系统行为与原版本完全一致

**NFR4: Maintainability (可维护性)**
- **NFR4.1** - 代码质量: 遵循SOLID原则，单元测试覆盖率 > 80%，代码符合PEP8规范
- **NFR4.2** - 文档完整: API文档（DRF自动生成），安装和配置指南，故障排查手册

**NFR5: Usability (可用性)**
- **NFR5.1** - Django Admin界面: 列表、搜索、筛选、批量操作、表单验证和错误提示
- **NFR5.2** - 前端体验: 代理选择器易于使用，测试连接实时反馈，加载状态提示

**非功能需求总数: 17个**

---

### Additional Requirements

**从Architecture文档提取:**

**数据层需求:**
- **ADR-001** - ProxyConfig模型（含password_encrypted字段，Fernet加密）
- **ADR-002** - ProxyUsageLog模型（记录每次AI调用的详细信息）
- **ADR-003** - Project模型扩展proxy_id外键（on_delete=SET_NULL，代理删除不删除项目）
- **ADR-004** - 数据库索引: (is_active, is_healthy), (-last_used_at)

**服务层需求:**
- **ADR-005** - ProxyManager（门面模式），提供get_provider()工厂方法
- **ADR-006** - ProxyProvider策略模式实现（NoProxyProvider、SingleProxyProvider）
- **ADR-007** - 自动降级逻辑: try-except捕获httpx.ProxyError，降级到直连

**API层需求:**
- **ADR-008** - DRF ViewSets: ProxyConfigViewSet（IsAdminUser）、ProxyUsageLogViewSet（IsAuthenticated）
- **ADR-009** - Serializers: ProxyConfigSerializer（密码隐藏）、ProxyConfigSelectSerializer（前端选择）、ProxyUsageLogSerializer
- **ADR-010** - API端点: /api/v1/proxy/（CRUD）、/api/v1/proxy/select/（只读）、/api/v1/proxy/{id}/test_connection/（测试）

**AI客户端集成需求:**
- **ADR-011** - BaseAIClient添加proxy_id参数到__init__
- **ADR-012** - _get_httpx_config()方法中添加代理配置逻辑
- **ADR-013** - _call_api_with_fallback()方法实现自动降级

**基础设施需求:**
- **ADR-014** - 密钥生成脚本: generate_proxy_key.py（生成Fernet密钥）
- **ADR-015** - 环境变量配置: PROXY_ENCRYPTION_KEY、PROXY_HEALTH_CHECK_INTERVAL等
- **ADR-016** - Celery Beat配置: 每5分钟执行check_proxy_health任务
- **ADR-017** - 数据库迁移文件: makemigrations proxy、migrate proxy

**测试需求:**
- **ADR-018** - 单元测试: ProxyConfig模型、ProxyManager策略、加密解密、覆盖率 > 80%
- **ADR-019** - 集成测试: 代理配置→AI调用成功、代理失败→自动降级
- **ADR-020** - E2E测试: Django Admin完整流程、前端代理选择器

**前端需求:**
- **ADR-021** - 代理选择器下拉框（daisyUI select组件）
- **ADR-022** - 测试连接按钮（异步AJAX，显示加载状态）
- **ADR-023** - 健康状态可视化（badge颜色: success=绿色、error=红色）

**部署需求:**
- **ADR-024** - 开发环境启动命令配置
- **ADR-025** - 生产环境零停机部署流程（~25分钟）

**从UX文档提取:**

**UI组件需求:**
- **UX-001** - 代理选择器: daisyUI select组件，显示"代理名称 (协议) - ✓/✗"格式
- **UX-002** - 健康状态徽章: badge-success（绿色✓）、badge-error（红色✗）
- **UX-003** - 测试连接按钮: btn-primary btn-sm，异步请求时显示加载状态
- **UX-004** - 加载提示: <span class="loading loading-spinner"></span>
- **UX-005** - 错误提示: alert alert-error组件，显示友好错误消息

**额外需求总数: 30个**

---

### FR Coverage Map

**F1: 代理配置管理**
- FR1.1 - Epic 9.0: Story 9.1 - ProxyConfig模型 + Django Admin CRUD
- FR1.2 - Epic 9.0: Story 9.1 - Django Admin列表显示
- FR1.3 - Epic 9.0: Story 9.1 - 编辑功能（密码占位符）
- FR1.4 - Epic 9.0: Story 9.1 - 删除功能（级联保护）
- FR1.5 - Epic 9.0: Story 9.1 - is_active状态切换

**F2: 代理测试**
- FR2.1 - Epic 9.0: Story 9.9 - Django Admin测试连接按钮
- FR2.2 - Epic 9.0: Story 9.8 - 前端测试连接按钮（异步AJAX）

**F3: 健康检查**
- FR3.1 - Epic 9.0: Story 9.10 - Celery Beat定时检查（5分钟间隔）
- FR3.2 - Epic 9.0: Story 9.10 - 故障标记（失败>3次）
- FR3.3 - Epic 9.0: Story 9.10 - 健康状态恢复（连续成功3次）

**F4: 使用日志**
- FR4.1 - Epic 9.0: Story 9.2 - ProxyUsageLog模型 + 日志记录
- FR4.2 - Epic 9.0: Story 9.11 - Django Admin日志查询界面

**F5: AI集成**
- FR5.1 - Epic 9.0: Story 9.7 - Project模型proxy_id外键
- FR5.2 - Epic 9.0: Story 9.6 - BaseAIClient代理支持
- FR5.3 - Epic 9.0: Story 9.5 - 代理降级策略（自动降级到直连）

**F6: 前端集成**
- FR6.1 - Epic 9.0: Story 9.8 - 项目创建页面代理选择器
- FR6.2 - Epic 9.0: Story 9.8 - API集成（/api/v1/proxy/select/）

**F7: 安全性**
- FR7.1 - Epic 9.0: Story 9.1 - Fernet密码加密
- FR7.2 - Epic 9.0: Story 9.1 - 权限控制（IsAdminUser）
- FR7.3 - Epic 9.0: Story 9.12 - 审计日志（Django Admin日志）

**SOCKS5协议支持（新增）**
- FR-SOCKS5.1 - Epic 9.0: Story 9.1 - ProxyProtocol枚举支持SOCKS5
- FR-SOCKS5.2 - Epic 9.0: Story 9.4 - SOCKS5ProxyProvider实现
- FR-SOCKS5.3 - Epic 9.0: Story 9.6 - httpx[socks]依赖集成

**SSH隧道协议支持（Epic 9.5，可选）**
- FR-SSH.1 - Epic 9.5: Story 9.13 - SSH数据模型扩展
- FR-SSH.2 - Epic 9.5: Story 9.14 - SSH连接管理器（单例模式）
- FR-SSH.3 - Epic 9.5: Story 9.15 - SSH隧道代理提供者
- FR-SSH.4 - Epic 9.5: Story 9.16 - SSH状态监控
- FR-SSH.5 - Epic 9.5: Story 9.17 - SSH测试（连接泄漏测试）

**覆盖率: 100%** ✅

---

## Epic List

### Epic 9.0: 多协议代理管理基础 (HTTP/HTTPS/SOCKS5)

**用户价值:** 管理员可以配置HTTP/HTTPS/SOCKS5代理，开发者可以在项目中使用代理调用AI API，系统提供自动降级和基础监控能力。

**FRs covered:** FR1-FR7 + FR-SOCKS5.1-3 (20个功能需求)

**工作量估算:** 14天 (12个Story)

**依赖关系:** 无外部依赖，可独立开发和部署

**Story列表:**

```
【第一阶段：数据层】(2天)
├── Story 9.1: ProxyConfig模型 + Fernet加密 (1天)
│   ├── 实现ProxyConfig模型（name, protocol, host, port, username, password_encrypted）
│   ├── 支持协议：HTTP, HTTPS, SOCKS5
│   ├── Fernet密码加密/解密
│   ├── Django Admin CRUD界面
│   └── 验收：密码加密解密一致性100%，管理员可完整管理代理配置
│
└── Story 9.2: ProxyUsageLog模型 + Admin界面 (1天)
    ├── 实现ProxyUsageLog模型（proxy, ai_provider, endpoint, response_time_ms, success, error_message）
    ├── Django Admin只读界面（支持时间、代理、AI提供商筛选）
    └── 验收：管理员可查询代理使用日志，模型定义正确

【第二阶段：服务层】(2天)
├── Story 9.3: ProxyManager + NoProxyProvider (1天)
│   ├── 实现ProxyManager工厂类
│   ├── 实现NoProxyProvider（直连场景）
│   └── 验收：proxy_id=None时返回NoProxyProvider，系统行为与原版本一致
│
├── Story 9.4: SingleProxyProvider实现 (1天)
│   ├── 实现SingleProxyProvider（HTTP/HTTPS/SOCKS5）
│   ├── httpx配置（支持socks5://协议）
│   ├── 安装httpx[socks]依赖
│   └── 验收：3种协议代理正常工作，单元测试覆盖率>80%

【第三阶段：降级逻辑】(1天)
└── Story 9.5: 代理降级逻辑 (1天)
    ├── 在ProxyProvider中实现降级策略
    ├── 代理失败时自动降级到直连
    ├── 记录降级事件到日志
    └── 验收：代理失败时100%降级，降级事件正确记录

【第四阶段：AI集成】(2天)
├── Story 9.6: BaseAIClient代理支持 (1.5天)
│   ├── BaseAIClient添加proxy_id参数
│   ├── _get_httpx_config()方法中集成代理
│   ├── _call_api_with_fallback()方法实现降级
│   └── 验收：AI客户端可通过代理调用API，降级逻辑正确
│
└── Story 9.7: Project模型proxy_id外键 (0.5天)
    ├── Project模型添加proxy_id外键（on_delete=SET_NULL）
    ├── 数据库迁移
    └── 验收：项目可绑定代理配置，代理删除不删除项目

【第五阶段：用户界面】(2天)
├── Story 9.8: 前端代理选择器 + API调用 (2天)
│   ├── 前端代理选择器（daisyUI select组件）
│   ├── 健康状态可视化（badge颜色映射）
│   ├── 测试连接按钮（异步AJAX）
│   ├── GET /api/v1/proxy/select/ API
│   ├── POST /api/v1/proxy/{id}/test_connection/ API
│   └── 验收：用户可在项目创建时选择代理，测试连接功能正常

【第六阶段：监控运维】(2天)
├── Story 9.9: 测试连接功能（Django Admin） (0.5天)
│   ├── Django Admin"Test Connection"按钮
│   ├── 测试URL: https://httpbin.org/ip
│   ├── 失败明确报错（不降级）
│   └── 验收：管理员可测试代理连通性，失败时明确提示错误
│
├── Story 9.10: Celery Beat健康检查 (1.5天)
│   ├── Celery Beat定时任务（每5分钟）
│   ├── 测试所有启用状态的代理
│   ├── 更新is_healthy字段（失败>3次标记不健康，连续成功3次恢复）
│   └── 验收：健康检查自动执行，代理健康状态准确更新

【第七阶段：测试与文档】(3天)
└── Story 9.12: 单元测试 + 集成测试 + E2E测试 (3天)
    ├── 单元测试：ProxyConfig模型、ProxyManager策略、加密解密、覆盖率>80%
    ├── 集成测试：代理配置→AI调用成功、代理失败→自动降级
    ├── E2E测试：Django Admin完整流程、前端代理选择器
    ├── API文档：DRF自动生成文档
    ├── 部署文档：环境配置、启动命令、故障排查
    └── 验收：所有测试通过，文档完整，无已知严重Bug
```

**交付物:**
- ✅ 完整的代理管理系统（HTTP/HTTPS/SOCKS5）
- ✅ Django Admin管理界面
- ✅ 前端代理选择器
- ✅ 自动降级逻辑
- ✅ 健康检查机制
- ✅ 使用日志记录
- ✅ 测试覆盖率>80%
- ✅ 完整文档

---

### Epic 9.5: SSH隧道代理（可选扩展）

**用户价值:** 管理员可以配置SSH隧道代理，支持跳板机访问内网API和高度加密传输。

**FRs covered:** FR-SSH.1-5 (5个SSH特定功能需求)

**工作量估算:** 4.5天 (6个Story)

**前置条件:** Epic 9.0上线并获得用户反馈（>30%用户需要SSH OR 竞品压力 OR 关键客户需求）

**依赖关系:** 依赖Epic 9.0的基础设施（ProxyManager, ProxyProvider）

**决策条件:** 根据Epic 9.0上线后的用户反馈和数据驱动决策

**Story列表:**

```
【第一阶段：SSH基础】(2.5天)
├── Story 9.13: SSH数据模型扩展 (0.5天)
│   ├── ProxyConfig增加SSH字段（ssh_host, ssh_port, ssh_username, ssh_key_path）
│   ├── ProxyProtocol枚举增加SSH选项
│   ├── SSH密钥管理（存储路径，非明文）
│   └── 验收：Admin界面可配置SSH代理参数
│
├── Story 9.14: 简化SSH连接管理器 (1天)
│   ├── 实现SimpleSSHTunnelProvider（单例模式）
│   ├── paramiko集成（SSH客户端库）
│   ├── 懒加载连接（首次使用时建立）
│   ├── 简单重连机制（最多3次，指数退避）
│   ├── 无心跳线程（依赖SSH timeout）
│   └── 验收：SSH隧道自动建立，连接失败时自动重连
│
└── Story 9.15: SSH隧道代理提供者 (1天)
    ├── Local Port Forwarding配置
    ├── 动态端口分配
    ├── 与ProxyManager集成
    └── 验收：SSH隧道代理正常工作，AI调用可通过SSH隧道

【第二阶段：监控与测试】(2天)
├── Story 9.16: SSH状态监控 (0.5天)
│   ├── Admin界面显示SSH连接状态（已连接/未连接/错误）
│   ├── 手动重连/断开操作
│   ├── SSH连接错误日志
│   └── 验收：管理员可监控SSH连接状态，手动操作连接
│
├── Story 9.17: SSH测试 (1天)
│   ├── 单元测试（Mock paramiko）
│   ├── 集成测试（真实SSH服务器）
│   ├── 连接泄漏测试
│   ├── 并发安全测试（单例串行化验证）
│   └── 验收：SSH测试覆盖率>85%，连接泄漏测试通过
│
└── Story 9.18: SSH文档 (0.5天)
    ├── SSH密钥生成指南
    ├── 部署配置文档
    ├── 故障排查手册（连接失败、密钥问题）
    └── 验收：文档完整，用户可按指南独立配置SSH代理
```

**技术方案（最小可行SSH）:**
- ✅ 单例模式（无连接池）
- ✅ 简单重连（最多3次）
- ❌ 无心跳线程（依赖SSH timeout）
- ❌ 无并发优化（单例自动串行化）

**交付物:**
- ✅ SSH隧道代理配置功能
- ✅ SSH连接管理（单例模式）
- ✅ SSH状态监控
- ✅ SSH测试套件
- ✅ SSH文档

---

## Epic决策总结

**分阶段策略:**
1. **Epic 9.0** (14天) - 多协议代理基础（HTTP/HTTPS/SOCKS5），快速交付核心价值
2. **Epic 9.5** (4.5天，可选) - SSH隧道代理，根据Epic 9.0用户反馈决定是否执行

**优势:**
- ✅ 快速交付MVP (2.5周)
- ✅ 风险隔离（SSH复杂度不拖累Epic 9.0）
- ✅ 反馈驱动（Phase 2根据用户反馈决策）
- ✅ 工作量清晰（14天 + 4.5天可选）

**关键里程碑:**
- Day 14: Epic 9.0上线，收集用户反馈
- Day 14-21: 用户反馈分析期
- Day 21: 决策是否执行Epic 9.5

---

## 附录：技术决策记录（ADR摘要）

**ADR-001: 使用Django Admin作为管理界面** ✅ Epic 9.0
**ADR-002: 策略模式实现代理提供者** ✅ Epic 9.0
**ADR-003: Fernet对称加密保护密码** ✅ Epic 9.0
**ADR-004: 自动降级策略** ✅ Epic 9.0
**ADR-005: Celery Beat定时健康检查** ✅ Epic 9.0
**ADR-006: 单例模式SSH连接管理** ✅ Epic 9.5
**ADR-007: 最小可行SSH方案** ✅ Epic 9.5

---

**文档版本:** 2.0
**最后更新:** 2026-01-30
**状态:** Step 2完成 - Epic结构已确定，待Step 3创建详细Story

