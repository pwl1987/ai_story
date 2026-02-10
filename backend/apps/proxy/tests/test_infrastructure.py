"""
Story 9.0: 基础设施测试套件
验证proxy应用的依赖、加载、URL配置和密钥生成脚本

@Author: Epic 9 Team
@Created: 2026-01-30
@Story: 9.0 - 代理管理基础设施准备
"""

import subprocess
import sys
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import resolve, reverse


class DependencyTests(TestCase):
    """测试1: 依赖冲突检测 (AC: 1)"""

    def test_no_dependency_conflicts(self):
        """验证cryptography和httpx[socks]依赖无冲突"""
        try:
            import cryptography
            import httpx

            # 验证版本符合要求
            crypto_version = cryptography.__version__
            httpx_version = httpx.__version__

            # cryptography >= 41.0.0
            crypto_major = int(crypto_version.split(".")[0])
            self.assertGreaterEqual(
                crypto_major, 41, f"cryptography版本{crypto_version}低于要求41.0.0"
            )

            # httpx >= 0.24.0
            httpx_parts = httpx_version.split(".")
            httpx_major = int(httpx_parts[0])
            httpx_minor = int(httpx_parts[1]) if len(httpx_parts) > 1 else 0
            self.assertTrue(
                httpx_major > 0 or (httpx_major == 0 and httpx_minor >= 24),
                f"httpx版本{httpx_version}低于要求0.24.0",
            )

            # 验证SOCKS支持可用（httpx通过Proxy类支持socks5://协议）
            try:
                proxy = httpx.Proxy("socks5://localhost:1080")
                # httpx.Proxy对象的字符串表示包含协议类型
                proxy_str = str(proxy)
                self.assertIn("socks5", proxy_str.lower(), f"代理字符串'{proxy_str}'不包含'socks5'")

                # 验证Proxy对象的关键属性
                self.assertIsNotNone(proxy.url, "Proxy URL不能为空")
                self.assertEqual(str(proxy.url.scheme), "socks5", "Proxy scheme应为socks5")
            except Exception as e:
                self.fail(f"httpx SOCKS代理支持验证失败: {e}")
        except ImportError as e:
            self.fail(f"依赖导入失败: {e}")


class AppConfigTests(TestCase):
    """测试2: 应用加载验证 (AC: 2)"""

    def test_proxy_app_loads(self):
        """验证proxy应用正确加载到INSTALLED_APPS"""
        try:
            app_config = apps.get_app_config("proxy")
            self.assertEqual(app_config.name, "apps.proxy")
            self.assertEqual(app_config.verbose_name, "Proxy Management")
        except LookupError:
            self.fail("proxy应用未在INSTALLED_APPS中注册")

    def test_proxy_app_modules_exist(self):
        """验证proxy应用的核心模块存在"""
        proxy_app = Path(settings.BASE_DIR) / "apps" / "proxy"

        required_files = [
            "__init__.py",
            "apps.py",
            "models.py",
            "admin.py",
            "services.py",
            "views.py",
            "urls.py",
        ]

        for filename in required_files:
            file_path = proxy_app / filename
            self.assertTrue(file_path.exists(), f"proxy应用缺少必需文件: {filename}")


class KeyGenerationTests(TestCase):
    """测试3: 密钥生成脚本验证 (AC: 3)"""

    def test_key_format(self):
        """验证生成的密钥格式符合Fernet要求"""
        # 运行密钥生成脚本
        script_path = Path(settings.BASE_DIR) / "scripts" / "generate_proxy_key.py"
        if not script_path.exists():
            self.skipTest(f"密钥生成脚本不存在: {script_path}")

        result = subprocess.run(
            [sys.executable, str(script_path)], capture_output=True, text=True, timeout=5
        )

        self.assertEqual(result.returncode, 0, f"脚本执行失败: {result.stderr}")

        # 验证输出包含密钥（Fernet密钥格式：44字节base64编码）
        output_lines = result.stdout.strip().split("\n")
        # 脚本输出格式: "Key (44 characters):\n{ACTUAL_KEY}"
        try:
            key_idx = output_lines.index("Key (44 characters):")
            key = output_lines[key_idx + 1].strip()
        except (ValueError, IndexError):
            # 尝试另一种格式
            key_line = [line for line in output_lines if line.startswith("Key: ")]
            if key_line:
                key = key_line[0].split("Key: ")[1].strip()
            else:
                self.fail("脚本输出未找到密钥，输出格式:\n" + result.stdout)

        # 验证密钥长度（Fernet密钥为44字节base64编码）
        self.assertEqual(len(key), 44, f"密钥长度不正确: {len(key)} != 44")

        # 验证密钥可被Fernet加载
        try:
            from cryptography.fernet import Fernet

            fernet = Fernet(key.encode() if isinstance(key, str) else key)
            self.assertIsNotNone(fernet)
        except Exception as e:
            self.fail(f"生成的密钥无法被Fernet加载: {e}")


