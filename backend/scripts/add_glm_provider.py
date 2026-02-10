"""
添加 GLM-4.7 ModelProvider 到系统
运行: uv run python scripts/add_glm_provider.py
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.models.models import ModelProvider


def add_glm_provider():
    """添加 GLM-4.7 模型提供商"""

    # 检查是否已存在
    existing = ModelProvider.objects.filter(name="167778.xyz GLM API").first()
    if existing:
        print(f"⚠️  ModelProvider 已存在: {existing.name}")
        print(f"   ID: {existing.id}")
        print(f"   访问: http://10.30.5.62:8000/admin/models/modelprovider/{existing.id}/change/")
        return existing

    # 创建新的 ModelProvider
    provider = ModelProvider.objects.create(
        name="167778.xyz GLM API",
        provider_type="llm",
        executor_class="core.ai_client.openai_client.OpenAIClient",
        api_url="https://api.167778.xyz/v1",
        api_key="sk-AT5hnGAl2aq0uJAd2lAOu8WTcCA4GAhkhybfeEfaxExOt00C",
        model_name="GLM-4.7",
        is_active=True,
        timeout=60,
        max_tokens=2000,
        temperature=0.7,
        top_p=1.0,
        priority=10,
        description="智谱 GLM-4.7 模型，通过 167778.xyz 代理服务访问。支持 OpenAI 兼容格式。",
        rate_limit_rpm=60,
        rate_limit_rpd=1000,
    )

    print("✅ ModelProvider 创建成功！")
    print("\n📋 配置信息:")
    print(f"   ID: {provider.id}")
    print(f"   名称: {provider.name}")
    print(f"   类型: {provider.provider_type}")
    print(f"   执行器: {provider.executor_class}")
    print(f"   API URL: {provider.api_url}")
    print(f"   模型: {provider.model_name}")
    print(f"   状态: {'✅ 激活' if provider.is_active else '❌ 未激活'}")

    print("\n🎛️  Admin 访问:")
    print(f"   http://10.30.5.62:8000/admin/models/modelprovider/{provider.id}/change/")

    print("\n📝 说明:")
    print("   - 模型: GLM-4.7 (智谱AI)")
    print("   - 响应格式: 支持 reasoning_content")
    print("   - 兼容性: OpenAI 格式兼容")
    print("   - 用途: LLM 文案生成")

    return provider


if __name__ == "__main__":
    provider = add_glm_provider()

    print(f"\n{'=' * 60}")
    print("🎉 完成！GLM-4.7 已添加到系统")
    print(f"{'=' * 60}")
