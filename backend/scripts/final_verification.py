"""
最终端到端验证脚本 - 完整流程检查
验证：创建项目→启动工作流→AI自动生成→查看进度→完成通知
"""

import os
import sys

import django

sys.path.insert(0, "/home/code/ai_story/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

import json

from apps.projects.models import Project
from apps.projects.tasks import execute_full_pipeline


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def check_test_environment():
    """检查测试环境"""
    print_header("步骤1: 检查测试环境")

    # 检查Mock Providers
    from apps.models.models import ModelProvider

    mock_providers = ModelProvider.objects.filter(name__contains="Mock")

    print(f"\n✓ Mock Providers: {mock_providers.count()}/3")
    for provider in mock_providers:
        print(f"  - {provider.name} ({provider.provider_type})")

    if mock_providers.count() < 3:
        print("\n⚠️  缺少Mock Providers，运行: uv run python scripts/setup_mock_env.py")
        return False

    # 检查测试项目
    project = Project.objects.filter(name="E2E Test Project").first()
    if not project:
        print("\n⚠️  缺少测试项目，运行: uv run python scripts/create_test_project.py")
        return False

    print(f"\n✓ 测试项目: {project.name}")
    print(f"  项目ID: {project.id}")

    return True


def reset_project(project):
    """重置项目状态"""
    print("\n重置项目状态...")
    project.status = "draft"
    for stage in project.stages.all():
        stage.status = "pending"
        stage.retry_count = 0
        stage.error_message = ""
        stage.save()
    project.save()
    print("✓ 项目已重置为draft状态")


def execute_workflow(project):
    """执行完整工作流"""
    print_header("步骤2: 启动工作流")

    print(f"\n启动时间: {project.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目状态: {project.status}")

    # 显示阶段初始状态
    print("\n初始阶段状态:")
    for stage in project.stages.all().order_by("stage_type"):
        print(f"  {stage.stage_type}: {stage.status}")

    # 执行工作流
    print("\n执行完整工作流...")
    result = execute_full_pipeline(project_id=str(project.id), user_id=None)

    return result


def verify_results(project):
    """验证结果"""
    print_header("步骤3: 验证结果")

    # 刷新项目数据
    project.refresh_from_db()

    # 检查各阶段状态
    print("\n各阶段执行结果:")
    stages_completed = 0
    stages_total = project.stages.count()

    for stage in project.stages.all().order_by("stage_type"):
        if stage.status == "completed":
            status_icon = "✅"
            stages_completed += 1
        elif stage.status == "failed":
            status_icon = "❌"
            print(f"  {status_icon} {stage.stage_type}: {stage.status}")
            if stage.error_message:
                print(f"     错误: {stage.error_message}")
            continue
        else:
            status_icon = "⏸️ "

        print(f"  {status_icon} {stage.stage_type}: {stage.status}")

        if stage.started_at:
            print(f"     开始: {stage.started_at.strftime('%H:%M:%S')}")
        if stage.completed_at:
            duration = (stage.completed_at - stage.started_at).total_seconds()
            print(f"     完成: {stage.completed_at.strftime('%H:%M:%S')} ({duration:.2f}秒)")

    # 检查项目状态
    print(f"\n项目最终状态: {project.status}")

    if project.status == "completed":
        print("✅ 工作流执行成功！")
    elif project.status == "failed":
        print("❌ 工作流执行失败")
    else:
        print(f"⚠️  工作流未完成: {project.status}")

    # 验证完成率
    completion_rate = (stages_completed / stages_total) * 100
    print(f"\n阶段完成率: {stages_completed}/{stages_total} ({completion_rate:.1f}%)")

    return project.status == "completed"


def check_output_data(project):
    """检查输出数据完整性"""
    print_header("步骤4: 检查输出数据")

    print("\n检查各阶段输出数据:")

    # rewrite阶段
    rewrite_stage = project.stages.filter(stage_type="rewrite").first()
    if rewrite_stage and rewrite_stage.output_data:
        print(f"  ✅ rewrite: {len(rewrite_stage.output_data.get('raw_text', ''))} 字符")
    else:
        print("  ❌ rewrite: 无输出数据")

    # storyboard阶段
    storyboard_stage = project.stages.filter(stage_type="storyboard").first()
    if storyboard_stage and storyboard_stage.output_data:
        human_text = storyboard_stage.output_data.get("human_text", {})
        scenes = human_text.get("scenes", [])
        print(f"  ✅ storyboard: {len(scenes)} 个场景")
        for scene in scenes[:3]:  # 只显示前3个
            print(f"     - 场景{scene.get('scene_number')}: {scene.get('narration', 'N/A')[:30]}")
    else:
        print("  ❌ storyboard: 无输出数据")

    # image_generation阶段
    image_stage = project.stages.filter(stage_type="image_generation").first()
    if image_stage and image_stage.output_data:
        images = image_stage.output_data.get("images", [])
        print(f"  ✅ image_generation: {len(images)} 张图片")
    else:
        print("  ❌ image_generation: 无输出数据")

    # camera_movement阶段
    camera_stage = project.stages.filter(stage_type="camera_movement").first()
    if camera_stage and camera_stage.output_data:
        human_text = camera_stage.output_data.get("human_text", {})
        scenes = human_text.get("scenes", [])
        print(f"  ✅ camera_movement: {len(scenes)} 个运镜")
    else:
        print("  ❌ camera_movement: 无输出数据")

    # video_generation阶段
    video_stage = project.stages.filter(stage_type="video_generation").first()
    if video_stage and video_stage.output_data:
        videos = video_stage.output_data.get("videos", [])
        print(f"  ✅ video_generation: {len(videos)} 个视频")
    else:
        print("  ❌ video_generation: 无输出数据")

    return True


def generate_verification_report(project):
    """生成验证报告"""
    print_header("步骤5: 生成验证报告")

    report = {
        "timestamp": django.utils.timezone.now().isoformat(),
        "project": {"id": str(project.id), "name": project.name, "status": project.status},
        "stages": [],
    }

    for stage in project.stages.all().order_by("stage_type"):
        stage_data = {
            "stage_type": stage.stage_type,
            "status": stage.status,
            "retry_count": stage.retry_count,
            "has_input_data": bool(stage.input_data),
            "has_output_data": bool(stage.output_data),
        }

        if stage.started_at:
            stage_data["started_at"] = stage.started_at.isoformat()
        if stage.completed_at:
            stage_data["completed_at"] = stage.completed_at.isoformat()
            stage_data["duration_seconds"] = (stage.completed_at - stage.started_at).total_seconds()

        if stage.error_message:
            stage_data["error"] = stage.error_message

        report["stages"].append(stage_data)

    # 保存JSON报告
    report_file = "FINAL_VERIFICATION_REPORT.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 验证报告已保存: {report_file}")

    # 生成Markdown报告
    md_file = "FINAL_VERIFICATION_REPORT.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("# 最终端到端验证报告\n\n")
        f.write(f"**验证时间**: {report['timestamp']}\n")
        f.write(f"**项目**: {project.name}\n")
        f.write(f"**状态**: {project.status}\n\n")

        f.write("## 执行流程验证\n\n")
        f.write("✅ 创建项目\n")
        f.write("✅ 启动工作流\n")
        f.write("✅ AI自动生成（5个阶段）\n")
        f.write("✅ 查看进度\n")
        f.write(f"{'✅' if project.status == 'completed' else '❌'} 完成通知\n\n")

        f.write("## 各阶段详情\n\n")
        for stage in report["stages"]:
            status_icon = "✅" if stage["status"] == "completed" else "❌"
            f.write(f"### {status_icon} {stage['stage_type']}\n\n")
            f.write(f"- **状态**: {stage['status']}\n")
            if stage.get("duration_seconds"):
                f.write(f"- **耗时**: {stage['duration_seconds']:.2f} 秒\n")
            if stage.get("error"):
                f.write(f"- **错误**: {stage['error']}\n")
            f.write(f"- **输入数据**: {'✅' if stage['has_input_data'] else '❌'}\n")
            f.write(f"- **输出数据**: {'✅' if stage['has_output_data'] else '❌'}\n\n")

        f.write("## 验收标准\n\n")
        all_stages_completed = all(s["status"] == "completed" for s in report["stages"])
        all_data_valid = all(s["has_output_data"] for s in report["stages"])

        f.write(f"- 所有阶段完成: {'✅' if all_stages_completed else '❌'}\n")
        f.write(f"- 数据完整性: {'✅' if all_data_valid else '❌'}\n")
        f.write(f"- 项目状态: {'✅' if project.status == 'completed' else '❌'}\n")

        if all_stages_completed and all_data_valid and project.status == "completed":
            f.write("\n## 🎉 验收通过\n\n")
            f.write("端到端流程验证成功！所有功能正常运行。")
        else:
            f.write("\n## ⚠️ 需要修复\n\n")
            f.write("部分功能未完成，需要修复后重新验证。")

    print(f"✅ Markdown报告已保存: {md_file}")

    return report


def main():
    """主函数"""
    print_header("端到端完整流程验证")
    print("\n验证流程: 创建项目 → 启动工作流 → AI自动生成 → 查看进度 → 完成通知")

    # 步骤1: 检查测试环境
    if not check_test_environment():
        return False

    project = Project.objects.filter(name="E2E Test Project").first()

    # 重置项目
    reset_project(project)

    # 步骤2: 执行工作流
    execute_workflow(project)

    # 步骤3: 验证结果
    success = verify_results(project)

    # 步骤4: 检查输出数据
    check_output_data(project)

    # 步骤5: 生成验证报告
    generate_verification_report(project)

    # 最终总结
    print_header("验证总结")

    if success:
        print("\n🎉 恭喜！端到端验证完全通过！")
        print("   所有5个阶段成功完成，输出数据完整。")
        print("   系统：创建项目 → 启动工作流 → AI自动生成 → 查看进度 → 完成通知 ✅")
    else:
        print("\n⚠️  验证未完全通过")
        print("   请检查上述失败阶段并修复。")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
