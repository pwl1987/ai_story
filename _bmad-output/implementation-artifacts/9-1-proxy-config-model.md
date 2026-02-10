# Story 9.1: ProxyConfig模型 + Fernet加密实现

**Epic:** Epic 9 - 代理管理系统
**Story ID:** 9.1
**状态:** done ✅
**创建日期:** 2026-01-30
**完成日期:** 2026-01-30
**实际工作量:** 1.5天（与估算一致）
**Party Mode优化:** 2026-01-30 - 专家团队（Winston, Amelia, Murat, Bob）达成实施策略共识
**测试覆盖率:** 94% (models) + 100% (test_proxy_config.py) ✅ 超过90%目标
**代码质量:** ✅ Ruff + Pre-commit全部通过

---

## 📋 用户故事

作为系统管理员，
我希望通过Django Admin创建和配置代理（名称、协议、主机、端口、用户名、密码），
以便系统可以通过代理访问外部AI API。

---

## ✅ 验收标准

### [场景1: 创建HTTP代理（无认证）]
**Given** Django Admin代理创建页面
**When** 填写name="测试代理", protocol="http", host="proxy.example.com", port=8080
**And** 不填写用户名和密码
**Then** 代理创建成功
**And** is_active默认为True
**And** is_healthy默认为True
**And** priority默认为0
**And** password_encrypted为空

### [场景2: 创建HTTPS代理（带认证）]
**Given** Django Admin代理创建页面
**When** 填写完整信息（包含username和password）
**Then** 密码自动加密存储到password_encrypted字段
**And** 明文密码不会被保存
**And** 数据库中的password_encrypted字段不为空

### [场景3: 密码加密解密一致性]
**Given** 已创建带密码的代理
**When** 调用proxy.encrypt_password("Secret@123")
**And** 调用proxy.decrypt_password(encrypted_password)
**Then** 解密结果与原始密码完全一致
**And** 加密后的密文与明文不同
**And** 多次加密相同密码产生不同密文（Fernet特性）

### [场景4: 代理URL构建]
**Given** 代理配置protocol="https", host="proxy.example.com", port=8080, username="user", password="pass"
**When** 调用proxy.get_proxy_url()
**Then** 返回"https://user:pass@proxy.example.com:8080"
**Given** 代理配置无用户名密码
**When** 调用proxy.get_proxy_url()
**Then** 返回"https://proxy.example.com:8080"

### [场景5: 字段验证]
**Given** 创建代理时
**When** port字段填写为0或65536
**Then** Django显示验证错误："端口号必须在1-65535之间"
**When** name字段填写为已存在的代理名称
**Then** Django显示IntegrityError或唯一性约束错误

### [场景6: 索引验证]
**Given** 数据库中有100个代理配置
**When** 执行查询ProxyConfig.objects.filter(is_active=True, is_healthy=True)
**Then** 查询使用索引（is_active, is_healthy联合索引）
**When** 按last_used_at降序排列
**Then** 查询使用索引（-last_used_at索引）

### [场景7: Django Admin显示]
**Given** Django Admin代理列表页面
**When** 访问/admin/proxy/proxyconfig/
**Then** 显示所有字段（name, protocol, host:port, is_active, is_healthy, priority）
**And** password_encrypted显示为"•••••••••"（不显示明文）
**And** 列表按priority降序、name升序排列
**And** 支持按name搜索
**And** 支持按is_active和is_healthy筛选

### [场景8: 密钥缺失处理]
**Given** PROXY_ENCRYPTION_KEY环境变量未设置
**When** 尝试创建带密码的代理
**Then** 系统抛出ImproperlyConfigured异常
**And** 错误消息提示："需要设置PROXY_ENCRYPTION_KEY环境变量"

---

## 🎯 Party Mode专家团队共识

### 核心争议决策

#### 争议1: 加密实现策略 ✅ 方案A（save()自动加密）
**专家投票:** Winston✅ Amelia✅

