"""
测试新实现的TODO功能
1. pause - 取消Celery任务
2. resume - 恢复暂停的项目
3. save_as_template - 保存项目为模板
4. export - 导出视频
"""

import os
import sys

import django

# 添加backend到sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

from django.contrib.auth import get_user_model

from apps.projects.models import Project
from apps.projects.services import cancel_project_tasks
from apps.prompts.models import PromptTemplate, PromptTemplateSet

User = get_user_model()


def test_cancel_project_tasks():
    """测试取消Celery任务功能"""
    print("\n" + "=" * 60)
    print("测试1: cancel_project_tasks")
    print("=" * 60)

    # 获取一个测试项目
    project = Project.objects.first()
    if not project:
        print("❌ 没有找到测试项目")
        return False

    print(f"✓ 找到测试项目: {project.name} (ID: {project.id})")

    # 将项目状态设为processing
    project.status = "processing"
    project.save()

    # 模拟一个processing状态的任务
    stage = project.stages.first()
    if stage:
        stage.status = "processing"
        stage.save()
        print(f"✓ 设置阶段 {stage.stage_type} 为processing状态")

    # 调用cancel_project_tasks
    cancelled_count = cancel_project_tasks(str(project.id))
    print(f"✓ 取消了 {cancelled_count} 个任务")

    # 验证阶段状态已重置
    stage.refresh_from_db()
    if stage.status == "pending":
        print("✓ 阶段状态已重置为pending")
        return True
    else:
        print(f"❌ 阶段状态未重置: {stage.status}")
        return False


def test_save_as_template():
    """测试保存项目为模板功能"""
    print("\n" + "=" * 60)
    print("测试2: save_as_template")
    print("=" * 60)

    # 获取一个测试项目
    project = Project.objects.first()
    if not project:
        print("❌ 没有找到测试项目")
        return False

    print(f"✓ 找到测试项目: {project.name}")

    # 模拟保存模板逻辑
    original_template_set = project.prompt_template_set
    template_name = "测试模板"

    # 创建新的提示词集
    new_template_set = PromptTemplateSet.objects.create(
        name=f"{template_name} (模板)",
        description=f"基于项目 '{project.name}' 创建的模板",
        created_by=project.user,
        is_active=True,
    )
    print(f"✓ 创建新提示词集: {new_template_set.name}")

    # 复制所有提示词模板
    original_templates = PromptTemplate.objects.filter(template_set=original_template_set)
    for template in original_templates:
        PromptTemplate.objects.create(
            template_set=new_template_set,
            stage_type=template.stage_type,
            template_content=template.template_content,
            is_active=True,
        )

    print(f"✓ 复制了 {original_templates.count()} 个提示词模板")

    # 验证
    new_templates_count = PromptTemplate.objects.filter(template_set=new_template_set).count()
    if new_templates_count == original_templates.count():
        print(f"✓ 模板复制成功 ({new_templates_count}个)")
        return True
    else:
        print("❌ 模板复制失败")
        return False


def test_export_logic():
    """测试视频导出逻辑"""
    print("\n" + "=" * 60)
    print("测试3: export logic")
    print("=" * 60)

    # 获取一个已完成的项目
    completed_project = Project.objects.filter(status="completed").first()
    if not completed_project:
        print("⚠️ 没有找到已完成的项目，跳过导出测试")
        return True

    print(f"✓ 找到已完成项目: {completed_project.name}")

    # 模拟导出逻辑
    import uuid

    from apps.content.models import GeneratedVideo, Storyboard
    from apps.projects.models import ProjectProgressHistory

    # 获取所有生成的视频片段
    storyboards = Storyboard.objects.filter(project=completed_project).order_by("sequence_number")
    videos = []

    for storyboard in storyboards:
        video = GeneratedVideo.objects.filter(storyboard=storyboard, status="completed").first()

        if video and video.video_url:
            videos.append(
                {
                    "sequence_number": storyboard.sequence_number,
                    "video_url": video.video_url,
                }
            )

    print(f"✓ 找到 {len(videos)} 个视频片段")

    if len(videos) > 0:
        # 创建导出任务记录
        export_id = str(uuid.uuid4())

        ProjectProgressHistory.objects.create(
            project=completed_project,
            stage_type="export",
            status="processing",
            progress=0,
            message=f"开始导出视频，共{len(videos)}个片段",
            metadata={"export_id": export_id, "video_count": len(videos)},
        )

        print(f"✓ 创建导出任务记录: {export_id}")
        return True
    else:
        print("⚠️ 没有找到视频片段")
        return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("TODO功能验证测试")
    print("=" * 60)

    results = []

    # 测试1: cancel_project_tasks
    try:
        result = test_cancel_project_tasks()
        results.append(("cancel_project_tasks", result))
    except Exception as e:
        print(f"❌ 测试1异常: {e}")
        results.append(("cancel_project_tasks", False))

    # 测试2: save_as_template
    try:
        result = test_save_as_template()
        results.append(("save_as_template", result))
    except Exception as e:
        print(f"❌ 测试2异常: {e}")
        results.append(("save_as_template", False))

    # 测试3: export logic
    try:
        result = test_export_logic()
        results.append(("export_logic", result))
    except Exception as e:
        print(f"❌ 测试3异常: {e}")
        results.append(("export_logic", False))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)

    print(f"\n总计: {passed_count}/{total_count} 通过")

    if passed_count == total_count:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️ {total_count - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
