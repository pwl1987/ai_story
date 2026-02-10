# Epic 9.0 - 代理管理系统完整Story文档

**Epic名称:** 代理配置与管理系统
**创建日期:** 2026-01-30
**基于文档:** PRD + Architecture + Story 9.1优化经验
**总计Story数:** 13个
**总估算工作量:** 15天

---

## Story 9.0: 代理管理基础设施准备

**用户故事:**
作为开发者，
我需要准备代理管理功能的基础设施（依赖、密钥、目录结构），
以便后续Story可以顺利实现代理功能。

**验收标准:**

[场景1: 依赖安装成功]
Given 项目缺少代理相关依赖
When 执行依赖安装命令
Then cryptography和httpx[socks]成功安装
And 版本兼容性检查通过

[场景2: Django App创建]
Given backend/apps目录存在
When 创建apps/proxy目录结构
Then __init__.py、apps.py、models.py等基础文件存在
And 在settings.py中注册'apps.proxy'

[场景3: 加密密钥生成]
Given 缺少PROXY_ENCRYPTION_KEY环境变量
When 执行generate_proxy_key.py脚本
Then 生成44字符的Fernet密钥
And 输出密钥到控制台
And 提示将密钥添加到.env文件

[场景4: URL配置]
Given config/urls.py存在
When 添加proxy app的URL配置
Then /api/v1/proxy/路由注册成功
And 可以访问Django Admin的proxy页面

[场景5: 数据库迁移准备]
Given ProxyConfig和ProxyUsageLog模型已定义
When 执行makemigrations命令
Then 生成0001_initial.py迁移文件
And 迁移文件包含proxy_proxyconfig和proxy_proxyusagelog表

**技术实现要点:**
- 安装cryptography库（Fernet加密）
- 安装httpx[socks]（SOCKS5代理支持）
- 创建apps/proxy目录结构（__init__.py, apps.py, models.py, admin.py, services.py, views.py, serializers.py, urls.py, tasks.py）
- 生成加密密钥脚本generate_proxy_key.py（使用Fernet.generate_key()）
- 在config/settings/base.py中注册'apps.proxy'
- 在config/urls.py中包含proxy的URL配置
- 创建空的Admin配置类（占位符）

**前置条件:**
- Django项目正常运行
- Python 3.8+环境
- uv包管理器可用

**依赖关系:**
- 无（这是Epic 9的第一个Story）

**估算:**
- 0.5天

**DoD:**
- [ ] cryptography和httpx[socks]依赖已安装并在pyproject.toml中记录
- [ ] apps/proxy目录结构完整（9个基础文件）
- [ ] generate_proxy_key.py脚本可执行并生成有效密钥
- [ ] 'apps.proxy'已在settings.py的INSTALLED_APPS中注册
- [ ] config/urls.py包含proxy的路由配置
- [ ] 数据库迁移文件生成成功（makemigrations proxy）
- [ ] Django Admin可以访问（即使显示空列表）
- [ ] .env.example文件添加PROXY_ENCRYPTION_KEY说明
- [ ] 开发环境验证通过（python manage.py check无错误）

---

## Story 9.1: ProxyConfig模型 + Fernet加密实现

**用户故事:**
作为系统管理员，
我希望通过Django Admin创建和配置代理（名称、协议、主机、端口、用户名、密码），
以便系统可以通过代理访问外部AI API。

**验收标准:**

[场景1: 创建HTTP代理（无认证）]
Given Django Admin代理创建页面
When 填写name="测试代理", protocol="http", host="proxy.example.com", port=8080
And 不填写用户名和密码
Then 代理创建成功
And is_active默认为True
And is_healthy默认为True
And priority默认为0
And password_encrypted为空

[场景2: 创建HTTPS代理（带认证）]
Given Django Admin代理创建页面
When 填写完整信息（包含username和password）
Then 密码自动加密存储到password_encrypted字段
And 明文密码不会被保存
And 数据库中的password_encrypted字段不为空

[场景3: 密码加密解密一致性]
Given 已创建带密码的代理
When 调用proxy.encrypt_password("Secret@123")
And 调用proxy.decrypt_password(encrypted_password)
Then 解密结果与原始密码完全一致
And 加密后的密文与明文不同
And 多次加密相同密码产生不同密文（Fernet特性）

[场景4: 代理URL构建]
Given 代理配置protocol="https", host="proxy.example.com", port=8080, username="user", password="pass"
When 调用proxy.get_proxy_url()
Then 返回"https://user:pass@proxy.example.com:8080"
Given 代理配置无用户名密码
When 调用proxy.get_proxy_url()
Then 返回"https://proxy.example.com:8080"

[场景5: 字段验证]
Given 创建代理时
When port字段填写为0或65536
Then Django显示验证错误："端口号必须在1-65535之间"
When name字段填写为已存在的代理名称
Then Django显示IntegrityError或唯一性约束错误

[场景6: 索引验证]
Given 数据库中有100个代理配置
When 执行查询ProxyConfig.objects.filter(is_active=True, is_healthy=True)
Then 查询使用索引（is_active, is_healthy联合索引）
When 按last_used_at降序排列
Then 查询使用索引（-last_used_at索引）

[场景7: Django Admin显示]
Given Django Admin代理列表页面
When 访问/admin/proxy/proxyconfig/
Then 显示所有字段（name, protocol, host:port, is_active, is_healthy, priority）
And password_encrypted显示为"•••••••••"（不显示明文）
And 列表按priority降序、name升序排列
And 支持按name搜索
And 支持按is_active和is_healthy筛选

[场景8: 密钥缺失处理]
Given PROXY_ENCRYPTION_KEY环境变量未设置
When 尝试创建带密码的代理
Then 系统抛出ImproperlyConfigured异常
And 错误消息提示："需要设置PROXY_ENCRYPTION_KEY环境变量"

**技术实现要点:**
- 实现ProxyConfig模型（包含所有字段和Meta配置）
- 实现ProxyProtocol枚举（HTTP, HTTPS, SOCKS5）
- 实现encrypt_password()方法（使用Fernet）
- 实现decrypt_password()方法
- 实现get_proxy_url()方法（构建httpx代理URL）
- 实现clean()方法（验证port范围）
- 配置Django Admin（list_display, list_filter, search_fields, readonly_fields）
- 密码字段在Admin中显示为占位符"•••••••••"
- 添加数据库索引（is_active, is_healthy联合索引；-last_used_at索引）

**前置条件:**
- Story 9.0已完成（基础设施准备就绪）
- PROXY_ENCRYPTION_KEY环境变量已设置

**依赖关系:**
- 依赖 Story 9.0

**估算:**
- 1.5天

**DoD:**
- [ ] ProxyConfig模型实现完整（13个字段）
- [ ] ProxyProtocol枚举定义（HTTP, HTTPS, SOCKS5）
- [ ] encrypt_password()方法通过单元测试（加密非空、密文与明文不同）
- [ ] decrypt_password()方法通过单元测试（解密一致性）
- [ ] get_proxy_url()方法通过单元测试（4种场景：有/无认证、HTTP/HTTPS）
- [ ] clean()方法验证port范围（1-65535）
- [ ] 数据库索引创建成功（2个索引）
- [ ] Django Admin配置完整（list_display包含7个字段）
- [ ] password_encrypted在Admin中显示为"•••••••••"
- [ ] Django Admin支持按name、is_active、is_healthy筛选
- [ ] 单元测试覆盖率 > 90%（包含密码加密解密、URL构建、字段验证）
- [ ] 集成测试验证Django Admin CRUD流程
- [ ] 错误场景测试通过（密钥缺失、port范围错误、name重复）

---

## Story 9.2: ProxyUsageLog模型 + Admin界面

**用户故事:**
作为系统管理员，
我需要查看代理使用日志（AI提供商、端点、响应时间、成功/失败、错误信息），
以便分析代理性能和诊断故障。

**验收标准:**

[场景1: 日志自动创建]
Given 已配置代理的项目调用AI API
When AI调用完成
Then ProxyUsageLog自动创建一条记录
And proxy字段正确关联到ProxyConfig
And ai_provider字段记录AI客户端类型（如"OpenAIClient"）
And endpoint字段记录API端点
And response_time_ms字段记录响应时间（毫秒）
And success字段记录调用是否成功
And error_message字段在失败时记录错误信息

[场景2: 时间戳自动记录]
Given 创建新的日志记录
When 保存到数据库
Then timestamp字段自动设置为当前时间
And timestamp字段不可手动修改

[场景3: Django Admin列表显示]
Given Django Admin日志列表页面
When 访问/admin/proxy/proxyusagelog/
Then 显示所有字段（proxy_name, ai_provider, endpoint, response_time_ms, success, timestamp）
And proxy_name通过外键关联显示
And success字段显示为绿色勾选（成功）或红色叉号（失败）
And timestamp字段显示为可读格式（"2026-01-30 10:30:45"）

[场景4: 日志筛选功能]
Given 日志列表页面
When 选择proxy筛选条件（如"OpenAI美国代理-01"）
Then 只显示该代理的日志记录
When 选择success筛选条件（如"失败"）
Then 只显示success=False的记录
When 选择time_range筛选条件（如"最近24小时"）
Then 只显示最近24小时的日志

[场景5: 日志只读权限]
Given 普通用户登录Django Admin
When 访问ProxyUsageLog页面
Then 可以查看日志列表
And 不显示"添加"按钮
And 不显示"删除"按钮
And 不显示"保存"按钮（只读模式）

[场景6: 日志索引验证]
Given 数据库中有10000条日志记录
When 执行查询ProxyUsageLog.objects.filter(proxy_id=5).order_by('-timestamp')
Then 查询使用索引（proxy, -timestamp联合索引）
When 执行查询ProxyUsageLog.objects.filter(ai_provider='OpenAIClient', success=False)
Then 查询使用索引（ai_provider, -timestamp联合索引）

[场景7: 错误信息记录]
Given AI调用失败
When 捕获到异常（如ConnectionTimeout）
Then error_message字段记录完整异常信息
And success字段设置为False
And response_time_ms记录到失败时刻的时间

[场景8: 批量操作支持]
Given 日志列表页面
When 勾选多条日志记录
Then 可以执行"导出为CSV"批量操作
And 可以执行"删除选定日志"批量操作（仅管理员）
And 批量删除时显示二次确认对话框

**技术实现要点:**
- 实现ProxyUsageLog模型（包含8个字段）
- 配置Django Admin（list_display, list_filter, readonly_fields）
- 实现proxy_name属性（通过外键关联显示）
- 添加数据库索引（3个联合索引）
- 配置Admin权限（只读模式，IsAuthenticated）
- 实现自定义Admin Action（导出CSV）
- 实现时间范围筛选（最近1小时、24小时、7天、30天）
- 配置success字段显示（boolean图标）
- 配置格式化显示（timestamp、response_time_ms）

**前置条件:**
- Story 9.1已完成（ProxyConfig模型可用）

**依赖关系:**
- 依赖 Story 9.1

**估算:**
- 1天

**DoD:**
- [ ] ProxyUsageLog模型实现完整（8个字段）
- [ ] timestamp字段auto_now_add=True
- [ ] Django Admin配置完整（list_display包含6个字段）
- [ ] Admin权限设置为只读（readonly_fields = 所有字段）
- [ ] 数据库索引创建成功（3个联合索引）
- [ ] proxy_name通过外键关联显示（source='proxy.name'）
- [ ] success字段显示boolean图标（绿色勾选/红色叉号）
- [ ] 支持按proxy、ai_provider、success、time_range筛选
- [ ] 批量操作"导出为CSV"可用
- [ ] 批量删除操作仅管理员可用
- [ ] 单元测试覆盖率 > 85%（模型验证、索引、Admin配置）
- [ ] 集成测试验证日志记录和Admin筛选
- [ ] 错误信息正确记录（包含异常堆栈）