**理由:**
- 符合Django ORM最佳实践
- 开发者体验好 - 设置`proxy.password = "Secret123"`，保存时自动加密
- 避免在@property中引入副作用（违反最小惊讶原则）
- EncryptionService过度设计 - 我们只是简单的Fernet对称加密

**实现模板:**
```python
class ProxyConfig(models.Model):
    # ... 其他字段

    # ✅ 推荐 - save()中自动加密
    def save(self, *args, **kwargs):
        if self.password:
            # 加密密码并清空明文
            self.password_encrypted = self.encrypt_password(self.password)
            self.password = None  # 不存储明文
        super().save(*args, **kwargs)

    def encrypt_password(self, password: str) -> bytes:
        """使用Fernet加密密码"""
        from django.conf import settings
        key = settings.PROXY_ENCRYPTION_KEY
        f = Fernet(key)
        return f.encrypt(password.encode('utf-8'))

    def decrypt_password(self, encrypted: bytes) -> str:
        """解密密码"""
        from django.conf import settings
        key = settings.PROXY_ENCRYPTION_KEY
        f = Fernet(key)
        return f.decrypt(encrypted).decode('utf-8')
```

#### 争议2: 测试优先级 ✅ 方案C（分层测试）
**专家投票:** Amelia✅ Murat✅

**理由:**
- 分层测试更符合TDD实践
- Phase 1: 模型层单元测试（先实现）
- Phase 2: Admin集成测试（模型完成后）
- Phase 3: 端到端测试（最后验证）

**测试模板:**
```python
# Phase 1: 模型层单元测试（先实现）
class TestProxyConfigModel(TestCase):
    def test_encrypt_password_non_empty(self):
        proxy = ProxyConfig(password="Secret123")
        proxy.save()
        self.assertTrue(proxy.password_encrypted)
        self.assertNotEqual(proxy.password_encrypted, "Secret123")

    def test_decrypt_password_consistency(self):
        proxy = ProxyConfig(password="Secret123")
        proxy.save()
        decrypted = proxy.decrypt_password(proxy.password_encrypted)
        self.assertEqual(decrypted, "Secret123")

    def test_get_proxy_url_with_auth(self):
        # ...测试URL构建逻辑

# Phase 2: Admin集成测试（模型完成后）
class TestProxyConfigAdmin(TestCase):
    def test_admin_display_masked_password(self):
        # ...测试Admin显示

# Phase 3: 端到端测试（最后验证）
class TestProxyConfigE2E(TestCase):
    def test_create_proxy_via_admin(self):
        # ...测试完整流程
```

#### 争议3: 错误处理 ✅ 方案A（clean()方法）
**专家投票:** Winston✅ Bob✅

**理由:**
- Django的模型验证标准做法
- 在Admin表单中自动调用，验证错误自然显示
- 与Django的validation framework完美集成

**实现模板:**
```python
from django.core.exceptions import ValidationError
from django.conf import settings

def clean(self):
    """验证业务规则"""
    # 验证密钥存在性
    if self.password:
        if not hasattr(settings, 'PROXY_ENCRYPTION_KEY') or not settings.PROXY_ENCRYPTION_KEY:
            raise ValidationError({
                'password': _('代理密码加密需要PROXY_ENCRYPTION_KEY环境变量')
            })

    # 验证port范围
    if self.port and not (1 <= self.port <= 65535):
        raise ValidationError({'port': _('端口号必须在1-65535之间')})

    super().clean()
```

#### 争议4: Admin界面复杂度 ✅ 方案A（完整实现）
**专家投票:** Amelia✅ Murat✅

**理由:**
- Django Admin配置是声明式的，一次性配置不增加复杂度
- `readonly_fields=['password_encrypted']` - 防止密文泄露
- `list_filter=['is_active', 'is_healthy', 'protocol']` - 内置功能，0成本
- 自定义action可以延后，但基础配置应该一次性完成

