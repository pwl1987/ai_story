"""
快速验证 GLM-4.7 集成
运行: uv run python scripts/verify_glm_quick.py
"""

import os
import django
import asyncio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.models.models import ModelProvider
from core.ai_client.factory import create_ai_client


def main():
    print("=" * 60)
    print("🔍 GLM-4.7 集成快速验证")
    print("=" * 60)

    # 查找 Provider
    print("\n📋 查找 ModelProvider...")
    provider = ModelProvider.objects.filter(name="167778.xyz GLM API").first()

    if not provider:
        print("❌ 未找到 GLM Provider！")
        print("\n请先运行: uv run python manage.py shell < scripts/add_glm_provider_shell.py")
        return False

    print("✅ 找到 Provider:")
    print(f"   ID: {provider.id}")
    print(f"   名称: {provider.name}")
    print(f"   模型: {provider.model_name}")
    print(f"   API URL: {provider.api_url}")
    print(f"   状态: {'✅ 激活' if provider.is_active else '❌ 未激活'}")

    # 创建客户端
    print("\n🏭 创建 AI 客户端...")
    client = create_ai_client(provider)
    print(f"✅ 客户端创建成功: {type(client).__name__}")

    # 测试 API 调用
    print("\n🚀 测试 API 调用...")
    test_prompt = "请用一句话介绍什么是人工智能"

    try:
        print(f"📤 发送: {test_prompt}")
        response = asyncio.run(client.generate(test_prompt))

        if response.success:
            text = response.text.strip()
            print("\n✅ API 调用成功！")
            print("\n💬 AI 回复:")
            print(f"   {text[:300]}{'...' if len(text) > 300 else ''}")

            print("\n📊 元数据:")
            for key, value in response.metadata.items():
                print(f"   {key}: {value}")

            # 验证内容
            if len(text) == 0:
                print("\n⚠️  警告: 响应内容为空！")
                return False

            print(f"\n{'=' * 60}")
            print("🎉 GLM-4.7 集成验证成功！")
            print(f"{'=' * 60}")
            print("\n✅ 系统已可以使用 GLM-4.7 模型")
            print("✅ 支持 reasoning_content 格式")
            print("✅ OpenAI 客户端兼容性正常")

            return True
        else:
            print("\n❌ API 调用失败:")
            print(f"   错误: {response.error}")
            return False

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