---

## Story 9.3: ProxyManager + NoProxyProvider实现

**用户故事:**
作为开发者，
我需要实现ProxyManager服务层和NoProxyProvider策略（直连模式），
以便AI客户端可以通过统一的接口使用代理或直连。

**验收标准:**

[场景1: NoProxyProvider返回None]
Given 初始化NoProxyProvider实例
When 调用provider.get_proxy()
Then 返回None
And 不抛出任何异常

[场景2: NoProxyProvider不记录日志]
Given 初始化NoProxyProvider实例
When 调用provider.record_usage(success=True, response_time=100)
Then 不创建任何ProxyUsageLog记录
And 不抛出任何异常

[场景3: ProxyManager工厂方法]
Given proxy_id=None
When 调用ProxyManager.get_provider(None)
Then 返回NoProxyProvider实例
Given proxy_id=999（不存在的代理）
When 调用ProxyManager.get_provider(999)
Then 返回NoProxyProvider实例（降级到直连）

[场景4: ProxyProvider抽象接口]
Given ProxyProvider是ABC抽象类
When 定义新的Provider子类
Then 必须实现get_proxy()方法
And 必须实现record_usage()方法
And 未实现时抛出TypeError

[场景5: 单元测试覆盖]
Given ProxyManager和NoProxyProvider实现
When 运行单元测试
Then 测试覆盖正常流程（proxy_id=None返回NoProxyProvider）
And 测试覆盖异常流程（proxy_id不存在返回NoProxyProvider）
And 测试覆盖接口契约（子类必须实现抽象方法）
And 测试覆盖率 > 85%

[场景6: 向后兼容性]
Given 现有AI客户端代码未设置proxy_id
When 创建BaseAIClient实例（不传proxy_id参数）
Then ProxyManager.get_provider返回NoProxyProvider
And get_proxy()返回None
And AI调用行为与原版本完全一致（直连）

[场景7: 项目上下文传递]
Given proxy_id=5, project_id=10
When 调用ProxyManager.get_provider(5, project_id=10)
Then 返回的Provider实例包含project_id信息
And project_id可用于未来日志记录（V2功能）

**技术实现要点:**
- 实现ProxyProvider抽象基类（ABC）
- 定义抽象方法：get_proxy() -> Optional[str], record_usage(...)
- 实现NoProxyProvider类（直连策略）
- 实现ProxyManager.get_provider()工厂方法
- 处理proxy_id=None和proxy_id不存在的情况（返回NoProxyProvider）
- 支持project_id参数传递（为未来扩展准备）
- 遵循策略模式和工厂模式
- 编写单元测试（覆盖正常和异常流程）

**前置条件:**
- Story 9.1已完成（ProxyConfig模型可用）
- Story 9.2已完成（ProxyUsageLog模型可用）

**依赖关系:**
- 依赖 Story 9.1
- 依赖 Story 9.2

**估算:**
- 1天

**DoD:**
- [ ] ProxyProvider抽象基类定义（2个抽象方法）
- [ ] NoProxyProvider实现完整
- [ ] ProxyManager.get_provider()工厂方法实现
- [ ] proxy_id=None返回NoProxyProvider
- [ ] proxy_id不存在返回NoProxyProvider（降级策略）
- [ ] 支持project_id参数传递
- [ ] 单元测试覆盖率 > 85%
- [ ] 向后兼容性测试通过（无proxy_id时直连）
- [ ] 代码符合SOLID原则（单一职责、开闭原则、依赖倒置）
- [ ] 代码符合PEP8规范
- [ ] 文档字符串完整（类和方法的docstring）

---

## Story 9.4: SingleProxyProvider实现

**用户故事:**
作为系统，
我需要实现SingleProxyProvider策略（单一代理模式），
以便AI客户端可以通过配置的代理访问外部API。

**验收标准:**

[场景1: 代理可用且健康]
Given 代理配置is_active=True, is_healthy=True
When 调用provider.get_proxy()
Then 返回代理URL（如"https://user:pass@proxy.example.com:8080"）
And 格式符合httpx代理URL规范

[场景2: 代理已禁用]
Given 代理配置is_active=False
When 调用provider.get_proxy()
Then 返回None（触发降级）

[场景3: 代理不健康]
Given 代理配置is_healthy=False
When 调用provider.get_proxy()
Then 返回None（触发降级）

[场景4: 记录成功日志]
Given AI调用成功（success=True, response_time=250ms）
When 调用provider.record_usage(...)
Then ProxyUsageLog创建一条记录
And success=True
And response_time_ms=250
And ai_provider和endpoint正确记录
And ProxyConfig.last_used_at更新为当前时间

[场景5: 记录失败日志]
Given AI调用失败（success=False, error_message="Connection timeout"）
When 调用provider.record_usage(...)
Then ProxyUsageLog创建一条记录
And success=False
And error_message记录完整错误信息
And ProxyConfig.last_used_at仍然更新

[场景6: 密码解密错误处理]
Given 代理配置password_encrypted字段损坏或密钥错误
When 调用provider.get_proxy()
Then 捕获解密异常
And 记录错误日志
And 返回None（触发降级）
And 不影响AI调用流程

[场景7: ProxyManager集成]
Given proxy_id=5（存在的代理配置）
When 调用ProxyManager.get_provider(5)
Then 返回SingleProxyProvider实例
And provider.proxy_config正确指向id=5的ProxyConfig

[场景8: 单元测试覆盖]
Given SingleProxyProvider实现
When 运行单元测试
Then 测试覆盖代理可用场景（返回代理URL）
And 测试覆盖代理禁用场景（返回None）
And 测试覆盖代理不健康场景（返回None）
And 测试覆盖日志记录场景（成功和失败）
And 测试覆盖last_used_at更新
And 测试覆盖率 > 85%

**技术实现要点:**
- 实现SingleProxyProvider类（继承ProxyProvider）
- 构造函数接收proxy_config和project_id
- get_proxy()方法：检查is_active和is_healthy，返回代理URL或None
- record_usage()方法：创建ProxyUsageLog记录，更新last_used_at
- 调用proxy_config.get_proxy_url()获取代理URL
- 处理解密异常（返回None）
- 更新ProxyManager.get_provider()以返回SingleProxyProvider
- 编写单元测试（覆盖所有场景）

**前置条件:**
- Story 9.1已完成（ProxyConfig模型可用）
- Story 9.2已完成（ProxyUsageLog模型可用）
- Story 9.3已完成（ProxyProvider抽象接口和ProxyManager可用）

**依赖关系:**
- 依赖 Story 9.1
- 依赖 Story 9.2
- 依赖 Story 9.3

**估算:**
- 1天

**DoD:**
- [ ] SingleProxyProvider实现完整
- [ ] get_proxy()检查is_active和is_healthy
- [ ] get_proxy()返回代理URL或None
- [ ] record_usage()创建ProxyUsageLog记录
- [ ] record_usage()更新last_used_at字段
- [ ] ProxyManager.get_provider()返回SingleProxyProvider
- [ ] 单元测试覆盖率 > 85%
- [ ] 集成测试验证代理使用流程
- [ ] 错误处理测试通过（解密异常、代理不存在）
- [ ] 代码符合SOLID原则
- [ ] 代码符合PEP8规范

---

## Story 9.5: 代理降级逻辑实现

**用户故事:**
作为AI客户端，
当代理失败时，我需要自动降级到直连模式，
以便保障服务可用性。

**验收标准:**

[场景1: 代理连接超时]
Given AI客户端配置代理proxy_id=5
When 调用AI API，代理连接超时（TimeoutException）
Then 自动降级到直连
And 重试一次API调用
And 日志记录："DEGRADED: Proxy timeout, using direct connection"
And 最终API调用成功返回

[场景2: 代理连接错误]
Given AI客户端配置代理proxy_id=5
When 调用AI API，代理返回ConnectionError
Then 自动降级到直连
And 重试一次API调用
And 日志记录："DEGRADED: Proxy connection error, using direct connection"

[场景3: 代理认证失败]
Given AI客户端配置代理proxy_id=5
When 调用AI API，代理返回407 Proxy Authentication Required
Then 自动降级到直连
And 重试一次API调用
And 日志记录："DEGRADED: Proxy authentication failed, using direct connection"

[场景4: 代理和直连都失败]
Given AI客户端配置代理proxy_id=5
When 代理调用失败，降级到直连后直连也失败
Then 抛出原始异常
And 日志记录："PROXY_AND_DIRECT_FAILED: Both proxy and direct connection failed"
And error_message包含两个异常信息

[场景5: 代理调用成功]
Given AI客户端配置代理proxy_id=5
When 调用AI API，代理正常工作
Then 使用代理发送请求
And 不降级到直连
And 日志记录success=True
And 不包含"DEGRADED"标记

[场景6: 日志记录完整性]
Given 代理降级场景
When 降级后API调用成功
Then ProxyUsageLog记录success=True
And error_message字段包含"DEGRADED: {原错误}"
And response_time_ms包含总耗时（代理+重试）
And ai_provider和endpoint正确记录

[场景7: 性能影响最小化]
Given 代理降级逻辑实现
When 测量AI调用延迟
Then 降级逻辑额外延迟 < 10ms（异常捕获和重试逻辑）
And 不影响正常代理调用的性能

[场景8: 异常类型覆盖]
Given 支持降级的异常类型
When 捕获到httpx.ProxyError、httpx.ConnectError、httpx.TimeoutException
Then 都触发降级逻辑
When 捕获到其他异常（如httpx.HTTPStatusError）
Then 不触发降级逻辑（直接抛出）

**技术实现要点:**
- 在BaseAIClient中实现_call_api_with_fallback()方法
- 使用try-except捕获代理相关异常（ProxyError, ConnectError, TimeoutException）
- 代理失败时移除proxies配置，重试一次
- 记录降级事件到ProxyUsageLog（error_message包含"DEGRADED"）
- 降级也失败时，记录"PROXY_AND_DIRECT_FAILED"并抛出异常
- 测量响应时间（包含代理和重试的总时间）
- 只对代理相关异常降级，其他异常直接抛出
- 编写单元测试和集成测试

**前置条件:**
- Story 9.3已完成（ProxyProvider抽象接口）
- Story 9.4已完成（SingleProxyProvider实现）

**依赖关系:**
- 依赖 Story 9.3
- 依赖 Story 9.4

**估算:**
- 1天

**DoD:**
- [ ] _call_api_with_fallback()方法实现
- [ ] 捕获代理相关异常（ProxyError, ConnectError, TimeoutException）
- [ ] 代理失败时自动重试一次（直连）
- [ ] 降级成功日志记录（error_message包含"DEGRADED"）
- [ ] 降级失败日志记录（error_message包含"PROXY_AND_DIRECT_FAILED"）
- [ ] 单元测试覆盖率 > 85%
- [ ] 集成测试验证降级流程（4种异常类型）
- [ ] 性能测试验证额外延迟 < 10ms
- [ ] 向后兼容性测试通过（无代理时行为一致）
- [ ] 错误处理测试通过（代理和直连都失败）
- [ ] 代码符合SOLID原则（单一职责、开闭原则）

---

## Story 9.6: BaseAIClient代理支持