**Admin配置模板:**
```python
@admin.register(ProxyConfig)
class ProxyConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'protocol', 'get_host_port', 'is_active', 'is_healthy', 'priority', 'last_used_at']
    list_filter = ['protocol', 'is_active', 'is_healthy']
    search_fields = ['name']
    readonly_fields = ['password_encrypted', 'created_at', 'updated_at', 'last_used_at']

    def get_host_port(self, obj):
        return f"{obj.host}:{obj.port}"
    get_host_port.short_description = "代理地址"
```

#### 争议5: 数据库迁移时机 ✅ 方案B（只创建ProxyConfig迁移）
**专家投票:** Murat✅ Bob✅

**理由:**
- ProxyUsageLog依赖ProxyConfig外键，应该到Story 9.2再创建
- 避免迁移文件过于复杂
- 符合单一Story职责原则

### 风险缓解措施（Bob识别）

#### 🔴 高风险（阻塞Story完成）

**风险1: Fernet密钥管理**
- **问题**: 开发者本地环境未配置密钥导致测试失败
- **缓解措施**: 在Story 9.0的generate_proxy_key.py脚本中添加详细注释

**风险2: BinaryField兼容性**
- **问题**: SQLite开发环境与PostgreSQL生产环境差异
- **缓解措施**: 在测试中验证BinaryField的跨数据库兼容性

**风险3: Admin密码字段显示**
- **问题**: 意外暴露密文
- **缓解措施**: 强制readonly_fields，添加单元测试验证

#### 🟡 中风险（影响进度）

**风险1: port范围验证**
- **问题**: 开发者忘记调用full_clean()
- **缓解措施**: 在Admin文档中强调验证流程

**风险2: ProxyProtocol枚举**
- **问题**: 枚举值与数据库迁移冲突
- **缓解措施**: 使用django.core.choices.Choices类（Django 3.2+）

### 工作量验证（Bob）

**任务拆分优化（并行执行策略）:**

```yaml
并行执行组1（Terminal Tab 1）:
  Task 1.1: ProxyConfig模型定义（2小时）
    - 13个字段定义
    - ProxyProtocol枚举
    - Meta.indexes配置
    - __str__方法

  Task 1.2: Fernet加密服务（2小时）[可与1.1并行]
    - encrypt_password()方法
    - decrypt_password()方法
    - 密钥加载逻辑
    - 单元测试

串行执行组:
  Task 2: get_proxy_url() + clean()验证（2小时）
    - 依赖Task 1.1完成
    - URL构建逻辑（4种场景）
    - port范围验证
    - 密钥存在性检查
    - 单元测试

  Task 3: Django Admin配置（2小时）
    - 依赖Task 2完成
    - list_display, list_filter配置
    - readonly_fields保护
    - 自定义方法（get_host_port）
    - Admin集成测试

  Task 4: 数据库迁移 + 验证（1小时）
    - 依赖Task 1完成
    - makemigrations proxy
    - migrate
    - 索引验证测试

  Task 5: 文档 + 代码审查（1小时）
    - 更新CLAUDE.md
    - 加密使用说明
    - PR自审查
```

**工作量统计:**
- 估算：1.5天（12小时）
- 优化后：10小时纯开发 + 2小时buffer = 12小时 ✅ 合理

### 测试覆盖率目标（Murat）

**关键测试风险识别:**

#### 🔴 高风险区域（必须100%覆盖）
1. **Fernet加密/解密一致性** - 数据损坏风险
2. **密码字段访问控制** - 安全漏洞风险
3. **port范围验证** - 数据完整性风险
4. **proxy URL构建** - API调用失败风险

**覆盖率目标分解:**
- **模型方法**: 100%（encrypt, decrypt, get_proxy_url, clean）
- **Admin配置**: 90%（list_display, readonly_fields验证）
- **验证逻辑**: 100%（port范围、name唯一性、密钥存在性）
- **总体覆盖率**: > 90%（DoD要求）

