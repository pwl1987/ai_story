#!/usr/bin/env python
"""
一键初始化Demo环境
快速开始脚本 - 为新用户自动配置完整的Mock环境

功能：
1. 创建测试用户
2. 创建3个Mock AI Provider
3. 创建完整的Prompt模板集（5个阶段）
4. 创建Demo项目
5. 配置所有关联关系

使用方法：
    cd backend
    uv run python scripts/init_demo_env.py
"""

import os
import sys

import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()


from django.contrib.auth import get_user_model

from apps.models.models import ModelProvider
from apps.projects.models import Project, ProjectModelConfig, ProjectStage
from apps.prompts.models import PromptTemplate, PromptTemplateSet

User = get_user_model()


def create_demo_user():
    """创建Demo用户"""
    print("=" * 70)
    print("步骤 1/5: 创建Demo用户")
    print("=" * 70)

    user, created = User.objects.get_or_create(
        username="demo_user",
        defaults={"email": "demo@example.com", "first_name": "Demo", "last_name": "User"},
    )

    if created:
        user.set_password("demo123456")
        user.save()
        print(f"✓ 创建用户成功: {user.username}")
        print(f"  邮箱: {user.email}")
        print("  密码: demo123456")
    else:
        print(f"✓ 用户已存在: {user.username}")

    return user


def create_mock_providers():
    """创建Mock AI Providers"""
    print("\n" + "=" * 70)
    print("步骤 2/5: 创建Mock AI Providers")
    print("=" * 70)

    providers = {}

    # Mock LLM Provider
    mock_llm, created = ModelProvider.objects.get_or_create(
        name="Demo Mock LLM",
        defaults={
            "provider_type": "llm",
            "executor_class": "core.ai_client.mock_llm_client.MockLLMClient",
            "api_url": "http://localhost:8000/api/mock/llm/",
            "is_active": True,
        },
    )
    providers["llm"] = mock_llm
    print(f"{'✓ 创建' if created else '✓ 已存在'} Mock LLM Provider")

    # Mock Text2Image Provider
    mock_t2i, created = ModelProvider.objects.get_or_create(
        name="Demo Mock Text2Image",
        defaults={
            "provider_type": "text2image",
            "executor_class": "core.ai_client.mock_text2image_client.MockText2ImageClient",
            "is_active": True,
        },
    )
    providers["t2i"] = mock_t2i
    print(f"{'✓ 创建' if created else '✓ 已存在'} Mock Text2Image Provider")

    # Mock Image2Video Provider
    mock_i2v, created = ModelProvider.objects.get_or_create(
        name="Demo Mock Image2Video",
        defaults={
            "provider_type": "image2video",
            "executor_class": "core.ai_client.mock_image2video_client.MockImage2VideoClient",
            "is_active": True,
        },
    )
    providers["i2v"] = mock_i2v
    print(f"{'✓ 创建' if created else '✓ 已存在'} Mock Image2Video Provider")

    print(f"\n✓ 总计 {len(providers)} 个Mock Provider已就绪")
    return providers


def create_prompt_templates(user):
    """创建完整的Prompt模板集"""
    print("\n" + "=" * 70)
    print("步骤 3/5: 创建Prompt模板集")
    print("=" * 70)

    # 创建PromptTemplateSet
    prompt_set, created = PromptTemplateSet.objects.get_or_create(
        name="Demo完整模板集",
        defaults={
            "description": "包含所有5个阶段的完整提示词模板，适用于快速开始",
            "created_by": user,
            "is_active": True,
            "is_default": True,
        },
    )
    print(f"{'✓ 创建' if created else '✓ 已存在'} Prompt模板集: {prompt_set.name}")

    # 定义5个阶段的模板
    templates_config = [
        {
            "stage_type": "rewrite",
            "template": """你是一位专业的故事编剧。请将以下原始文案改写为更生动、更有吸引力的版本。

原始文案：{{ raw_text }}

要求：
1. 保持核心主题不变
2. 增加细节描写，让场景更生动
3. 优化语言表达，提升可读性
4. 保持简洁，不超过200字

请输出改写后的文案：""",
        },
        {
            "stage_type": "storyboard",
            "template": """你是一位专业的分镜师。请根据以下改写后的文案，生成详细的分镜描述。

改写文案：{{ rewritten_text }}

请按照以下格式输出分镜：
[
  {
    "scene_number": 1,
    "description": "场景描述",
    "camera_angle": "拍摄角度（如：特写/中景/远景）",
    "duration": "时长（秒）",
    "audio": "音频描述"
  }
]

要求：
1. 生成5-8个分镜
2. 每个分镜要具体可执行
3. 包含镜头运动和画面描述

请输出分镜脚本：""",
        },
        {
            "stage_type": "image_generation",
            "template": """请为以下分镜生成AI绘画提示词。

分镜描述：{{ scene_description }}
镜头角度：{{ camera_angle }}

请生成详细的英文提示词，包括：
1. 主体描述
2. 环境和背景
3. 光照和氛围
4. 艺术风格
5. 质量标签（如：masterpiece, best quality, 4k）

输出格式：
Prompt: [详细提示词]
Negative Prompt: [负面提示词]""",
        },
        {
            "stage_type": "camera_movement",
            "template": """请为以下图片设计合适的运镜效果。

图片描述：{{ scene_description }}
初始镜头：{{ camera_angle }}

请设计运镜序列，包括：
1. 镜头运动类型（推/拉/摇/移/跟/升降）
2. 运动轨迹
3. 运动速度（慢/中/快）
4. 关键帧描述

输出JSON格式：
{
  "movements": [
    {
      "type": "运镜类型",
      "trajectory": "运动轨迹",
      "speed": "速度",
      "keyframes": ["关键帧1", "关键帧2"]
    }
  ]
}""",
        },
        {
            "stage_type": "video_generation",
            "template": """请将以下图片序列和运镜效果合成为视频。

图片列表：{{ image_urls }}
运镜序列：{{ camera_movements }}

请生成：
1. 视频时长（秒）
2. 帧率（fps）
3. 输出分辨率
4. 转场效果描述

输出格式：
{
  "duration": 5,
  "fps": 24,
  "resolution": "1920x1080",
  "transitions": ["淡入", "叠化", "淡出"]
}""",
        },
    ]

    stage_names = {
        "rewrite": "文案改写模板",
        "storyboard": "分镜生成模板",
        "image_generation": "图片生成提示词模板",
        "camera_movement": "运镜生成模板",
        "video_generation": "视频生成模板",
    }

    created_count = 0
    for config in templates_config:
        _template, created = PromptTemplate.objects.get_or_create(
            template_set=prompt_set,
            stage_type=config["stage_type"],
            defaults={"template_content": config["template"], "is_active": True},
        )
        if created:
            created_count += 1
        print(f"  {'✓ 创建' if created else '✓ 已存在'} {stage_names[config['stage_type']]}")

    print(f"\n✓ 总计 {len(templates_config)} 个Prompt模板已就绪")
    return prompt_set