**用户故事:**
作为AI客户端开发者，
我需要在BaseAIClient基类中添加代理支持，
以便所有AI客户端子类（OpenAI、Claude等）自动继承代理功能。

**验收标准:**

[场景1: BaseAIClient构造函数接收proxy_id]
Given 创建OpenAIClient实例
When 传递proxy_id=5参数
Then client.proxy_provider正确初始化为SingleProxyProvider
And client.project_id正确设置

[场景2: _get_httpx_config返回代理配置]
Given AI客户端配置proxy_id=5（代理可用）
When 调用client._get_httpx_config()
Then 返回的config字典包含'proxies'键
And config['proxies']格式为{'http://': proxy_url, 'https://': proxy_url}
When 配置proxy_id=None（无代理）
Then config字典不包含'proxies'键

[场景3: AI调用自动使用代理]
Given OpenAIClient配置proxy_id=5
When 调用client.chat_completions()方法
Then HTTP请求通过代理发送
And 代理URL格式正确（httpx支持）
And 请求头、认证等不受影响

[场景4: AI调用自动降级]
Given OpenAIClient配置proxy_id=5（代理不可用）
When 调用client.chat_completions()方法
And 代理连接失败
Then 自动降级到直连
And 重试一次API调用
And 日志记录降级事件

[场景5: 子类继承代理功能]
Given 创建新的AI客户端子类（如StableDiffusionClient）
When 继承BaseAIClient
Then 子类自动支持代理功能
And 子类无需修改代码
And 子类调用API时自动使用配置的代理

[场景6: 向后兼容性]
Given 现有代码创建OpenAIClient（不传proxy_id）
When 调用API方法
Then 行为与原版本完全一致（直连）
And 不抛出任何异常
And 不记录ProxyUsageLog

[场景7: 项目上下文传递]
Given 创建OpenAIClient实例（从Celery任务上下文）
When 传递project_id=10
Then client.project_id=10
And project_id可用于日志记录（未来扩展）

[场景8: 单元测试覆盖]
Given BaseAIClient代理支持实现
When 运行单元测试
Then 测试覆盖proxy_id初始化
And 测试覆盖_get_httpx_config()代理配置
And 测试覆盖AI调用使用代理
And 测试覆盖AI调用自动降级
And 测试覆盖率 > 75%

**技术实现要点:**
- 修改BaseAIClient.__init__()，接收proxy_id和project_id参数
- 调用ProxyManager.get_provider()初始化proxy_provider
- 实现_get_httpx_config()方法，添加代理配置
- 集成_call_api_with_fallback()方法（Story 9.5实现）
- 所有子类（OpenAIClient、ClaudeClient等）自动继承代理功能
- 保持向后兼容（proxy_id默认为None）
- 编写单元测试和集成测试

**前置条件:**
- Story 9.3已完成（ProxyManager可用）
- Story 9.4已完成（SingleProxyProvider可用）
- Story 9.5已完成（降级逻辑可用）

**依赖关系:**
- 依赖 Story 9.3
- 依赖 Story 9.4
- 依赖 Story 9.5

**估算:**
- 1.5天

**DoD:**
- [ ] BaseAIClient.__init__()接收proxy_id和project_id参数
- [ ] proxy_provider通过ProxyManager初始化
- [ ] _get_httpx_config()方法实现（返回代理配置）
- [ ] _call_api_with_fallback()集成到API调用流程
- [ ] 所有子类自动继承代理功能（OpenAI、Claude、Stable Diffusion）
- [ ] 向后兼容性测试通过（无proxy_id时直连）
- [ ] 单元测试覆盖率 > 75%
- [ ] 集成测试验证AI调用通过代理
- [ ] 集成测试验证AI调用自动降级
- [ ] 性能测试验证代理调用额外延迟 < 100ms
- [ ] 代码符合SOLID原则（开闭原则）
- [ ] 代码符合PEP8规范

---

## Story 9.7: Project模型proxy_id外键

**用户故事:**
作为系统，
我需要在Project模型中添加proxy_id外键，
以便项目可以关联代理配置。

**验收标准:**

[场景1: 数据库迁移]
Given 执行makemigrations命令
When 修改Project模型添加proxy_id字段
Then 生成迁移文件（如0002_add_proxy_id_to_project.py）
And 迁移文件包含add_field操作
And proxy_id设置为ForeignKey（指向proxy.ProxyConfig）
And on_delete设置为SET_NULL（代理删除时不删除项目）
And null=True, blank=True（允许为空）

[场景2: 迁移执行成功]
Given 执行migrate命令
When 运行迁移
Then proxy_proxyconfig_id字段添加到project_project表
And 现有Project记录的proxy_id为NULL
And 迁移无错误

[场景3: Django Admin显示]
Given Django Admin项目编辑页面
When 打开Project详情页
Then 显示"代理配置"下拉框
And 下拉框包含所有已创建的代理配置
And 允许选择"--------"（无代理）
And 选中代理后显示代理名称（如"OpenAI美国代理-01"）

[场景4: API序列化]
Given 通过API获取Project列表
When 访问/api/v1/projects/
Then 返回的JSON包含proxy_id字段
And proxy_id为整数或null
And 可选包含proxy_name（嵌套序列化）

[场景5: 前端兼容性]
Given 前端Project组件
When 加载Project数据（包含proxy_id）
Then 组件正常渲染
And proxy_id字段可正常访问
And 不影响现有Project显示逻辑

[场景6: 级联删除保护]
Given 项目A关联代理B（project.proxy_id = B.id）
When 尝试删除代理B
Then Django显示保护错误："无法删除代理，因为它被1个项目使用"
And 代理不被删除
When 先将项目A的proxy_id设置为NULL
Then 可以成功删除代理B

[场景7: 反向关联查询]
Given 代理配置proxy_id=5
When 执行proxy_config.projects.all()
Then 返回所有使用该代理的项目列表
And related_name='projects'正确配置

[场景8: 单元测试]
Given Project模型添加proxy_id外键
When 运行单元测试
Then 测试覆盖数据库迁移
And 测试覆盖Project创建时设置proxy_id
And 测试覆盖Project修改proxy_id
And 测试覆盖级联删除保护
And 测试覆盖率 > 80%

**技术实现要点:**
- 在apps/projects/models.py的Project模型中添加proxy_config字段
- 字段类型：ForeignKey('proxy.ProxyConfig', on_delete=models.SET_NULL)
- 配置：null=True, blank=True, related_name='projects'
- 生成并执行数据库迁移
- 更新ProjectSerializer（可选包含proxy_name）
- Django Admin配置（添加proxy_config到list_display和fields）
- 编写单元测试

**前置条件:**
- Story 9.1已完成（ProxyConfig模型可用）
- apps/projects应用正常运行

**依赖关系:**
- 依赖 Story 9.1

**估算:**
- 0.5天

**DoD:**
- [ ] Project.proxy_config字段添加成功
- [ ] 数据库迁移文件生成并执行
- [ ] proxy_id允许为NULL（向后兼容）
- [ ] on_delete=SET_NULL配置正确
- [ ] Django Admin显示代理配置下拉框
- [ ] API序列化器包含proxy_id字段
- [ ] 级联删除保护测试通过
- [ ] 反向关联查询测试通过（proxy_config.projects.all()）
- [ ] 单元测试覆盖率 > 80%
- [ ] 现有Project数据不受影响（proxy_id为NULL）
- [ ] 前端组件正常工作（proxy_id字段可访问）

---

## Story 9.8: 前端代理选择器 + API调用

**用户故事:**
作为应用开发者，
我需要在创建项目时选择代理配置，
以便项目可以自动使用指定的代理调用AI API。

**验收标准:**

[场景1: 代理列表API调用]
Given 前端项目创建页面加载
When 调用GET /api/v1/proxy/select/
Then 返回启用且健康的代理列表
And 响应格式：{results: [{id, name, protocol, host, port, is_healthy}, ...]}
And 只返回is_active=True且is_healthy=True的代理
And 响应时间 < 500ms

[场景2: 代理选择器显示]
Given 代理列表API返回成功
When 项目创建页面渲染
Then 显示"代理配置"下拉框
And 下拉框第一项为"不使用代理"（value=null）
And 其他选项显示格式："代理名称 (协议) - 状态"
And 状态标识：✓健康 或 ❌不健康

[场景3: 代理选择保存]
Given 用户在下拉框选择"OpenAI美国代理-01 (HTTPS) - ✓健康"
When 点击"保存"按钮
Then 项目创建请求包含proxy_id字段（值为代理ID）
And 后端成功保存Project记录
And 前端跳转到项目详情页

[场景4: 测试连接功能]
Given 用户在下拉框选择代理
When 点击"测试连接"按钮
Then 调用POST /api/v1/proxy/{id}/test_connection/
And 按钮显示加载状态（"测试中..."）
And 测试成功后显示："✓ 连接成功！IP: 203.0.113.42，响应时间: 245ms"
And 测试失败后显示："✗ 连接失败：Connection timeout"

[场景5: 无代理选项]
Given 用户在下拉框选择"不使用代理"
When 保存项目
Then proxy_id字段为null
And 项目调用AI API时直连
And 日志不记录ProxyUsageLog

[场景6: 错误处理]
Given 代理列表API调用失败
When 前端捕获错误
Then 显示友好提示："无法加载代理列表，请稍后重试"
And 下拉框显示为禁用状态
And 不影响其他表单字段填写

[场景7: 权限控制]
Given 普通用户登录
When 访问项目创建页面
Then 可以查看代理选择器
And 可以选择代理
And 不能修改代理配置（只有管理员可访问Django Admin）

[场景8: 响应式设计]
Given 用户在移动设备访问
When 项目创建页面加载
Then 代理选择器正常显示
And 下拉框宽度自适应屏幕
And 测试连接按钮可点击

**技术实现要点:**
- 前端：修改CreateProject.vue组件
- 添加代理选择器（<select>下拉框）
- 调用GET /api/v1/proxy/select/获取代理列表
- 实现测试连接按钮（POST /api/v1/proxy/{id}/test_connection/）
- 添加加载状态和错误处理
- 样式优化（状态标识、响应式布局）
- API权限控制：/api/v1/proxy/select/允许所有认证用户访问
- 编写E2E测试

**前置条件:**
- Story 9.1已完成（ProxyConfig模型可用）
- Story 9.7已完成（Project.proxy_id字段可用）
- 后端API已实现（/api/v1/proxy/select/和test_connection）

**依赖关系:**
- 依赖 Story 9.1
- 依赖 Story 9.7

**估算:**
- 2天

**DoD:**
- [ ] 前端代理选择器实现（<select>下拉框）
- [ ] 代理列表API调用（GET /api/v1/proxy/select/）
- [ ] 代理选项格式："代理名称 (协议) - 状态"
- [ ] 测试连接按钮实现（POST /api/v1/proxy/{id}/test_connection/）
- [ ] 加载状态显示（"测试中..."）
- [ ] 成功/失败提示显示
- [ ] 错误处理（API失败时友好提示）
- [ ] "不使用代理"选项（value=null）
- [ ] 项目保存时包含proxy_id字段
- [ ] 响应式设计（移动端适配）
- [ ] API权限控制（普通用户可访问）
- [ ] E2E测试验证完整流程
- [ ] 前端代码符合Vue 2.7规范
- [ ] 前端代码符合项目现有风格

---

## Story 9.9: 测试连接功能（Django Admin）

**用户故事:**
作为系统管理员，
我需要在Django Admin中测试代理连接，
以便验证代理配置是否正确可用。

