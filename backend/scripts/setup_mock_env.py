"""
Mock环境配置脚本
用于创建端到端测试所需的Mock ModelProvider

运行方式:
    cd backend
    uv run python scripts/setup_mock_env.py
"""
import os
import sys
import django

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.models.models import ModelProvider


def create_mock_providers():
    """
    创建Mock环境的ModelProvider

    Returns:
        Dict[str, ModelProvider]: 包含3个Mock providers的字典
    """
    providers = {}

    # 1. Mock LLM Provider
    mock_llm, created = ModelProvider.objects.get_or_create(
        name='Mock LLM for E2E Test',
        defaults={
            'provider_type': 'llm',
            'executor_class': 'core.ai_client.mock_llm_client.MockLLMClient',
            'api_url': 'mock://localhost',
            'api_key': '',
            'model_name': 'mock-llm',
            'max_tokens': 2000,
            'temperature': 0.7,
            'is_active': True,
            'priority': 10,
            'rate_limit_rpm': 1000,
            'rate_limit_rpd': 10000
        }
    )
    providers['llm'] = mock_llm
    print(f"{'✓ 创建' if created else '− 已存在'} Mock LLM Provider: {mock_llm.name}")

    # 2. Mock Text2Image Provider
    mock_t2i, created = ModelProvider.objects.get_or_create(
        name='Mock Text2Image for E2E Test',
        defaults={
            'provider_type': 'text2image',
            'executor_class': 'core.ai_client.mock_text2image_client.MockText2ImageClient',
            'api_url': 'mock://localhost',
            'api_key': '',
            'model_name': 'mock-t2i',
            'is_active': True,
            'priority': 10,
            'rate_limit_rpm': 100,
            'rate_limit_rpd': 1000
        }
    )
    providers['t2i'] = mock_t2i
    print(f"{'✓ 创建' if created else '− 已存在'} Mock Text2Image Provider: {mock_t2i.name}")

    # 3. Mock Image2Video Provider
    mock_i2v, created = ModelProvider.objects.get_or_create(
        name='Mock Image2Video for E2E Test',
        defaults={
            'provider_type': 'image2video',
            'executor_class': 'core.ai_client.mock_image2video_client.MockImage2VideoClient',
            'api_url': 'mock://localhost',
            'api_key': '',
            'model_name': 'mock-i2v',
            'is_active': True,
            'priority': 10,
            'rate_limit_rpm': 50,
            'rate_limit_rpd': 500
        }
    )
    providers['i2v'] = mock_i2v
    print(f"{'✓ 创建' if created else '− 已存在'} Mock Image2Video Provider: {mock_i2v.name}")

    return providers


def main():
    """主函数"""
    print("=" * 60)
    print("Mock环境配置")
    print("=" * 60)

    try:
        providers = create_mock_providers()
        print("\n" + "=" * 60)
        print("✓ Mock环境配置完成")
        print("=" * 60)
        print(f"\n创建的Providers:")
        for key, provider in providers.items():
            print(f"  - {key}: {provider.name} (ID: {provider.id})")
        return 0
    except Exception as e:
        print(f"\n✗ 配置失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
