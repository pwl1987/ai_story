"""
简化的端到端测试
直接测试execute_full_pipeline任务，跳过认证
"""

import os
import sys

import django

sys.path.insert(0, ".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()


from apps.projects.models import Project
from apps.projects.tasks import execute_full_pipeline

print("=" * 60)
print("端到端工作流测试（简化版）")
print("=" * 60)

# 1. 获取测试项目
print("\n1. 获取测试项目...")
try:
    project = Project.objects.get(name="E2E Test Project")
    print(f"✓ 找到项目: {project.name}")
    print(f"  ID: {project.id}")
    print(f"  状态: {project.status}")
except Project.DoesNotExist:
    print("✗ 测试项目不存在")
    print("  请先运行: uv run python scripts/create_test_project.py")
    sys.exit(1)

# 2. 直接调用Celery任务
print("\n2. 启动工作流...")
try:
    # 同步调用任务（用于测试）
    result = execute_full_pipeline(
        project_id=str(project.id),
        user_id=None,  # 不需要用户ID
    )

    print("\n任务结果:")
    print(f"  success: {result.get('success')}")
    print(f"  project_id: {result.get('project_id')}")

    if result.get("success"):
        print("\n✓ 工作流完成！")

        # 3. 验证项目状态
        print("\n3. 验证项目状态...")
        project.refresh_from_db()

        print(f"  最终状态: {project.status}")

        # 显示各阶段状态
        print("\n  阶段详情:")
        for stage in project.stages.all():
            symbol = "✓" if stage.status == "completed" else "✗"
            print(f"    {symbol} {stage.stage_type}: {stage.status}")

        # 验证完成
        if project.status == "completed":
            all_completed = all(s.status == "completed" for s in project.stages.all())
            if all_completed:
                print("\n" + "=" * 60)
                print("✓ 端到端测试通过！")
                print("=" * 60)
                sys.exit(0)
            else:
                print("\n⚠ 部分阶段未完成")
        else:
            print(f"\n✗ 项目状态异常: {project.status}")

    else:
        print("\n✗ 工作流失败")
        print(f"  错误: {result.get('error')}")

except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback

    traceback.print_exc()

sys.exit(1)