**验收标准:**

[场景1: 测试按钮显示]
Given Django Admin代理列表页面
When 打开ProxyConfig详情页
Then 右侧操作栏显示"Test Connection"按钮
And 按钮样式为按钮（非链接）

[场景2: 测试连接成功]
Given 代理配置正确可用
When 点击"Test Connection"按钮
Then 发送测试请求到https://httpbin.org/ip
And 3秒内返回响应
And Django显示成功消息："✓ 连接成功！代理IP: 203.0.113.42，响应时间: 245ms"
And 不显示错误信息

[场景3: 测试连接失败]
Given 代理配置错误（如主机不存在）
When 点击"Test Connection"按钮
Then 请求超时（5秒）
And Django显示错误消息："✗ 连接失败：Connection timeout"
And 错误消息包含具体异常信息

[场景4: 代理未启用]
Given 代理配置is_active=False
When 点击"Test Connection"按钮
Then 立即返回错误
And Django显示错误消息："代理未启用，无法测试"
And 不发送实际请求

[场景5: 测试响应时间]
Given 代理正常工作
When 点击"Test Connection"按钮
Then 返回的成功消息包含响应时间（毫秒）
And 响应时间基于实际HTTP请求耗时

[场景6: 自定义Admin Action]
Given 代理列表页面
When 勾选多个代理
And 选择"测试连接"批量操作
Then 依次测试每个代理
And 显示汇总结果："成功3个，失败1个"

[场景7: 异步处理]
Given 点击"Test Connection"按钮
When 请求发送中
Then 按钮显示为禁用状态
And 页面不阻塞
And 测试完成后刷新页面显示结果

[场景8: 日志记录]
Given 测试连接成功
When 请求完成
Then 创建ProxyUsageLog记录
And ai_provider="system"
And endpoint="https://httpbin.org/ip"
And success=True或False
And response_time_ms记录测试耗时

**技术实现要点:**
- 在ProxyConfigAdmin中添加自定义Admin Action
- 实现test_connection()方法（使用@admin.action装饰器）
- 使用httpx.Client发送测试请求（GET https://httpbin.org/ip）
- 配置超时为5秒
- 解析响应获取代理IP
- 记录响应时间
- 创建ProxyUsageLog记录
- 返回HttpResponseRedirect或JSON响应
- 处理异常（连接失败、超时等）
- 编写单元测试

**前置条件:**
- Story 9.1已完成（ProxyConfig模型可用）
- Story 9.2已完成（ProxyUsageLog模型可用）
- httpx库已安装

**依赖关系:**
- 依赖 Story 9.1
- 依赖 Story 9.2

**估算:**
- 0.5天

**DoD:**
- [ ] test_connection()方法实现
- [ ] Admin按钮显示在详情页
- [ ] 测试成功时显示代理IP和响应时间
- [ ] 测试失败时显示错误信息
- [ ] is_active=False时立即返回错误
- [ ] 超时配置为5秒
- [ ] 创建ProxyUsageLog记录
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试验证测试连接流程
- [ ] 异常处理测试通过（超时、连接失败、代理未启用）
- [ ] 代码符合Django Admin最佳实践

---

## Story 9.10: Celery Beat健康检查实现

**用户故事:**
作为系统，
我需要通过Celery Beat定时检查代理健康状态，
以便自动标记不可用的代理并维护代理池质量。

**验收标准:**

[场景1: Celery Beat任务注册]
Given config/celery.py已配置Celery Beat
When 添加代理健康检查任务
Then 任务注册到Celery Beat调度器
And 任务名称为"apps.proxy.tasks.check_proxy_health"
And 执行间隔为5分钟（300秒）

[场景2: 健康检查任务执行]
Given Celery Beat运行中
When 每5分钟触发一次任务
Then 任务查询所有is_active=True的代理
And 依次测试每个代理连接
And 更新is_healthy字段
And 创建ProxyUsageLog记录

[场景3: 代理健康]
Given 代理正常工作
When 健康检查任务执行
Then 测试请求成功
And is_healthy设置为True
And ProxyUsageLog记录success=True
And 响应时间 < 3秒

[场景4: 代理不健康]
Given 代理连接失败
When 健康检查任务执行
Then 测试请求失败（超时或连接错误）
And is_healthy设置为False
And ProxyUsageLog记录success=False
And error_message记录错误信息

[场景5: 连续失败判断]
Given 代理在5分钟内失败1次
When 健康检查任务执行
Then 代理仍标记为健康（容忍单次失败）
Given 代理在5分钟内失败超过3次
When 健康检查任务执行
Then 代理标记为不健康（is_healthy=False）

[场景6: 健康恢复判断]
Given 代理当前is_healthy=False
When 健康检查任务执行
And 连续3次检查成功
Then is_healthy设置为True（恢复健康状态）
And 代理重新参与代理池

[场景7: 任务日志记录]
Given Celery Beat执行任务
When 任务完成
Then Celery日志记录任务执行状态
And 日志包含："Checked 5 proxies, 4 healthy, 1 unhealthy"
And 异常情况记录错误日志

[场景8: 性能要求]
Given 健康检查任务执行
When 任务运行
Then 内存占用 < 50MB
And 单个代理测试超时为5秒
And 总任务执行时间 < 30秒（假设最多10个代理）

**技术实现要点:**
- 在apps/proxy/tasks.py中实现check_proxy_health任务
- 使用@shared_task装饰器
- 查询ProxyConfig.objects.filter(is_active=True)
- 使用httpx.Client测试连接（GET https://httpbin.org/ip）
- 超时配置为5秒
- 实现连续失败逻辑（5分钟内失败>3次标记不健康）
- 实现健康恢复逻辑（连续3次成功标记健康）
- 创建ProxyUsageLog记录
- 在config/celery.py中注册Celery Beat定时任务
- 配置任务间隔为300秒（5分钟）
- 编写单元测试

**前置条件:**
- Story 9.1已完成（ProxyConfig模型可用）
- Story 9.2已完成（ProxyUsageLog模型可用）
- Celery Beat已配置并运行

**依赖关系:**
- 依赖 Story 9.1
- 依赖 Story 9.2

**估算:**
- 1.5天

**DoD:**
- [ ] check_proxy_health任务实现
- [ ] Celery Beat定时任务注册（5分钟间隔）
- [ ] 查询is_active=True的代理
- [ ] 测试连接（httpx请求，5秒超时）
- [ ] 更新is_healthy字段（True/False）
- [ ] 创建ProxyUsageLog记录
- [ ] 连续失败逻辑实现（5分钟内失败>3次）
- [ ] 健康恢复逻辑实现（连续3次成功）
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试验证健康检查流程
- [ ] 性能测试验证内存占用 < 50MB
- [ ] Celery日志记录任务执行状态
- [ ] 异常处理测试通过（代理超时、连接失败）

---

## Story 9.11: 文档和部署指南

**用户故事:**
作为DevOps工程师，
我需要完整的文档和部署指南，
以便顺利部署和维护代理管理系统。

**验收标准:**

[场景1: 安装指南完整]
Given 阅读INSTALLATION.md
When 按照指南操作
Then 可以成功完成依赖安装
And 可以成功生成加密密钥
And 可以成功配置环境变量
And 可以成功执行数据库迁移

[场景2: 配置指南完整]
Given 阅读CONFIGURATION.md
When 配置代理系统
Then 可以正确设置PROXY_ENCRYPTION_KEY
And 可以正确配置Celery Beat
And 可以正确配置Django Admin
And 可以正确配置API权限

[场景3: 使用指南完整]
Given 阅读USAGE.md
When 使用代理功能
Then 可以成功创建第一个代理配置
And 可以成功测试代理连接
And 可以成功在项目中配置代理
And 可以成功查看使用日志

[场景4: 故障排查指南完整]
Given 阅读TROUBLESHOOTING.md
When 遇到问题
Then 可以找到常见问题解决方案
And 可以找到错误信息含义
And 可以找到调试方法
And 包含日志查看命令

[场景5: API文档完整]
Given 阅读API.md
When 调用API
Then 可以找到所有API端点说明
And 可以找到请求/响应示例
And 可以找到权限要求
And 可以找到错误码说明

[场景6: 部署清单完整]
Given 阅读DEPLOYMENT_CHECKLIST.md
When 部署到生产环境
Then 可以逐项检查部署步骤
And 包含数据库备份步骤
And 包含密钥备份步骤
And 包含回滚步骤

[场景7: 安全指南完整]
Given 阅读SECURITY.md
When 配置安全策略
Then 可以了解密钥管理最佳实践
And 可以了解权限控制策略
And 可以了解审计日志查看方法
And 可以了解常见安全风险

[场景8: 文档示例正确]
Given 文档中的代码示例
When 复制执行
Then 示例代码可以正常运行
And 示例输出与文档描述一致
And 示例包含必要的上下文说明

**技术实现要点:**
- 创建docs/proxy/目录
- 编写INSTALLATION.md（安装指南）
- 编写CONFIGURATION.md（配置指南）
- 编写USAGE.md（使用指南）
- 编写TROUBLESHOOTING.md（故障排查）
- 编写API.md（API文档）
- 编写DEPLOYMENT_CHECKLIST.md（部署清单）
- 编写SECURITY.md（安全指南）
- 更新主README.md（添加代理管理功能说明）
- 创建generate_proxy_key.py文档（密钥生成脚本说明）
- 编写代码示例和命令示例
- 添加流程图和架构图

**前置条件:**
- 所有前置Story已完成
- 代理管理功能开发完成

**依赖关系:**
- 依赖 所有前置Story（9.0-9.10）

**估算:**
- 1天

**DoD:**
- [ ] INSTALLATION.md文档完整（8个步骤）
- [ ] CONFIGURATION.md文档完整（5个配置项）
- [ ] USAGE.md文档完整（4个使用场景）
- [ ] TROUBLESHOOTING.md文档完整（10个常见问题）
- [ ] API.md文档完整（3个API端点）
- [ ] DEPLOYMENT_CHECKLIST.md文档完整（15个检查项）
- [ ] SECURITY.md文档完整（4个安全主题）
- [ ] generate_proxy_key.py使用说明
- [ ] 主README.md更新（添加代理功能介绍）
- [ ] 所有代码示例可运行
- [ ] 所有命令示例可复制执行
- [ ] 文档包含流程图和架构图
- [ ] 文档拼写检查通过
- [ ] 文档链接测试通过（无死链）

---

## Story 9.12: 单元测试 + 集成测试 + E2E测试

**用户故事:**
作为质量保证工程师，
我需要完整的测试套件（单元测试、集成测试、E2E测试），
以便确保代理管理系统的质量和稳定性。

**验收标准:**

[场景1: 单元测试覆盖率]
Given 运行pytest --cov=apps/proxy
When 测试完成
Then 总体覆盖率 > 80%
And apps/proxy/models.py覆盖率 > 90%
And apps/proxy/services.py覆盖率 > 85%
And apps/proxy/views.py覆盖率 > 80%
And apps/proxy/tasks.py覆盖率 > 80%
And core/ai_client/base.py覆盖率 > 75%

[场景2: 模型单元测试]
Given ProxyConfig模型
When 运行模型测试
Then 测试密码加密解密一致性
And 测试get_proxy_url()方法（4种场景）
And 测试clean()验证方法
And 测试字段默认值
And 测试索引创建
Given ProxyUsageLog模型
When 运行模型测试
Then 测试字段验证
And 测试时间戳自动设置
And 测试外键关联