**测试用例设计（覆盖8个验收场景）:**

```python
# Scenario 1-2: 模型CRUD + 密码加密
@pytest.mark.django_db
class TestProxyConfigScenarios:
    def test_http_proxy_no_auth(self, client):
        """AC: 创建HTTP代理（无认证）"""
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080
        )
        assert proxy.is_active is True
        assert proxy.is_healthy is True
        assert proxy.priority == 0
        assert proxy.password_encrypted == b''  # 无密码，空bytes

    def test_https_proxy_with_encryption(self, client):
        """AC: 密码自动加密存储"""
        proxy = ProxyConfig.objects.create(
            name="加密代理",
            protocol=ProxyProtocol.HTTPS,
            host="proxy.example.com",
            port=443,
            username="user",
            password="Secret@123"
        )
        # 验证加密
        assert proxy.password_encrypted != b''
        assert proxy.password_encrypted != b'Secret@123'
        # 验证解密一致性
        decrypted = proxy.decrypt_password(proxy.password_encrypted)
        assert decrypted == "Secret@123"

# Scenario 3: 加密解密一致性（必须测试多次加密）
@pytest.mark.django_db
def test_fernet_non_deterministic():
    """AC: 多次加密相同密码产生不同密文（Fernet特性）"""
    proxy = ProxyConfig(password="SamePassword")

    encrypted1 = proxy.encrypt_password("SamePassword")
    encrypted2 = proxy.encrypt_password("SamePassword")

    # Fernet每次生成不同的token（timestamp不同）
    assert encrypted1 != encrypted2

    # 但解密结果一致
    assert proxy.decrypt_password(encrypted1) == "SamePassword"
    assert proxy.decrypt_password(encrypted2) == "SamePassword"

# Scenario 8: 密钥缺失处理
def test_missing_encryption_key():
    """AC: PROXY_ENCRYPTION_KEY未设置时抛出异常"""
    with override_settings(PROXY_ENCRYPTION_KEY=None):
        with pytest.raises(ImproperlyConfigured) as exc:
            ProxyConfig.objects.create(password="test")
        assert "PROXY_ENCRYPTION_KEY" in str(exc.value)

# Scenario 6: 索引验证（性能测试）
@pytest.mark.django_db
def test_query_indexes():
    """AC: 验证查询使用索引"""
    from django.test.utils import CaptureQueriesContext

    # 创建100个代理
    ProxyConfig.objects.bulk_create([
        ProxyConfig(name=f"Proxy{i}", protocol=ProxyProtocol.HTTP, host=f"host{i}", port=8080)
        for i in range(100)
    ])

    # 捕获查询
    with CaptureQueriesContext(connection) as context:
        list(ProxyConfig.objects.filter(is_active=True, is_healthy=True))

    # 验证使用了联合索引
    query = context.captured_queries[0]['sql']
    assert 'WHERE "apps_proxy"."is_active" AND "apps_proxy"."is_healthy"' in query
```

**测试依赖Mock策略:**
```python
# Mock Fernet避免依赖真实密钥
@patch('apps.proxy.models.Fernet')
def test_encrypt_with_mock_fernet(mock_fernet_class):
    mock_fernet = MagicMock()
    mock_fernet.encrypt.return_value = b'mocked_encrypted'
    mock_fernet_class.return_value = mock_fernet

    proxy = ProxyConfig(password="test")
    encrypted = proxy.encrypt_password("test")

    assert encrypted == b'mocked_encrypted'
    mock_fernet.encrypt.assert_called_once_with(b'test')
```

---

## 🛠️ 技术实现要点

