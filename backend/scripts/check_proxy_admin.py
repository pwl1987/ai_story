#!/usr/bin/env python
"""
Epic 9 代理管理 Admin 诊断脚本

检查 Django Admin 中代理配置的完整状态
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django 设置
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

import django

django.setup()

from django.contrib import admin
from apps.proxy.models import ProxyConfig, ProxyUsageLog
from apps.proxy.apps import ProxyConfig as ProxyAppConfig


def check_installed_apps():
    """检查 1: INSTALLED_APPS 配置"""
    print("=" * 60)
    print("✅ 检查 1: INSTALLED_APPS 配置")
    print("=" * 60)

    from django.conf import settings

    if "apps.proxy" in settings.INSTALLED_APPS:
        print("✓ apps.proxy 已在 INSTALLED_APPS 中")
        return True
    else:
        print("✗ apps.proxy 未在 INSTALLED_APPS 中")
        return False


def check_migrations():
    """检查 2: 数据库迁移状态"""
    print("\n" + "=" * 60)
    print("✅ 检查 2: 数据库迁移状态")
    print("=" * 60)

    from django.core.management import call_command
    from io import StringIO

    out = StringIO()
    call_command("showmigrations", "proxy", stdout=out)
    output = out.getvalue()

    if "[X]" in output:
        migration_count = output.count("[X]")
        print(f"✓ 已完成 {migration_count} 个迁移")
        print(f"  {output.strip()}")
        return True
    else:
        print("✗ 迁移未完成")
        print(f"  {output.strip()}")
        return False


def check_admin_registration():
    """检查 3: Admin 注册状态"""
    print("\n" + "=" * 60)
    print("✅ 检查 3: Admin 注册状态")
    print("=" * 60)

    models_registered = []

    if ProxyConfig in admin.site._registry:
        print("✓ ProxyConfig 已注册到 Admin")
        models_registered.append("ProxyConfig")
    else:
        print("✗ ProxyConfig 未注册到 Admin")

    if ProxyUsageLog in admin.site._registry:
        print("✓ ProxyUsageLog 已注册到 Admin")
        models_registered.append("ProxyUsageLog")
    else:
        print("✗ ProxyUsageLog 未注册到 Admin")

    return len(models_registered) == 2


def check_database_records():
    """检查 4: 数据库记录"""
    print("\n" + "=" * 60)
    print("✅ 检查 4: 数据库记录")
    print("=" * 60)

    proxy_count = ProxyConfig.objects.count()
    log_count = ProxyUsageLog.objects.count()

    print(f"ProxyConfig 记录数: {proxy_count}")
    print(f"ProxyUsageLog 记录数: {log_count}")

    if proxy_count > 0:
        print("\n现有代理配置:")
        for proxy in ProxyConfig.objects.all()[:5]:
            print(
                f"  - {proxy.name} ({proxy.protocol}) - {'激活' if proxy.is_active else '未激活'}"
            )
        return True
    else:
        print("  ℹ️  数据库中无代理配置（这是正常的，需要手动创建）")
        return None


def check_admin_config():
    """检查 5: Admin 配置详情"""
    print("\n" + "=" * 60)
    print("✅ 检查 5: Admin 配置详情")
    print("=" * 60)

    if ProxyConfig in admin.site._registry:
        admin_class = admin.site._registry[ProxyConfig]
        print(f"✓ Admin 类: {admin_class.__class__.__name__}")
        print(f"  列表显示字段: {admin_class.list_display}")
        print(f"  搜索字段: {admin_class.search_fields}")
        print(f"  筛选器: {admin_class.list_filter}")
        return True
    else:
        print("✗ Admin 类未找到")
        return False


def check_app_config():
    """检查 6: App 配置"""
    print("\n" + "=" * 60)
    print("✅ 检查 6: App 配置")
    print("=" * 60)

    app_config = ProxyAppConfig.create("apps.proxy")
    print(f"✓ App 名称: {app_config.verbose_name}")
    print(f"  模块路径: {app_config.name}")
    return True


def generate_test_data():
    """操作: 创建测试代理配置"""
    print("\n" + "=" * 60)
    print("🔧 操作: 创建测试代理配置")
    print("=" * 60)

    if ProxyConfig.objects.count() > 0:
        print("ℹ️  数据库中已有代理配置，跳过创建")
        return False

    print("正在创建测试代理配置...")

    test_proxies = [
        {
            "name": "测试代理-HTTP",
            "protocol": "http",
            "host": "127.0.0.1",
            "port": 8080,
            "is_active": True,
            "priority": 10,
        },
        {
            "name": "测试代理-SOCKS5",
            "protocol": "socks5",
            "host": "127.0.0.1",
            "port": 1080,
            "is_active": False,
            "priority": 20,
        },
    ]

    for proxy_data in test_proxies:
        proxy = ProxyConfig.objects.create(**proxy_data)
        print(f"✓ 创建: {proxy.name}")

    print(f"\n✅ 成功创建 {len(test_proxies)} 个测试代理配置")
    print("  现在可以在 Django Admin 中查看和编辑这些配置")
    return True


def main():
    """主诊断流程"""
    print("\n" + "🔍" * 30)
    print("  Epic 9 代理管理 Admin 诊断工具")
    print("🔍" * 30 + "\n")

    results = []

    # 执行检查
    results.append(("INSTALLED_APPS", check_installed_apps()))
    results.append(("数据库迁移", check_migrations()))
    results.append(("Admin 注册", check_admin_registration()))
    results.append(("App 配置", check_app_config()))
    results.append(("Admin 配置详情", check_admin_config()))
    db_result = check_database_records()

    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 诊断结果汇总")
    print("=" * 60)

    passed = sum(1 for _, result in results if result is True)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\n通过率: {passed}/{total} ({passed * 100 // total}%)")

    # 结论和建议
    print("\n" + "=" * 60)
    print("💡 结论和建议")
    print("=" * 60)

    if passed == total:
        print("✅ 所有检查通过！代理管理系统配置正确")
        print("\n如果 Admin 后台仍看不到代理配置，请检查：")
        print("  1. 刷新浏览器页面（Ctrl+F5 强制刷新）")
        print("  2. 确认登录用户有查看权限")
        print("  3. 检查 Admin 首页是否显示 'Proxy Management' 应用")
        print("  4. 尝试重启 Django 服务器")
    else:
        print("❌ 部分检查失败，请查看上面的详细信息")

    # 创建测试数据
    if db_result is None:
        print("\n是否创建测试代理配置？(y/n): ", end="")
        # 交互模式禁用，直接创建
        print("\n自动创建测试数据...")
        generate_test_data()

    print("\n" + "=" * 60)
    print("✅ 诊断完成")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