[场景3: 服务层单元测试]
Given ProxyManager和ProxyProvider
When 运行服务层测试
Then 测试ProxyManager.get_provider()工厂方法
And 测试NoProxyProvider.get_proxy()返回None
And 测试SingleProxyProvider.get_proxy()（可用/禁用/不健康）
And 测试record_usage()创建日志
And 测试last_used_at更新

[场景4: AI客户端集成测试]
Given BaseAIClient代理支持
When 运行AI客户端测试
Then 测试代理URL配置
And 测试代理调用成功
And 测试代理调用自动降级
And 测试降级后日志记录
And 测试向后兼容性（无proxy_id）

[场景5: API集成测试]
Given DRF API端点
When 运行API测试
Then 测试GET /api/v1/proxy/select/（普通用户可访问）
And 测试POST /api/v1/proxy/{id}/test_connection/
And 测试权限控制（IsAdminUser for CRUD）
And 测试筛选功能（时间、代理、AI提供商、成功/失败）
And 测试序列化器（密码隐藏）

[场景6: Celery任务集成测试]
Given check_proxy_health任务
When 运行任务测试
Then 测试任务注册（Celery Beat）
And 测试健康检查逻辑（成功/失败）
And 测试连续失败判断（>3次标记不健康）
And 测试健康恢复判断（连续3次成功）
And 测试日志记录
And 使用Mock避免实际网络请求

[场景7: E2E测试]
Given 完整系统环境
When 运行E2E测试
Then 测试Django Admin完整流程（创建代理→测试连接→查看日志）
And 测试前端完整流程（创建项目→选择代理→保存→测试连接）
And 测试降级流程（代理失败→自动降级→日志记录）
And 测试健康检查流程（Celery Beat执行→状态更新）
And 使用Selenium或Playwright自动化前端测试

[场景8: 性能测试]
Given 代理系统运行
When 运行性能测试
Then 测试代理测试连接响应时间 < 3秒
And 测试AI调用额外延迟 < 100ms
And 测试健康检查任务内存占用 < 50MB
And 测试并发支持（100个并发请求）
And 使用locust或类似工具

[场景9: 安全测试]
Given 密码加密机制
When 运行安全测试
Then 测试密钥缺失时抛出异常
And 测试日志中不记录明文密码
And 测试API权限控制（管理员vs普通用户）
And 测试Django Admin权限控制
And 测试SQL注入防护

[场景10: 测试报告]
Given 所有测试执行完成
When 生成测试报告
Then HTML报告显示覆盖率百分比
And 报告包含测试通过/失败统计
And 报告包含失败测试的详细错误信息
And 报告包含执行时间统计
And 使用pytest-html或allure生成报告

**技术实现要点:**
- 使用pytest测试框架
- 使用pytest-cov测量覆盖率
- 使用pytest-mock模拟外部依赖
- 使用pytest-django配置Django测试环境
- 使用pytest-asyncio测试异步代码
- 使用factory_boy生成测试数据
- 编写单元测试（apps/proxy/tests/test_models.py, test_services.py, test_views.py, test_tasks.py）
- 编写集成测试（apps/proxy/tests/integration/test_ai_client_integration.py）
- 编写E2E测试（使用Selenium或Playwright）
- 编写性能测试（使用locust）
- 编写安全测试（检查密码、权限、SQL注入）
- 配置CI/CD集成测试

**前置条件:**
- 所有功能Story已完成（9.0-9.11）
- 测试框架已配置（pytest、pytest-django、pytest-cov）

**依赖关系:**
- 依赖 所有前置Story（9.0-9.11）

**估算:**
- 3天

**DoD:**
- [ ] 单元测试覆盖率 > 80%（apps/proxy和core/ai_client）
- [ ] 模型测试完成（ProxyConfig、ProxyUsageLog）
- [ ] 服务层测试完成（ProxyManager、ProxyProvider）
- [ ] AI客户端测试完成（代理支持、降级逻辑）
- [ ] API测试完成（所有端点、权限、筛选）
- [ ] Celery任务测试完成（健康检查逻辑）
- [ ] 集成测试完成（代理配置→AI调用成功）
- [ ] E2E测试完成（Django Admin流程、前端流程）
- [ ] 性能测试完成（响应时间、并发支持）
- [ ] 安全测试完成（密码、权限、SQL注入）
- [ ] 测试覆盖率报告生成（HTML格式）
- [ ] 所有测试在CI/CD中通过
- [ ] 无已知严重Bug
- [ ] 测试代码符合PEP8规范
- [ ] 测试文档完整（README.md说明如何运行测试）

---

# Epic 9.5: SSH隧道代理（可选扩展）

**Epic描述:**
在Epic 9.0基础上，增加SSH隧道代理支持，允许管理员配置SSH隧道作为代理，用于跳板机访问内网API和高度加密传输。

**用户价值:**
- 支持企业内网跳板机场景
- 提供更高的加密安全性
- 支持动态端口分配
- 自动连接管理和重连

**FRs covered:**
- FR-SSH.1: SSH协议支持（跳板机）
- FR-SSH.2: SSH连接管理（单例模式）
- FR-SSH.3: SSH密钥管理
- FR-SSH.4: SSH状态监控
- FR-SSH.5: SSH自动重连

**工作量:** 4.5天（6个Story）

**前置条件:** Epic 9.0上线并获得用户反馈（>30%用户需要SSH OR 竞品压力 OR 关键客户需求）

**技术栈:**
- paramiko (SSH客户端库)
- 单例模式（连接管理）
- Local Port Forwarding（本地端口转发）
- 指数退避重连策略

---

## Story 9.13: SSH数据模型扩展

**用户故事:**
作为系统管理员，
我需要在ProxyConfig中增加SSH相关字段，
以便配置SSH隧道代理连接参数。

**验收标准:**

[场景1: 添加SSH协议选项]
Given ProxyProtocol枚举类型
When 添加SSH选项
Then ProxyProtocol.HTTP = 'http'
And ProxyProtocol.HTTPS = 'https'
And ProxyProtocol.SOCKS5 = 'socks5'
And ProxyProtocol.SSH = 'ssh'
And 枚举类型可在Django Admin和DRF序列化器中使用

[场景2: 添加SSH连接字段]
Given ProxyConfig模型
When 添加SSH相关字段
Then ssh_host字段存在（CharField，max_length=255，blank=True，default=''）
And ssh_port字段存在（IntegerField，blank=True，null=True）
And ssh_username字段存在（CharField，max_length=128，blank=True，default=''）
And ssh_key_path字段存在（CharField，max_length=512，blank=True，default=''）
And 所有字段仅当protocol=SSH时必填
And 字段验证逻辑正确（非SSH时可为空）

[场景3: SSH密钥路径验证]
Given ssh_key_path字段
When 验证SSH密钥路径
Then 检查文件是否存在（path.exists()）
And 检查文件权限（os.access(file, os.R_OK)）
And 检查文件格式（.pem或.key结尾）
And 无效路径抛出ValidationError
And 错误消息明确（"SSH密钥文件不存在或不可读: /path/to/key"）

[场景4: 数据库迁移]
Given 添加SSH字段到ProxyConfig模型
When 运行makemigrations
Then 生成迁移文件（如0015_add_ssh_fields.py）
And 迁移文件包含所有4个SSH字段
And 迁移文件包含ProxyProtocol.SSH枚举扩展
And 迁移文件可回滚
And 运行migrate成功，无数据丢失

[场景5: Django Admin界面显示]
Given Django Admin ProxyConfig表单
When protocol选择SSH
Then SSH相关字段显示（ssh_host、ssh_port、ssh_username、ssh_key_path）
And protocol非SSH时，SSH字段隐藏
And SSH字段有清晰的label和help_text
And ssh_key_path字段使用FilePathInput或文件上传组件
And 表单验证正确触发

[场景6: DRF序列化器支持]
Given ProxyConfigSerializer
When 序列化SSH代理配置
Then 所有SSH字段包含在序列化器中
And 验证逻辑与模型一致
And SSH字段在响应中正确返回
And 密钥路径不暴露敏感信息（仅返回路径字符串）
And 错误处理正确

[场景7: 向后兼容性]
Given 现有ProxyConfig记录（protocol=HTTP/HTTPS/SOCKS5）
When 数据库迁移执行
Then 现有记录的SSH字段为空（blank=True默认值）
And 现有记录可正常编辑和保存
And 现有记录的API调用不受影响
And 无需修改现有代码

[场景8: 字段组合验证]
Given 创建SSH代理配置
When protocol=SSH但ssh_host为空
Then 模型clean()方法抛出ValidationError
And 错误消息"SSH协议必须配置ssh_host和ssh_port"
When protocol=SSH但ssh_port为空
Then 同样抛出ValidationError
When protocol=HTTP且SSH字段为空
Then 验证通过（SSH字段可选）

**技术实现要点:**
- 扩展ProxyProtocol枚举（使用models.TextChoices或django-enumfields）
- 添加4个SSH字段到ProxyConfig模型（blank=True，允许非SSH协议为空）
- 实现模型clean()方法验证字段组合（protocol=SSH时SSH字段必填）
- 实现ssh_key_path自定义验证器（检查文件存在性和权限）
- 生成并运行Django迁移
- 更新ProxyConfigAdmin（SSH字段条件显示）
- 更新ProxyConfigSerializer（添加SSH字段）
- 编写单元测试（模型验证、迁移、Admin、序列化器）

**前置条件:**
- Epic 9.0完成（ProxyConfig模型存在）
- paramiko库已安装（Story 9.0依赖）

**依赖关系:**
- 依赖 Epic 9.0

**估算:**
- 0.5天

**DoD:**
- [ ] ProxyProtocol.SSH枚举添加完成
- [ ] 4个SSH字段添加到ProxyConfig模型
- [ ] 模型clean()方法实现字段组合验证
- [ ] ssh_key_path自定义验证器实现
- [ ] 数据库迁移文件生成并执行成功
- [ ] Django Admin支持SSH字段显示和验证
- [ ] DRF序列化器支持SSH字段
- [ ] 向后兼容性测试通过（现有记录不受影响）
- [ ] 单元测试覆盖率 > 85%
- [ ] 代码符合PEP8规范

---

## Story 9.14: 简化SSH连接管理器

**用户故事:**
作为系统，
我需要实现SimpleSSHTunnelManager（单例模式），
以便统一管理SSH隧道连接的建立、维护和关闭。

**验收标准:**

[场景1: 单例模式实现]
Given SimpleSSHTunnelManager类
When 多次调用SimpleSSHTunnelManager.get_instance(proxy_config_id)
Then 返回相同的实例（id()相同）
And 每个proxy_config_id对应唯一实例
And 使用线程安全的单例实现（如__new__方法或线程锁）

[场景2: 建立SSH连接]
Given proxy_config_id=5（SSH代理配置）
When 调用manager.connect()
Then 使用paramiko.SSHClient()建立连接
And 连接参数从ProxyConfig读取（ssh_host、ssh_port、ssh_username、ssh_key_path）
And 使用ssh_key_path私钥认证（RSA或ECDSA密钥）
And 连接成功后设置self.client和self.is_connected=True
And 连接失败抛出SSHConnectionError
And 连接超时设置为10秒

[场景3: Local Port Forwarding]
Given SSH连接已建立
When 调用manager.create_tunnel(local_port, remote_host, remote_port)
Then 使用client.get_transport().request_port_forward()建立隧道
And local_port绑定到本地端口（如8080）
And remote_host:remote_port映射到远程目标
And 隧道创建成功返回True
And 隧道创建失败抛出SSHTunnelError
And local_port冲突时自动选择可用端口（动态端口分配）

