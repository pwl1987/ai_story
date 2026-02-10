"""
使用正确的模型名称测试 167778.xyz API
模型: GLM-4.7 (智谱AI)
运行: uv run python scripts/test_glm_api.py
"""

import asyncio
import json
from httpx import AsyncClient

API_URL = "https://api.167778.xyz/v1/chat/completions"
API_KEY = "sk-AT5hnGAl2aq0uJAd2lAOu8WTcCA4GAhkhybfeEfaxExOt00C"
MODEL_NAME = "GLM-4.7"


async def test_glm_api():
    """测试 GLM-4.7 模型"""
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    # 测试用例
    test_cases = [
        {
            "name": "简单问候",
            "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己"}],
            "max_tokens": 100,
        },
        {
            "name": "文案生成",
            "messages": [{"role": "user", "content": "请为一家AI公司写一句简短的宣传语"}],
            "max_tokens": 50,
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"测试 {i}: {test_case['name']}")
        print(f"{'=' * 60}")

        payload = {
            "model": MODEL_NAME,
            "messages": test_case["messages"],
            "max_tokens": test_case["max_tokens"],
            "temperature": 0.7,
        }

        print("📤 发送请求...")
        print(f"模型: {MODEL_NAME}")
        print(f"提示: {test_case['messages'][0]['content']}")

        try:
            async with AsyncClient(timeout=60.0, verify=False) as client:
                response = await client.post(API_URL, json=payload, headers=headers)

                print(f"\n📥 响应状态: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()

                    # 提取响应
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {})

                        print("\n✅ 测试成功！")
                        print("\n💬 AI 回复:")
                        print(f"  {content}")

                        print("\n📊 Token 使用:")
                        print(f"  提示: {usage.get('prompt_tokens', 'N/A')}")
                        print(f"  完成: {usage.get('completion_tokens', 'N/A')}")
                        print(f"  总计: {usage.get('total_tokens', 'N/A')}")

                        # 显示完整响应
                        print("\n📦 完整响应:")
                        print(json.dumps(data, indent=2, ensure_ascii=False))

                        print(f"\n{'=' * 60}")
                        print("✅ API 测试完全通过！")
                        print(f"{'=' * 60}")

                        # 集成建议
                        print("\n🎯 系统集成建议:")
                        print(f"{'=' * 60}")
                        print("\n1. Admin 配置信息:")
                        print("   Name: 167778.xyz GLM API")
                        print("   Provider Type: LLM")
                        print("   Executor: OpenAIClient (兼容)")
                        print("   API URL: https://api.167778.xyz/v1")
                        print(f"   API Key: {API_KEY}")
                        print(f"   Model Name: {MODEL_NAME}")
                        print("   Timeout: 60")
                        print("   Max Tokens: 2000")
                        print("   Temperature: 0.7")

                        print("\n2. 运行配置脚本:")
                        print("   uv run python scripts/add_glm_provider.py")

                        print("\n3. 或手动配置:")
                        print("   访问: http://10.30.5.62:8000/admin/models/modelprovider/")

                        return True
                else:
                    print(f"❌ 错误响应: {response.status_code}")
                    print(f"内容: {response.text}")
                    return False

        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return False

    return True


async def main():
    """主流程"""
    print("🚀 GLM-4.7 API 验证测试")
    print(f"URL: {API_URL}")
    print(f"模型: {MODEL_NAME}")
    print(f"密钥: {API_KEY[:20]}...{API_KEY[-10:]}")

    success = await test_glm_api()

    if success:
        print(f"\n{'=' * 60}")
        print("🎉 恭喜！API 验证成功，可以集成到系统！")
        print(f"{'=' * 60}")
        return 0
    else:
        print(f"\n{'=' * 60}")
        print("❌ API 测试失败")
        print(f"{'=' * 60}")
        return 1


if __name__ == "__main__":
    import sys

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