def create_demo_project(user, providers, prompt_set):
    """创建Demo项目"""
    print("\n" + "=" * 70)
    print("步骤 4/5: 创建Demo项目")
    print("=" * 70)

    # 创建项目
    project, created = Project.objects.get_or_create(
        name="Demo示例项目 - 宁静的小镇",
        defaults={
            "user": user,
            "original_topic": "宁静的小镇，清晨的阳光洒在石板路上，年轻的画家在溪边写生，远处的山峦若隐若现",
            "prompt_template_set": prompt_set,
            "status": "draft",
            "description": "这是一个完整的示例项目，展示了从文案到视频的完整工作流",
        },
    )
    print(f"{'✓ 创建' if created else '✓ 已存在'} Demo项目: {project.name}")
    print(f"  项目ID: {project.id}")
    print(f"  主题: {project.original_topic}")

    # 创建5个阶段
    stages_created = 0
    for stage_type in [
        "rewrite",
        "storyboard",
        "image_generation",
        "camera_movement",
        "video_generation",
    ]:
        _stage, created = ProjectStage.objects.get_or_create(
            project=project, stage_type=stage_type, defaults={"status": "pending"}
        )
        if created:
            stages_created += 1
        print(f"  {'✓ 创建' if created else '✓ 已存在'} 阶段: {stage_type}")

    # 配置模型
    config, created = ProjectModelConfig.objects.get_or_create(project=project)

    # 清除旧的关联
    config.rewrite_providers.clear()
    config.storyboard_providers.clear()
    config.camera_providers.clear()
    config.image_providers.clear()
    config.video_providers.clear()

    # 添加Mock Providers
    config.rewrite_providers.add(providers["llm"])
    config.storyboard_providers.add(providers["llm"])
    config.camera_providers.add(providers["llm"])
    config.image_providers.add(providers["t2i"])
    config.video_providers.add(providers["i2v"])

    print("\n✓ 模型配置完成:")
    print(f"  - Rewrite: {providers['llm'].name}")
    print(f"  - Storyboard: {providers['llm'].name}")
    print(f"  - Camera: {providers['llm'].name}")
    print(f"  - Image: {providers['t2i'].name}")
    print(f"  - Video: {providers['i2v'].name}")

    return project


def print_summary(user, project):
    """打印初始化摘要"""
    print("\n" + "=" * 70)
    print("✅ Demo环境初始化完成！")
    print("=" * 70)

    print("\n📝 登录信息:")
    print(f"  用户名: {user.username}")
    print("  密码: demo123456")
    print(f"  邮箱: {user.email}")

    print("\n🎯 Demo项目:")
    print(f"  项目名称: {project.name}")
    print(f"  项目ID: {project.id}")
    print(f"  当前状态: {project.status}")

    print("\n🚀 快速开始:")
    print("  1. 访问前端: http://localhost:3000/")
    print("  2. 使用上述账户登录")
    print("  3. 查看Demo项目")
    print("  4. 点击'执行完整工作流'体验")

    print("\n📚 下一步:")
    print("  - 查看5个阶段的配置")
    print("  - 修改提示词模板")
    print("  - 创建自己的项目")
    print("  - 配置真实AI API")

    print("\n💡 提示:")
    print("  - Demo使用Mock AI，响应速度快")
    print("  - 可以随时切换到真实AI API")
    print("  - 查看 docs/QUICKSTART.md 了解更多")

    print("\n" + "=" * 70)


def main():
    """主函数"""
    print("\n" + "🚀" * 35)
    print("  AI Story - Demo环境一键初始化")
    print("  让新用户快速体验完整工作流")
    print("🚀" * 35 + "\n")

    try:
        # Step 1: 创建用户
        user = create_demo_user()

        # Step 2: 创建Mock Providers
        providers = create_mock_providers()

        # Step 3: 创建Prompt模板
        prompt_set = create_prompt_templates(user)

        # Step 4: 创建Demo项目
        project = create_demo_project(user, providers, prompt_set)

        # Step 5: 打印摘要
        print_summary(user, project)

        print("\n✅ 初始化成功！现在可以开始使用系统了。\n")
        return 0

    except Exception as e:
        print(f"\n❌ 初始化失败: {e!s}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