[场景4: 获取代理URL]
Given SSH隧道已建立（local_port=8080）
When 调用manager.get_proxy_url()
Then 返回"http://127.0.0.1:8080"（SOCKS5代理）
或返回"socks5://127.0.0.1:8080"（SOCKS5代理）
And URL格式符合httpx代理规范
And 隧道未建立时返回None

[场景5: 关闭SSH连接]
Given SSH连接已建立
When 调用manager.close()
Then 关闭Local Port Forwarding（取消端口转发）
And 关闭SSH客户端连接（client.close()）
And 设置self.client=None和self.is_connected=False
And 连接关闭后无法再使用get_proxy_url()（返回None）
And 重复调用close()不抛出异常（幂等性）

[场景6: 简单重连机制]
Given SSH连接已断开（is_connected=False）
When 调用manager.reconnect(max_retries=3)
Then 尝试重新建立SSH连接（调用connect()）
And 重试最多3次（max_retries参数）
And 重试间隔使用指数退避（1秒、2秒、4秒）
And 重试成功返回True并设置is_connected=True
And 重试失败返回False并抛出SSHConnectionError
And 使用time.sleep()实现退避间隔

[场景7: 连接状态查询]
Given SimpleSSHTunnelManager实例
When 查询manager.is_connected
Then 返回当前连接状态（True/False）
And 连接建立后立即更新状态
And 连接断开后立即更新状态
And 状态查询无副作用

[场景8: 异常处理]
Given SSH连接建立过程
When 发生异常（AuthenticationException、SSHException、SocketError）
Then 捕获异常并转换为SSHConnectionError
And 记录详细错误日志（包含proxy_config_id、异常类型、消息）
And 设置is_connected=False
And 不影响其他proxy_config_id的连接

[场景9: 资源清理]
Given SimpleSSHTunnelManager实例
When Python解释器关闭或实例销毁
Then __del__()方法自动调用close()
And SSH连接正确关闭
And 无资源泄漏（文件描述符、Socket连接）
And 使用atexit.register()注册全局清理函数

[场景10: 并发安全]
Given 多个线程同时访问同一proxy_config_id的Manager
When 并发调用connect()、get_proxy_url()、close()
then 使用线程锁（threading.Lock()）保护关键操作
And 同一时刻只有一个线程执行连接建立
And 并发调用close()不会抛出异常
And 线程安全测试通过（使用pytest+多线程）

**技术实现要点:**
- 创建core/proxy/ssh_tunnel.py模块
- 实现SimpleSSHTunnelManager类（单例模式，使用__new__或模块级字典）
- 使用paramiko.SSHClient()建立SSH连接
- 使用SSHClient.connect()方法（hostname、port、username、key_filename参数）
- 实现Local Port Forwarding（Transport.request_port_forward()）
- 实现简单重连机制（指数退避，max_retries=3）
- 使用threading.Lock()保证并发安全
- 实现异常处理（捕获paramiko异常，转换为自定义异常）
- 实现资源清理（__del__ + atexit.register）
- 编写单元测试（Mock paramiko，测试连接、隧道、重连、并发）

**前置条件:**
- Story 9.13已完成（SSH数据模型可用）
- paramiko库已安装

**依赖关系:**
- 依赖 Story 9.13

**估算:**
- 1天

**DoD:**
- [ ] SimpleSSHTunnelManager类实现完成
- [ ] 单例模式实现正确（线程安全）
- [ ] SSH连接建立功能正确（使用paramiko）
- [ ] Local Port Forwarding功能正确
- [ ] 简单重连机制实现（指数退避，最多3次）
- [ ] 异常处理完整（SSHConnectionError、SSHTunnelError）
- [ ] 资源清理实现（__del__、atexit）
- [ ] 并发安全保证（threading.Lock）
- [ ] 单元测试覆盖率 > 85%
- [ ] 代码符合SOLID原则（单一职责、开闭原则）
- [ ] 代码符合PEP8规范
- [ ] docstring完整（类和方法）

---

## Story 9.15: SSH隧道代理提供者

**用户故事:**
作为系统，
我需要实现SSHTunnelProvider策略类，
以便ProxyManager可以统一管理SSH隧道代理。

**验收标准:**

[场景1: SSHTunnelProvider类结构]
Given SSHTunnelProvider类
When 类定义完成
Then 继承自ProxyProvider抽象基类
And 实现get_proxy()方法（返回代理URL或None）
And 实现record_usage()方法（记录使用日志）
And __init__接收proxy_config参数
And 遵循策略模式设计

[场景2: get_proxy() - 隧道已建立]
Given proxy_config.protocol=SSH
And SSH隧道已建立（local_port=8080）
When 调用provider.get_proxy()
Then 返回"socks5://127.0.0.1:8080"（SOCKS5代理URL）
And URL格式符合httpx代理规范
And 不重复建立隧道（复用现有连接）
And 不触发重连（连接正常）

[场景3: get_proxy() - 隧道未建立]
Given proxy_config.protocol=SSH
And SSH隧道未建立（is_connected=False）
When 调用provider.get_proxy()
Then 自动调用manager.connect()建立隧道
Then 创建Local Port Forwarding（动态分配端口）
Then 返回"socks5://127.0.0.1:{动态端口}"
And 隧道建立失败时返回None（触发降级）
And 记录错误日志

[场景4: get_proxy() - 连接失败时重连]
Given SSH隧道已断开（is_connected=False）
When 调用provider.get_proxy()
Then 调用manager.reconnect(max_retries=3)
And 重试成功返回代理URL
And 重试失败返回None（降级）
And 重试间隔使用指数退避

[场景5: record_usage() - 记录使用日志]
Given SSH代理调用成功（success=True, response_time=300ms）
When 调用provider.record_usage(...)
Then ProxyUsageLog创建一条记录
And proxy字段正确关联到ProxyConfig
And success=True, response_time_ms=300
And ai_provider和endpoint正确记录
And ProxyConfig.last_used_at更新
And 记录SSH特定信息（如is_connected状态）

[场景6: ProxyManager集成]
Given proxy_config.protocol=SSH
When 调用ProxyManager.get_provider(proxy_config.id)
Then 返回SSHTunnelProvider实例
And provider.proxy_config正确指向SSH配置
And provider.ssh_manager是SimpleSSHTunnelManager实例
And Manager使用单例模式（同一proxy_config_id共享实例）

[场景7: 降级策略集成]
Given SSH代理失败（get_proxy()返回None）
When AI客户端调用降级逻辑
Then 自动降级到NoProxyProvider（直连）
And 记录降级事件到日志
And ProxyUsageLog记录success=False
And 错误消息包含"SSH tunnel failed, falling back to direct connection"

[场景8: 资源清理]
Given SSHTunnelProvider实例销毁
When Python垃圾回收触发
Then __del__()方法调用ssh_manager.close()
And SSH连接正确关闭
And 无资源泄漏
And 使用weakref.finalize作为备选清理机制

[场景9: 多SSH代理支持]
Given 两个不同的SSH代理配置（id=5和id=6）
When 同时使用两个代理
Then 返回两个不同的SSHTunnelProvider实例
And 两个实例使用不同的SimpleSSHTunnelManager
And 两个SSH隧道独立管理（不同端口）
And 互不干扰（连接状态、资源清理）

[场景10: 错误处理]
Given SSH代理配置有误（ssh_key_path无效）
When 调用provider.get_proxy()
Then 捕获SSHConnectionError
And 返回None（降级）
And 记录详细错误日志（包含proxy_config.id、错误原因）
And 不抛出未捕获异常
And AI调用流程继续（降级到直连）

**技术实现要点:**
- 创建core/proxy/providers/ssh_tunnel_provider.py
- 实现SSHTunnelProvider类（继承ProxyProvider）
- 集成SimpleSSHTunnelManager（单例管理）
- 实现get_proxy()方法（自动建立隧道、返回代理URL）
- 实现record_usage()方法（复用ProxyProvider基类逻辑）
- 实现降级策略（返回None触发降级）
- 实现资源清理（__del__ + weakref.finalize）
- 更新ProxyManager.get_provider()工厂方法（支持protocol=SSH）
- 更新BaseAIClient._get_httpx_config()（支持SOCKS5代理URL）
- 编写单元测试（Mock SimpleSSHTunnelManager，测试get_proxy、record_usage、降级）

**前置条件:**
- Story 9.13已完成（SSH数据模型）
- Story 9.14已完成（SimpleSSHTunnelManager）

**依赖关系:**
- 依赖 Story 9.13
- 依赖 Story 9.14

**估算:**
- 1天

**DoD:**
- [ ] SSHTunnelProvider类实现完成
- [ ] get_proxy()方法实现正确（自动建立隧道、返回URL）
- [ ] record_usage()方法实现正确
- [ ] ProxyManager集成完成（支持protocol=SSH）
- [ ] 降级策略集成（SSH失败→降级到直连）
- [ ] 资源清理实现（__del__、weakref.finalize）
- [ ] 多SSH代理支持（独立隧道管理）
- [ ] 单元测试覆盖率 > 85%
- [ ] BaseAIClient支持SOCKS5代理URL
- [ ] 代码符合SOLID原则
- [ ] 代码符合PEP8规范
- [ ] docstring完整

---

## Story 9.16: SSH状态监控

**用户故事:**
作为系统管理员，
我需要在Django Admin中监控SSH连接状态，
以便实时了解SSH隧道的可用性并手动操作连接。

**验收标准:**

[场景1: Admin列表显示SSH状态]
Given Django Admin ProxyConfig列表页
When 存在SSH代理配置
Then list_display添加get_ssh_status方法
And 显示SSH连接状态（已连接✅/未连接❌/错误⚠️）
And 状态badge颜色区分（绿色/红色/黄色）
And 状态实时更新（每次请求查询SimpleSSHTunnelManager）

[场景2: SSH状态查询方法]
Given ProxyConfigAdmin
When 调用get_ssh_status(proxy_config)
Then protocol非SSH时返回"-"（不适用）
Then protocol=SSH时查询SimpleSSHTunnelManager.is_connected
Then 返回"已连接"（is_connected=True，绿色badge）
Then 返回"未连接"（is_connected=False，红色badge）
Then 返回"错误"（manager实例不存在或异常，黄色badge）

[场景3: Admin详情页SSH信息]
Given Django Admin ProxyConfig详情页
When 查看SSH代理配置
Then 显示SSH连接详细信息
And 包括：ssh_host、ssh_port、ssh_username、ssh_key_path
And 包括：当前SSH状态（已连接/未连接）
And 包括：Local Port Forwarding端口（如已连接）
And 包括：最后连接时间（last_connected_at字段，需添加）

[场景4: 手动重连操作]
Given SSH代理配置（is_connected=False）
When 在Admin详情页点击"重连SSH"按钮
Then 调用admin_action_reconnect_ssh(request, proxy_config)
Then 执行ssh_manager.reconnect(max_retries=3)
Then 重连成功显示成功消息（"SSH连接已建立"）
Then 重连失败显示错误消息（"SSH连接失败: {错误原因}"）
Then 刷新页面显示最新状态

[场景5: 手动断开操作]
Given SSH代理配置（is_connected=True）
When 在Admin详情页点击"断开SSH"按钮
Then 调用admin_action_disconnect_ssh(request, proxy_config)
Then 执行ssh_manager.close()
Then 连接关闭成功显示成功消息（"SSH连接已关闭"）
Then 刷新页面显示"未连接"状态