class URLConfigurationTests(TestCase):
    """测试4: URL配置验证 (AC: 2)"""

    @override_settings(ROOT_URLCONF="config.urls")
    def test_proxy_urls_included(self):
        """验证proxy URL路由正确包含到主URL配置"""
        try:
            # 测试proxy-select路由可访问
            url = reverse("proxy:proxy-select")
            resolved = resolve(url)

            self.assertEqual(url, "/api/v1/proxy/select/")
            self.assertEqual(resolved.url_name, "proxy-select")
        except Exception as e:
            self.fail(f"proxy URL路由未正确配置: {e}")

    @override_settings(ROOT_URLCONF="config.urls")
    def test_proxy_namespace_exists(self):
        """验证proxy应用命名空间正确配置"""
        try:
            # 验证可以通过命名空间解析URL
            url = reverse("proxy:proxy-select")
            self.assertIn("/api/v1/proxy/", url)
        except Exception as e:
            self.fail(f"proxy命名空间配置错误: {e}")


class MigrationTests(TestCase):
    """测试5: 数据库迁移验证 (AC: 4)"""

    def test_initial_migration_exists(self):
        """验证proxy应用有初始迁移文件"""
        from pathlib import Path

        # 直接检查迁移文件是否存在
        migrations_dir = Path(settings.BASE_DIR) / "apps" / "proxy" / "migrations"
        migration_file = migrations_dir / "0001_initial.py"

        self.assertTrue(
            migration_file.exists(), f"proxy应用缺少0001_initial迁移文件: {migration_file}"
        )

        # 验证迁移文件内容有效
        content = migration_file.read_text(encoding="utf-8")
        self.assertIn("class Migration", content, "迁移文件格式无效")
        self.assertIn("dependencies = [", content, "迁移文件缺少dependencies")
        self.assertIn("operations = [", content, "迁移文件缺少operations")

    def test_migration_file_structure(self):
        """验证迁移文件是空迁移（Story 9.0策略：--empty标志）"""
        from pathlib import Path

        migration_file = (
            Path(settings.BASE_DIR) / "apps" / "proxy" / "migrations" / "0001_initial.py"
        )
        content = migration_file.read_text(encoding="utf-8")

        # Story 9.0决策：使用空迁移，operations应为空列表
        self.assertIn("operations = [\n    ]", content, "迁移应为空迁移（operations为空列表）")


class TODOValidationTests(TestCase):
    """测试6: TODO注释验证 (Sally的质量标准)"""

    def test_models_py_has_todos(self):
        """验证models.py包含Story 9.1/9.2的实现和路线图注释"""
        models_path = Path(settings.BASE_DIR) / "apps" / "proxy" / "models.py"
        with open(models_path, encoding="utf-8") as f:
            content = f.read()

        # 验证包含实施路线图注释
        self.assertIn("实施路线图", content, "缺少实施路线图注释")

        # Story 9.1已完成：验证ProxyConfig模型存在
        self.assertIn("class ProxyConfig(models.Model):", content, "缺少ProxyConfig模型实现")

        # Story 9.2已完成：验证ProxyUsageLog模型存在
        self.assertIn("class ProxyUsageLog(models.Model):", content, "缺少ProxyUsageLog模型实现")

    def test_services_py_has_todos(self):
        """验证services.py包含Story 9.3和Story 9.4的完整实现"""
        services_path = Path(settings.BASE_DIR) / "apps" / "proxy" / "services.py"
        with open(services_path, encoding="utf-8") as f:
            content = f.read()

        # Story 9.3已完成：验证实现存在
        self.assertIn("class ProxyProvider(ABC):", content, "缺少ProxyProvider实现")
        self.assertIn("class NoProxyProvider(ProxyProvider):", content, "缺少NoProxyProvider实现")
        self.assertIn("class ProxyManager:", content, "缺少ProxyManager实现")

        # Story 9.4已完成：验证HttpProxyProvider完整实现
        self.assertIn(
            "class HttpProxyProvider(ProxyProvider):", content, "缺少HttpProxyProvider实现"
        )
        self.assertIn("def record_usage(", content, "缺少record_usage方法实现")

    def test_tasks_py_has_todos(self):
        """验证tasks.py包含Story 9.10的完整实现"""
        tasks_path = Path(settings.BASE_DIR) / "apps" / "proxy" / "tasks.py"
        with open(tasks_path, encoding="utf-8") as f:
            content = f.read()

        # Story 9.10已完成：验证健康检查任务实现存在
        self.assertIn("def check_proxy_health(", content, "缺少check_proxy_health任务实现")
        self.assertIn("Story 9.10", content, "缺少Story 9.10标记")