### 核心实现
- ✅ 实现ProxyConfig模型（包含所有字段和Meta配置）
- ✅ 实现ProxyProtocol枚举（HTTP, HTTPS, SOCKS5）
- ✅ 实现encrypt_password()方法（使用Fernet，在save()中调用）
- ✅ 实现decrypt_password()方法
- ✅ 实现get_proxy_url()方法（构建httpx代理URL）
- ✅ 实现clean()方法（验证port范围、密钥存在性）
- ✅ 配置Django Admin（list_display, list_filter, search_fields, readonly_fields）
- ✅ 密码字段在Admin中显示为占位符"•••••••••"
- ✅ 添加数据库索引（is_active, is_healthy联合索引；-last_used_at索引）

### 架构决策
- **加密策略**: save()方法自动加密（方案A）
- **测试策略**: 分层测试（Phase 1: 单元测试 → Phase 2: Admin集成 → Phase 3: E2E）
- **验证策略**: clean()方法验证业务规则
- **Admin策略**: 完整实现（声明式配置，一次性完成）
- **迁移策略**: 只创建ProxyConfig迁移（ProxyUsageLog留到Story 9.2）

---

## 📦 前置条件

- ✅ Story 9.0已完成（基础设施准备就绪）
- ✅ PROXY_ENCRYPTION_KEY环境变量已设置
- ✅ cryptography和httpx[socks]依赖已安装

---

## 🔗 依赖关系

- 依赖 Story 9.0（代理管理基础设施准备）
- 被以下Story依赖:
  - Story 9.2（ProxyUsageLog模型，需要ProxyConfig外键）
  - Story 9.3（ProxyManager服务，需要ProxyConfig查询）

---

## 📊 DoD (Definition of Done)

- [x] ProxyConfig模型实现完整（13个字段）✅
- [x] ProxyProtocol枚举定义（HTTP, HTTPS, SOCKS5）✅
- [x] encrypt_password()方法通过单元测试（加密非空、密文与明文不同）✅
- [x] decrypt_password()方法通过单元测试（解密一致性）✅
- [x] get_proxy_url()方法通过单元测试（4种场景：有/无认证、HTTP/HTTPS）✅
- [x] clean()方法验证port范围（1-65535）✅
- [x] clean()方法验证PROXY_ENCRYPTION_KEY存在性 ✅
- [x] save()方法自动调用encrypt_password() ✅
- [x] 数据库索引创建成功（3个索引）✅
- [x] Django Admin配置完整（list_display包含7个字段）✅
- [x] password_encrypted在Admin中显示为"•••••••••" ✅
- [x] Django Admin支持按name、is_active、is_healthy、protocol筛选 ✅
- [x] 单元测试覆盖率 > 90%（包含密码加密解密、URL构建、字段验证）✅ 94% + 100%
- [x] 集成测试验证Django Admin CRUD流程 ✅ 29个测试全部通过
- [x] 错误场景测试通过（密钥缺失、port范围错误、name重复）✅
- [x] Fernet非确定性测试通过（多次加密产生不同密文）✅
- [x] 索引查询验证测试通过（100个代理性能测试）✅
- [ ] BinaryField跨数据库兼容性验证（SQLite ↔ PostgreSQL）⚠️ 生产环境需验证
- [x] Admin密码字段只读保护测试通过 ✅
- [x] 代码质量：Ruff + Pre-commit全部通过 ✅
- [x] 所有8个验收场景测试通过 ✅

---

## 📝 Change Log

| 日期 | 变更内容 | 作者 |
|------|---------|------|
| 2026-01-30 | Story创建完成 - ProxyConfig模型 + Fernet加密，包含8个验收场景 | BMAD Create-Story Workflow |
| 2026-01-30 | Party Mode专家团队优化 - 5个核心争议决策、风险缓解、测试策略、任务拆分优化 | Party Mode (Winston, Amelia, Murat, Bob) |

---

**Story状态:** ready-for-dev
**下一个Story:** Story 9.2 - ProxyUsageLog模型 + Admin界面
