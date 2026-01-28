"""
测试项目创建脚本
用于创建端到端测试所需的完整测试项目

运行方式:
    cd backend
    uv run python scripts/create_test_project.py

依赖: 需要先运行 setup_mock_env.py 创建Mock Providers
"""
import os
import sys

import django

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model

from apps.models.models import ModelProvider
from apps.projects.models import Project, ProjectModelConfig, ProjectStage
from apps.prompts.models import PromptTemplate, PromptTemplateSet

User = get_user_model()


def create_e2e_test_project():
    """
    创建端到端测试项目

    Returns:
        Project: 创建的测试项目
    """
    print("\n1. 创建/获取测试用户...")
    user, created = User.objects.get_or_create(
        username='e2e_test_user',
        defaults={
            'email': 'e2e_test@example.com'
        }
    )
    if created:
        # 如果是Django默认User模型，需要设置密码
        try:
            user.set_password('test_password')
            user.save()
            print(f"✓ 创建用户: {user.username}")
        except AttributeError:
            # 如果User模型没有set_password方法（自定义模型）
            print(f"✓ 获取用户: {user.username}")
    else:
        print(f"− 已存在用户: {user.username}")

    print("\n2. 创建PromptTemplateSet...")
    prompt_set, created = PromptTemplateSet.objects.get_or_create(
        name='E2E Test Prompt Set',
        defaults={
            'description': '端到端测试使用的提示词集',
            'is_active': True,
            'created_by': user
        }
    )
    if created:
        print(f"✓ 创建提示词集: {prompt_set.name}")
    else:
        print(f"− 已存在提示词集: {prompt_set.name}")

    print("\n3. 创建/更新5个PromptTemplate...")
    stage_templates = {
        'rewrite': '请改写以下文案，使其更加生动有趣：\n\n{{ raw_text }}',
        'storyboard': '根据以下改写后的文案，生成分镜描述（JSON格式）：\n\n{{ rewritten_text }}\n\n请生成3个场景的分镜。',
        'image_generation': '为以下场景生成英文图片提示词：\n\n{{ scene_description }}',
        'camera_movement': '为以下场景设计运镜方案：\n\n{{ scene_description }}',
        'video_generation': '根据以下图片和运镜方案生成视频：\n图片: {{ image_url }}\n运镜: {{ camera_movement }}'
    }

    for stage_type, template_content in stage_templates.items():
        _template, created = PromptTemplate.objects.get_or_create(
            template_set=prompt_set,
            stage_type=stage_type,
            defaults={
                'template_content': template_content,
                'is_active': True
            }
        )
        if created:
            print(f"  ✓ 创建模板: {stage_type}")
        else:
            print(f"  − 已存在模板: {stage_type}")

    print("\n4. 获取Mock Providers...")
    try:
        mock_llm = ModelProvider.objects.get(name='Mock LLM for E2E Test')
        mock_t2i = ModelProvider.objects.get(name='Mock Text2Image for E2E Test')
        mock_i2v = ModelProvider.objects.get(name='Mock Image2Video for E2E Test')
        print("✓ 获取Mock Providers成功")
    except ModelProvider.DoesNotExist as e:
        print(f"✗ Mock Provider不存在: {e}")
        print("请先运行: uv run python scripts/setup_mock_env.py")
        raise

    print("\n5. 创建测试项目...")
    # 先删除已存在的同名测试项目
    Project.objects.filter(name='E2E Test Project').delete()

    project = Project.objects.create(
        name='E2E Test Project',
        description='端到端完整验证测试项目',
        original_topic='宁静的小镇，年轻的画家',
        status='draft',
        prompt_template_set=prompt_set,
        user=user
    )
    print(f"✓ 创建项目: {project.name} (ID: {project.id})")

    print("\n6. 创建5个项目阶段...")
    stages = []
    for stage_type in ['rewrite', 'storyboard', 'image_generation', 'camera_movement', 'video_generation']:
        stage = ProjectStage.objects.create(
            project=project,
            stage_type=stage_type,
            status='pending'
        )
        stages.append(stage)
        print(f"  ✓ 创建阶段: {stage_type}")

    print("\n7. 配置项目模型...")
    config = ProjectModelConfig.objects.create(
        project=project,
        load_balance_strategy='weighted'
    )

    # 配置各阶段的模型
    config.rewrite_providers.add(mock_llm)
    config.storyboard_providers.add(mock_llm)
    config.camera_providers.add(mock_llm)
    config.image_providers.add(mock_t2i)
    config.video_providers.add(mock_i2v)

    print("✓ 配置模型完成")

    return project


def main():
    """主函数"""
    print("=" * 60)
    print("创建E2E测试项目")
    print("=" * 60)

    try:
        project = create_e2e_test_project()

        print("\n" + "=" * 60)
        print("✓ 测试项目创建完成")
        print("=" * 60)

        print("\n项目信息:")
        print(f"  ID: {project.id}")
        print(f"  名称: {project.name}")
        print(f"  状态: {project.status}")
        print(f"  原始主题: {project.original_topic}")
        print(f"  阶段数: {project.stages.count()}")

        return 0
    except Exception as e:
        print(f"\n✗ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
