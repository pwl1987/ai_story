"""
端到端测试：GLM-4.7 完整集成
验证：数据库 → 工厂方法 → API 调用 → 响应处理
运行: uv run python manage.py shell < scripts/test_e2e_glm.py
"""

import asyncio

from apps.models.models import ModelProvider
from core.ai_client.factory import create_ai_client


async def test_e2e():
    """端到端测试流程"""

    print("=" * 60)
    print("🔄 端到端集成测试 - GLM-4.7")
    print("=" * 60)

    # Step 1: 从数据库获取 ModelProvider
    print("\n📋 Step 1: 从数据库获取 ModelProvider...")
    provider = ModelProvider.objects.filter(name="167778.xyz GLM API").first()

    if not provider:
        print("❌ 未找到 ModelProvider！请先运行添加脚本。")
        return False

    print("✅ 找到 Provider:")
    print(f"   ID: {provider.id}")
    print(f"   名称: {provider.name}")
    print(f"   模型: {provider.model_name}")
    print(f"   执行器: {provider.executor_class}")

    # Step 2: 使用工厂方法创建客户端
    print("\n🏭 Step 2: 使用工厂方法创建客户端...")
    try:
        client = create_ai_client(provider)
        print("✅ 客户端创建成功:")
        print(f"   类型: {type(client).__name__}")
        print(f"   API URL: {client.api_url}")
        print(f"   模型: {client.model_name}")
    except Exception as e:
        print(f"❌ 客户端创建失败: {e}")
        return False

    # Step 3: 测试 API 调用
    print("\n🚀 Step 3: 测试 API 调用...")
    test_prompt = "请用一句话介绍什么是人工智能"

    try:
        print(f"📤 发送提示: {test_prompt}")
        response = await client.generate(test_prompt)

        if response.success:
            print("✅ API 调用成功！")
            print("\n💬 AI 回复:")
            print(f"   {response.text}")

            print("\n📊 元数据:")
            for key, value in response.metadata.items():
                print(f"   {key}: {value}")

            # 验证内容不为空
            if not response.text or response.text.strip() == "":
                print("\n⚠️  警告: 响应内容为空！")
                print("   这可能意味着 reasoning_content 提取失败")
                return False

            print(f"\n{'=' * 60}")
            print("🎉 端到端测试完全通过！")
            print(f"{'=' * 60}")
            return True
        else:
            print("❌ API 调用失败:")
            print(f"   错误: {response.error}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


# 运行异步测试
asyncio.run(test_e2e())
