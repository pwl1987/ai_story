#!/usr/bin/env python
"""
Story 8.1手动验证脚本 - 使用Django Test Client
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from config.admin import staff_admin_site


def verify_story_8_1():
    """验证Story 8.1的所有功能"""

    print("=" * 60)
    print("Story 8.1: StaffAdminSite手动验证")
    print("=" * 60)
    print()

    results = []

    # 测试1: 检查StaffAdminSite配置
    print("📋 测试1: StaffAdminSite配置检查")
    try:
        assert staff_admin_site.site_header == "AI Story 管理后台"
        assert staff_admin_site.site_title == "AI Story Admin"
        assert staff_admin_site.index_title == "欢迎使用 AI Story 管理后台"
        print("✅ 通过: StaffAdminSite自定义配置正确")
        results.append(("StaffAdminSite配置", True))
    except AssertionError as e:
        print(f"❌ 失败: {e}")
        results.append(("StaffAdminSite配置", False))
    print()

    # 测试2: 检查模型注册
    print("📋 测试2: 模型注册检查")
    try:
        from apps.projects.models import Project, ProjectStage, ProjectModelConfig
        from apps.models.models import ModelProvider, ModelUsageLog
        from apps.prompts.models import PromptTemplateSet, PromptTemplate, GlobalVariable
        from apps.content.models import (
            ContentRewrite,
            Storyboard,
            GeneratedImage,
            CameraMovement,
            GeneratedVideo,
        )
        from apps.files.models import UploadedFile, FileQuota
        from django.contrib.auth.models import User

        expected_models = [
            Project,
            ProjectStage,
            ProjectModelConfig,
            ModelProvider,
            ModelUsageLog,
            PromptTemplateSet,
            PromptTemplate,
            GlobalVariable,
            ContentRewrite,
            Storyboard,
            GeneratedImage,
            CameraMovement,
            GeneratedVideo,
            UploadedFile,
            FileQuota,
            User,
        ]

        for model in expected_models:
            assert staff_admin_site.is_registered(model), f"{model.__name__}未注册"

        print(f"✅ 通过: {len(expected_models)}个模型已注册")
        results.append(("模型注册", True))
    except AssertionError as e:
        print(f"❌ 失败: {e}")
        results.append(("模型注册", False))
    print()

    # 创建测试客户端
    client = Client()

    # 测试3: 未认证用户访问
    print("📋 测试3: 未认证用户访问Admin")
    response = client.get("/admin/")
    if response.status_code == 302:
        print("✅ 通过: 未认证用户被重定向到登录页 (302)")
        results.append(("未认证访问", True))
    else:
        print(f"❌ 失败: 期望302，实际{response.status_code}")
        results.append(("未认证访问", False))
    print()

    # 测试4: admin用户登录
    print("📋 测试4: admin超级用户登录并访问Admin")
    try:
        admin_user = User.objects.get(username="admin")
        client.force_login(admin_user)
        response = client.get("/admin/")

        assert response.status_code == 200, f"期望200，实际{response.status_code}"
        content = response.content.decode("utf-8")
        assert "AI Story 管理后台" in content, "页面不包含自定义标题"

        print("✅ 通过: admin用户可以访问Admin并看到自定义标题")
        results.append(("admin用户访问", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        results.append(("admin用户访问", False))
    print()

    # 测试5: staff用户访问
    print("📋 测试5: staff用户登录并访问Admin")
    try:
        staff_user = User.objects.get(username="staff")
        client.force_login(staff_user)
        response = client.get("/admin/")

        assert response.status_code == 200, f"期望200，实际{response.status_code}"

        print("✅ 通过: staff用户可以访问Admin后台")
        results.append(("staff用户访问", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        results.append(("staff用户访问", False))
    print()

    # 测试6: normal用户访问
    print("📋 测试6: normal用户（is_staff=False）访问Admin")
    try:
        normal_user = User.objects.get(username="normal")
        client.force_login(normal_user)
        response = client.get("/admin/")

        # Django Admin会重定向到登录页
        assert response.status_code == 302, f"期望302，实际{response.status_code}"

        print("✅ 通过: normal用户被重定向到登录页 (302)")
        results.append(("normal用户访问", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        results.append(("normal用户访问", False))
    print()

    # 测试7: User模型Admin页面
    print("📋 测试7: User模型Admin页面访问")
    try:
        admin_user = User.objects.get(username="admin")
        client.force_login(admin_user)
        response = client.get("/admin/auth/user/")

        assert response.status_code == 200, f"期望200，实际{response.status_code}"

        print("✅ 通过: User模型Admin页面可访问")
        results.append(("User模型Admin", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        results.append(("User模型Admin", False))
    print()

    # 测试8: has_permission方法
    print("📋 测试8: StaffAdminSite.has_permission()方法")
    try:
        from django.test import RequestFactory

        factory = RequestFactory()

        # 未认证请求
        request = factory.get("/admin/")
        request.user = type("AnonymousUser", (), {"is_authenticated": False})()
        assert not staff_admin_site.has_permission(request), "未认证用户应该没有权限"

        # normal用户
        request.user = normal_user
        assert not staff_admin_site.has_permission(request), "normal用户应该没有权限"

        # staff用户
        request.user = staff_user
        assert staff_admin_site.has_permission(request), "staff用户应该有权限"

        print("✅ 通过: has_permission方法工作正常")
        results.append(("has_permission方法", True))
    except Exception as e:
        print(f"❌ 失败: {e}")
        results.append(("has_permission方法", False))
    print()

    # 打印总结
    print("=" * 60)
    print("验证总结")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")

    print()
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)

    if passed == total:
        print("\n🎉 所有测试通过！Story 8.1验证成功！")
        print("\n📝 下一步建议:")
        print("1. 在浏览器中手动测试Admin界面（推荐）")
        print("   - 访问 http://localhost:8000/admin/")
        print("   - 使用 admin/admin123 登录")
        print("   - 查看17个注册的模型")
        print("2. 继续实施 Story 8.2: 用户管理Admin功能")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查实现")
        return False


if __name__ == "__main__":
    verify_story_8_1()