[场景6: SSH连接错误日志]
Given SSH连接失败或异常
When 在Admin详情页查看
Then 显示最近错误信息（error_message字段，需添加）
Then 包括错误时间（error_occurred_at字段，需添加）
Then 错误信息最多显示1000字符（截断超长日志）
Then 错误信息支持HTML格式（<pre>标签保留格式）
Then 提供"清除错误日志"按钮

[场景7: 批量操作支持]
Given Django Admin ProxyConfig列表页
When 勾选多个SSH代理配置
Then actions菜单显示"批量重连SSH"选项
Then 执行后遍历所有勾选的SSH配置并重连
Then 显示汇总消息（"成功重连3个，失败1个: {原因}"）
Then 失败的配置不影响其他配置的重连

[场景8: SSH字段添加到模型]
Given ProxyConfig模型
When 添加SSH状态监控字段
Then last_connected_at字段存在（DateTimeField，blank=True，null=True）
Then error_message字段存在（TextField，blank=True，default=''）
Then error_occurred_at字段存在（DateTimeField，blank=True，null=True）
Then 字段在SSH连接建立/失败时自动更新
Then 数据库迁移成功执行

[场景9: SSH状态自动更新]
Given SSH代理配置
When SSH连接成功建立
Then last_connected_at更新为当前时间
And error_message清空
And error_occurred_at清空
When SSH连接失败
Then error_message记录错误信息（最多1000字符）
Then error_occurred_at更新为当前时间
And last_connected_at不变

[场景10: 权限控制]
Given Django Admin
When 非管理员用户访问
Then "重连SSH"和"断开SSH"按钮不可见（或禁用）
Then 普通用户只能查看SSH状态，无法操作
Then 使用has_change_permission()控制按钮显示

**技术实现要点:**
- 扩展ProxyConfig模型（添加last_connected_at、error_message、error_occurred_at字段）
- 更新ProxyConfigAdmin（添加get_ssh_status方法、自定义按钮）
- 实现admin_action_reconnect_ssh()方法（调用ssh_manager.reconnect）
- 实现admin_action_disconnect_ssh()方法（调用ssh_manager.close）
- 实现admin_action_bulk_reconnect_ssh()方法（批量操作）
- 更新SimpleSSHTunnelManager（连接成功/失败时更新模型字段）
- 自定义Admin模板（详情页添加SSH信息面板、操作按钮）
- 配置Admin权限控制（is_staff检查）
- 编写集成测试（Admin操作、状态显示、按钮功能）

**前置条件:**
- Story 9.13已完成（SSH数据模型）
- Story 9.14已完成（SimpleSSHTunnelManager）
- Story 9.15已完成（SSHTunnelProvider）

**依赖关系:**
- 依赖 Story 9.13
- 依赖 Story 9.14
- 依赖 Story 9.15

**估算:**
- 0.5天

**DoD:**
- [ ] ProxyConfig模型添加3个SSH状态字段
- [ ] 数据库迁移成功执行
- [ ] ProxyConfigAdmin添加get_ssh_status()方法
- [ ] Admin列表页显示SSH状态badge
- [ ] Admin详情页显示SSH详细信息
- [ ] "重连SSH"按钮实现并测试
- [ ] "断开SSH"按钮实现并测试
- [ ] "批量重连SSH"操作实现并测试
- [ ] SimpleSSHTunnelManager更新模型字段
- [ ] 权限控制实现（is_staff检查）
- [ ] 集成测试通过（Admin操作流程）
- [ ] 代码符合PEP8规范

---

## Story 9.17: SSH测试

**用户故事:**
作为开发团队，
我需要为SSH隧道功能编写完整的测试套件，
以便确保SSH功能的可靠性和稳定性。

**验收标准:**

[场景1: 单元测试 - SimpleSSHTunnelManager]
Given SimpleSSHTunnelManager类
When 运行单元测试
then Mock paramiko.SSHClient
And 测试单例模式（多个get_instance()调用返回相同实例）
And 测试SSH连接建立（connect()方法）
And 测试Local Port Forwarding（create_tunnel()方法）
And 测试代理URL生成（get_proxy_url()方法）
And 测试连接关闭（close()方法）
And 测试重连机制（reconnect()方法，指数退避）
And 测试异常处理（AuthenticationException、SSHException）
And 覆盖率 > 90%

[场景2: 单元测试 - SSHTunnelProvider]
Given SSHTunnelProvider类
When 运行单元测试
Then Mock SimpleSSHTunnelManager
And 测试get_proxy()方法（隧道已建立、未建立、失败场景）
And 测试record_usage()方法（复用基类逻辑）
And 测试降级策略（返回None触发降级）
And 测试资源清理（__del__方法）
And 测试多SSH代理支持（不同proxy_config_id）
And 覆盖率 > 90%

[场景3: 集成测试 - 真实SSH服务器]
Given 真实SSH服务器环境（如Docker容器）
When 运行集成测试
Then 使用真实paramiko库（不Mock）
And 测试完整SSH连接流程（连接→隧道→代理URL）
And 测试SSH密钥认证（使用测试密钥）
And 测试Local Port Forwarding（端口转发成功）
And 测试httpx通过SOCKS5代理发起请求
And 测试连接断开后重连
And 使用pytest fixture设置和清理SSH服务器

[场景4: 连接泄漏测试]
Given SimpleSSHTunnelManager
When 运行连接泄漏测试
Then 创建100个SSH连接（不同proxy_config_id）
Then 关闭所有连接
Then 检查系统资源（文件描述符、Socket连接）
then 确认无资源泄漏（lsof或/proc/{pid}/fd）
And 所有连接正确关闭（is_connected=False）
And 使用pytest-benchmark监控内存使用

[场景5: 并发安全测试]
Given SimpleSSHTunnelManager单例
When 运行并发安全测试
Then 使用10个线程同时调用connect()
Then 使用线程锁保证串行化执行
then 同一时刻只有一个线程建立连接
And 连接建立成功后，其他线程复用连接
And 使用pytest-xdist并发执行测试
And 无竞态条件和死锁

[场景6: SSH模型测试]
Given ProxyConfig模型SSH扩展
When 运行模型测试
Then 测试ProxyProtocol.SSH枚举值
And 测试SSH字段验证（protocol=SSH时必填）
And 测试ssh_key_path验证器（文件存在性、权限）
And 测试模型clean()方法（字段组合验证）
And 测试向后兼容性（现有记录不受影响）
And 覆盖率 > 85%

[场景7: SSH Admin测试]
Given ProxyConfigAdmin SSH功能
When 运行Admin测试
then 测试get_ssh_status()方法（不同状态badge）
And 测试admin_action_reconnect_ssh()（重连操作）
And 测试admin_action_disconnect_ssh()（断开操作）
And 测试admin_action_bulk_reconnect_ssh()（批量操作）
And 测试权限控制（普通用户无操作权限）
And 使用Django test client模拟Admin请求
And 覆盖率 > 80%

[场景8: 混沌测试 - SSH故障注入]
Given SSH代理正常运行
When 运行混沌测试
then 模拟SSH服务器故障（kill SSH进程）
then 模拟网络中断（iptables drop）
And 模拟密钥文件删除
And 模拟端口冲突（local_port占用）
And 验证系统行为（降级到直连、错误日志、重连机制）
And 使用pytest + subprocess模拟故障场景

[场景9: 性能测试 - SSH开销]
Given SSH隧道代理
When 运行性能测试
then 测试SSH连接建立时间（< 2秒）
And 测试代理URL生成时间（< 10ms）
And 测试AI调用额外延迟（< 200ms，SSH隧道开销）
And 测试并发SSH连接（10个并发）
And 使用pytest-benchmark记录性能指标
And 确认性能可接受

[场景10: 测试报告]
Given 所有SSH测试执行完成
When 生成测试报告
then HTML报告显示SSH模块覆盖率
And 报告包含单元测试、集成测试、混沌测试结果
And 报告包含性能测试基准数据
And 报告包含失败测试的详细错误信息
And 使用pytest-html或allure生成报告

**技术实现要点:**
- 创建apps/proxy/tests/test_ssh_manager.py（单元测试）
- 创建apps/proxy/tests/test_ssh_provider.py（单元测试）
- 创建apps/proxy/tests/integration/test_ssh_integration.py（集成测试）
- 创建apps/proxy/tests/test_chaos_ssh.py（混沌测试）
- 使用pytest-mock Mock paramiko
- 使用pytest fixture设置测试SSH服务器（Docker或paramiko.TestServer）
- 使用pytest-benchmark进行性能测试
- 使用pytest-cov测量覆盖率
- 使用pytest-asyncio测试异步代码（如适用）
- 配置CI/CD集成测试（GitHub Actions或GitLab CI）

**前置条件:**
- Story 9.13已完成（SSH数据模型）
- Story 9.14已完成（SimpleSSHTunnelManager）
- Story 9.15已完成（SSHTunnelProvider）
- Story 9.16已完成（SSH状态监控）

**依赖关系:**
- 依赖 所有SSH功能Story（9.13-9.16）

**估算:**
- 1天

**DoD:**
- [ ] 单元测试完成（SimpleSSHTunnelManager、SSHTunnelProvider）
- [ ] 集成测试完成（真实SSH服务器）
- [ ] 连接泄漏测试通过
- [ ] 并发安全测试通过
- [ ] 混沌测试完成（故障注入）
- [ ] 性能测试完成（基准数据）
- [ ] SSH模型测试完成
- [ ] SSH Admin测试完成
- [ ] 测试覆盖率 > 85%（SSH模块整体）
- [ ] 测试报告生成（HTML格式）
- [ ] 所有测试在CI/CD中通过
- [ ] 测试代码符合PEP8规范
- [ ] 测试文档完整（README.md说明如何运行SSH测试）

---

## Story 9.18: SSH文档

**用户故事:**
作为系统管理员和开发者，
我需要完整的SSH代理配置文档，
以便独立配置和使用SSH隧道代理功能。

**验收标准:**

[场景1: SSH功能概述文档]
Given docs/proxy/SSH_OVERVIEW.md
When 查看文档
Then 包含SSH隧道代理简介（什么是SSH隧道、应用场景）
And 包含功能特性列表（支持跳板机、动态端口、自动重连）
And 包含技术架构图（Mermaid图表）
And 包含与Epic 9.0的关系说明（依赖关系）
And 包含适用场景和限制说明

[场景2: SSH密钥生成指南]
Given docs/proxy/SSH_KEY_GENERATION.md
When 查看文档
Then 包含SSH密钥生成步骤（ssh-keygen命令）
Then 包含RSA和ECDSA密钥生成示例
And 包含密钥权限设置（chmod 600）
And 包含密钥格式要求（OpenSSH格式、.pem/.key）
And 包含常见错误排查（权限拒绝、格式不匹配）
And 包含密钥安全最佳实践（不提交到Git、强密码保护）

[场景3: 部署配置文档]
Given docs/proxy/SSH_DEPLOYMENT.md
When 查看文档
Then 包含Django设置配置（PROXY_SSH_KEY_BASE_PATH）
And 包含paramiko依赖安装（pip install paramiko）
And 包含系统依赖安装（ssh-client、openssh）
And 包含文件权限配置（Django进程读取密钥文件）
And 包含防火墙规则配置（SSH端口、本地端口）
And 包含Docker部署配置（密钥卷挂载、环境变量）

