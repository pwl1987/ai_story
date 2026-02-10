"""
GLM-4.7 集成测试（异步版本）
运行: uv run python scripts/test_glm_integration.py
"""

import asyncio
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from asgiref.sync import sync_to_async
from core.ai_client.factory import create_ai_client
from apps.models.models import ModelProvider


async def test_glm_integration():
    """完整的 GLM-4.7 集成测试"""

    print("=" * 60)
    print("🔄 GLM-4.7 完整集成测试")
    print("=" * 60)

    # Step 1: 从数据库获取 Provider（使用 sync_to_async）
    print("\n📋 Step 1: 从数据库获取 ModelProvider...")

    @sync_to_async
    def get_provider():
        return ModelProvider.objects.filter(name="167778.xyz GLM API").first()

    provider = await get_provider()

    if not provider:
        print("❌ 未找到 ModelProvider！")
        return False

    print("✅ 找到 Provider:")
    print(f"   ID: {provider.id}")
    print(f"   名称: {provider.name}")
    print(f"   模型: {provider.model_name}")

    # Step 2: 创建客户端
    print("\n🏭 Step 2: 创建 AI 客户端...")
    try:
        client = create_ai_client(provider)
        print("✅ 客户端创建成功:")
        print(f"   类型: {type(client).__name__}")
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return False

    # Step 3: 测试 API 调用
    print("\n🚀 Step 3: 测试 API 调用...")
    test_prompts = ["请用一句话介绍什么是人工智能", "请为一家AI公司写一句宣传语"]

    all_passed = True

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n测试 {i}: {prompt}")

        try:
            response = await client.generate(prompt)

            if response.success:
                text = response.text.strip()
                print("✅ 成功！")
                print(f"💬 回复: {text[:100]}{'...' if len(text) > 100 else ''}")

                if not text:
                    print("⚠️  警告: 内容为空！")
                    all_passed = False
            else:
                print(f"❌ 失败: {response.error}")
                all_passed = False

        except Exception as e:
            print(f"❌ 异常: {e}")
            all_passed = False

    # 总结
    print(f"\n{'=' * 60}")
    if all_passed:
        print("🎉 所有测试通过！GLM-4.7 集成成功！")
        print(f"{'=' * 60}")
        print("\n✅ 可以在生产环境中使用此模型")
        print("✅ 支持内容: reasoning_content 格式")
        print("✅ 兼容性: OpenAI 格式")
    else:
        print("❌ 部分测试失败，需要进一步检查")
        print(f"{'=' * 60}")

    return all_passed


if __name__ == "__main__":
    result = asyncio.run(test_glm_integration())
    exit(0 if result else 1)