[场景4: Admin操作指南]
Given docs/proxy/SSH_ADMIN_GUIDE.md
When 查看文档
Then 包含Django Admin配置SSH代理步骤（截图或GIF）
And 包含字段说明（ssh_host、ssh_port、ssh_username、ssh_key_path）
And 包含SSH状态监控说明（已连接/未连接/错误badge）
And 包含手动重连/断开操作说明
And 包含批量操作说明
And 包含常见错误处理（连接失败、密钥错误、端口冲突）

[场景5: 故障排查手册]
Given docs/proxy/SSH_TROUBLESHOOTING.md
When 查看文档
Then 包含常见错误和解决方案（表格形式）
And 包含SSH连接失败排查步骤（检查清单）
And 包含密钥问题排查（权限、格式、路径）
And 包含端口冲突排查（netstat、lsof命令）
And 包含日志查看指南（Django日志、paramiko日志）
And 包含调试技巧（开启DEBUG、详细日志、Mock测试）

[场景6: API使用文档]
Given docs/proxy/SSH_API.md
When 查看文档
Then 包含SSH代理配置API示例（POST /api/v1/proxy/）
And 包含protocol=SSH请求体示例（JSON）
And 包含前端代理选择器使用说明（Vue组件）
And 包含AI客户端调用示例（通过SSH隧道）
And 包含错误处理示例（降级、超时、认证失败）
And 包含代码片段（Python、JavaScript）

[场景7: 性能和安全文档]
Given docs/proxy/SSH_PERFORMANCE_SECURITY.md
When 查看文档
Then 包含性能基准数据（连接建立时间、额外延迟）
And 包含性能优化建议（连接复用、并发限制）
And 包含安全最佳实践（密钥保护、权限控制、日志脱敏）
And 包含安全风险说明（私钥泄露、SSH劫持）
And 包含审计日志配置（记录SSH操作）
And 包含合规性要求（如SOC2、ISO27001）

[场景8: 开发者文档]
Given docs/proxy/SSH_DEVELOPER.md
When 查看文档
Then 包含代码结构说明（core/proxy/ssh_tunnel.py、providers/）
And 包含类和方法说明（SimpleSSHTunnelManager、SSHTunnelProvider）
And 包含设计模式说明（单例模式、策略模式）
And 包含扩展开发指南（如何添加新功能）
And 包含测试指南（如何运行SSH测试）
And 包含代码示例（自定义SSH Provider）

[场景9: FAQ文档]
Given docs/proxy/SSH_FAQ.md
When 查看文档
Then 包含常见问题列表（10-15个）
And 包含问题和答案（简洁明了）
And 包含交叉引用（指向详细文档）
And 包含搜索功能（如使用文档搜索工具）
And 问题示例：SSH和HTTP代理有什么区别？如何配置跳板机？为什么连接失败？

[场景10: 文档集成和导航]
Given 所有SSH文档
When 查看文档首页
Then 包含文档索引（所有SSH文档链接）
And 包含导航结构（面包屑、侧边栏）
And 包含快速开始指南（5分钟配置SSH代理）
And 文档使用Markdown格式（支持GitHub、GitBook、Docusaurus）
And 包含图表和截图（Mermaid图表、Admin界面截图）
And 文档中英文双语（可选）

**技术实现要点:**
- 创建docs/proxy/目录（如不存在）
- 创建8个SSH文档文件（Markdown格式）
- 使用Mermaid绘制架构图（SSH隧道连接图、组件关系图）
- 编写代码示例（Python、JavaScript、Bash）
- 插入截图或GIF（Django Admin操作、前端界面）
- 配置文档导航（MKDocs、Docusaurus或GitBook）
- 编写快速开始指南（step-by-step教程）
- 编写FAQ（收集常见问题）
- 文档review（技术写作优化）

**前置条件:**
- 所有SSH功能Story已完成（9.13-9.17）
- SSH功能已测试并验证

**依赖关系:**
- 依赖 所有SSH功能Story（9.13-9.17）

**估算:**
- 0.5天

**DoD:**
- [ ] SSH_OVERVIEW.md创建完成
- [ ] SSH_KEY_GENERATION.md创建完成
- [ ] SSH_DEPLOYMENT.md创建完成
- [ ] SSH_ADMIN_GUIDE.md创建完成
- [ ] SSH_TROUBLESHOOTING.md创建完成
- [ ] SSH_API.md创建完成
- [ ] SSH_PERFORMANCE_SECURITY.md创建完成
- [ ] SSH_DEVELOPER.md创建完成
- [ ] SSH_FAQ.md创建完成
- [ ] 文档索引和导航配置完成
- [ ] 快速开始指南完成
- [ ] 文档包含Mermaid图表和截图
- [ ] 文档包含代码示例
- [ ] 文档review完成（无错别字、格式统一）
- [ ] 文档发布到文档站点（如GitBook、内部Wiki）

---

## 附录：Epic 9.5成功标准

### 功能完整性
- ✅ 所有6个Story完成并验证
- ✅ Django Admin可以配置SSH隧道代理
- ✅ SSH隧道自动建立和维护
- ✅ SSH连接失败自动重连
- ✅ SSH状态监控和手动操作

### 质量门禁
- ✅ 单元测试覆盖率 > 85%（SSH模块）
- ✅ 集成测试完成（真实SSH服务器）
- ✅ 连接泄漏测试通过
- ✅ 并发安全测试通过
- ✅ 混沌测试完成（故障注入）
- ✅ 0个严重Bug（资源泄漏、安全漏洞、系统崩溃）

### 性能标准
- ✅ SSH连接建立时间 < 2秒
- ✅ AI调用额外延迟 < 200ms（SSH隧道开销）
- ✅ 并发SSH连接支持（10个并发）
- ✅ 无资源泄漏（文件描述符、Socket连接）

### 文档完整性
- ✅ SSH功能概述文档
- ✅ SSH密钥生成指南
- ✅ 部署配置文档
- ✅ Admin操作指南
- ✅ 故障排查手册
- ✅ API使用文档
- ✅ 性能和安全文档
- ✅ 开发者文档
- ✅ FAQ文档

---

## 附录：Story依赖关系图（Epic 9.5）

```mermaid
graph TD
    Story9.0[Story 9.0<br/>基础设施准备] --> Story9.13[Story 9.13<br/>SSH数据模型扩展]
    Story9.13 --> Story9.14[Story 9.14<br/>SSH连接管理器]
    Story9.14 --> Story9.15[Story 9.15<br/>SSH隧道代理提供者]
    Story9.15 --> Story9.16[Story 9.16<br/>SSH状态监控]
    Story9.16 --> Story9.17[Story 9.17<br/>SSH测试]
    Story9.17 --> Story9.18[Story 9.18<br/>SSH文档]
```

**依赖说明:**
- Epic 9.5完全依赖Epic 9.0的基础设施（Story 9.0）
- Epic 9.5内部Story线性依赖（9.13 → 9.14 → 9.15 → 9.16 → 9.17 → 9.18）

---

## 附录：Epic 9.5决策触发条件

**决策条件（满足任一即执行Epic 9.5）:**
1. **用户反馈**: >30%的Epic 9.0用户需要SSH隧道功能
2. **竞品压力**: 竞争对手支持SSH隧道且成为卖点
3. **关键客户需求**: 关键客户或大客户明确要求SSH支持
4. **安全合规**: 企业客户要求SSH加密传输（如金融、政府）

**决策时间点:**
- Epic 9.0上线后14天
- 收集和分析用户反馈
- 举行Go/No-Go决策会议

**如果决定不执行Epic 9.5:**
- 继续监控用户反馈
- 每季度重新评估需求
- 优先考虑其他Epic

---

**文档版本:** 2.0
**创建日期:** 2026-01-30
**最后更新:** 2026-01-30
**状态:** Ready for Implementation
**Epic 9.0估算:** 15天
**Epic 9.5估算:** 4.5天（可选）

---

## 附录：Story依赖关系图

```mermaid
graph TD
    Story9_0[Story 9.0: 基础设施准备] --> Story9_1[Story 9.1: ProxyConfig模型]
    Story9_1 --> Story9_2[Story 9.2: ProxyUsageLog模型]
    Story9_1 --> Story9_3[Story 9.3: ProxyManager]
    Story9_2 --> Story9_3
    Story9_3 --> Story9_4[Story 9.4: SingleProxyProvider]
    Story9_3 --> Story9_5[Story 9.5: 代理降级逻辑]
    Story9_4 --> Story9_5
    Story9_4 --> Story9_6[Story 9.6: BaseAIClient代理支持]
    Story9_5 --> Story9_6
    Story9_1 --> Story9_7[Story 9.7: Project proxy_id外键]
    Story9_1 --> Story9_8[Story 9.8: 前端代理选择器]
    Story9_7 --> Story9_8
    Story9_1 --> Story9_9[Story 9.9: 测试连接功能]
    Story9_2 --> Story9_9
    Story9_1 --> Story9_10[Story 9.10: Celery Beat健康检查]
    Story9_2 --> Story9_10
    Story9_0[Story 9.0-9.10全部完成] --> Story9_11[Story 9.11: 文档和部署指南]
    Story9_0[Story 9.0-9.11全部完成] --> Story9_12[Story 9.12: 单元测试+集成测试+E2E测试]
```

---

## 附录：Epic 9.0成功标准

### 功能完整性
- ✅ 所有13个Story完成并验证
- ✅ Django Admin可以管理代理配置
- ✅ 前端可以选择代理
- ✅ AI客户端可以使用代理
- ✅ 代理失败自动降级
- ✅ Celery Beat定时健康检查

### 质量门禁
- ✅ 单元测试覆盖率 > 80%
- ✅ 集成测试覆盖核心路径
- ✅ E2E测试通过
- ✅ 0个严重Bug（数据丢失、安全漏洞、系统崩溃）
- ✅ 密码加密解密一致性 100%
- ✅ 向后兼容性测试通过

### 性能标准
- ✅ 代理测试连接响应时间 < 3秒
- ✅ AI调用额外延迟 < 100ms
- ✅ 健康检查任务内存占用 < 50MB
- ✅ 并发支持：100个并发请求

### 文档完整性
- ✅ 安装指南
- ✅ 配置指南
- ✅ 使用指南
- ✅ 故障排查指南
- ✅ API文档
- ✅ 部署清单
- ✅ 安全指南

---

**文档版本:** 2.0
**创建日期:** 2026-01-30
**最后更新:** 2026-01-30
**状态:** Ready for Implementation
**Epic 9.0估算:** 15天（13个Story）
**Epic 9.5估算:** 4.5天（6个Story，可选）
**总计:** 19.5天（19个Story）

---

## 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| 1.0 | 2026-01-30 | Epic 9.0初始版本（13个Story） | BMAD |
| 2.0 | 2026-01-30 | 添加Epic 9.5（6个SSH隧道Story） | BMAD |

---

## Epic总览

### Epic 9.0: 多协议代理管理（MVP）
- **Story数量:** 13个（9.0-9.12）
- **工作量:** 15天
- **协议支持:** HTTP、HTTPS、SOCKS5
- **状态:** ✅ Ready for Implementation

### Epic 9.5: SSH隧道代理（可选扩展）
- **Story数量:** 6个（9.13-9.18）
- **工作量:** 4.5天
- **协议支持:** SSH隧道（跳板机）
- **状态:** ⏸️ 待Epic 9.0上线后决策

### Epic决策流程
```
Epic 9.0上线（Day 14）
         ↓
   收集用户反馈（Day 14-21）
         ↓
   决策会议（Day 21）
         ↓
    [满足条件?] ──Yes──> 执行Epic 9.5
         │ No
         ↓
   继续监控反馈
```

---
