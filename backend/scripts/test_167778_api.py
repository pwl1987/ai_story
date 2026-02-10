"""
快速测试 167778.xyz API
运行: uv run python scripts/test_167778_api.py

功能：
1. 测试 API 连通性
2. 验证响应格式
3. 检查模型可用性
"""

import asyncio
import json
import sys
from httpx import AsyncClient, ConnectError, TimeoutException

# API 配置
API_URL = "https://api.167778.xyz/v1/chat/completions"
API_KEY = "sk-AT5hnGAl2aq0uJAd2lAOu8WTcCA4GAhkhybfeEfaxExOt00C"

# 测试模型列表（按优先级）
TEST_MODELS = [
    "gpt-3.5-turbo",
    "gpt-4",
    "gpt-4o",
    "gpt-4o-mini",
]


async def test_model(model_name: str) -> dict:
    """
    测试指定模型的连通性和响应

    Args:
        model_name: 模型名称

    Returns:
        dict: 测试结果
    """
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己"}],
        "max_tokens": 100,
        "temperature": 0.7,
    }

    print(f"\n{'=' * 60}")
    print(f"🔍 测试模型: {model_name}")
    print(f"{'=' * 60}")

    try:
        async with AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.post(API_URL, json=payload, headers=headers)

            print(f"📡 状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # 显示完整响应（美化格式）
                print("\n📦 完整响应:")
                print(json.dumps(data, indent=2, ensure_ascii=False))

                # 提取关键信息
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})

                    print(f"\n{'=' * 60}")
                    print(f"✅ 模型 {model_name} 可用！")
                    print(f"{'=' * 60}")
                    print(f"💬 AI 回复: {content}")
                    print("\n📊 Token 使用:")
                    print(f"  - 提示 Token: {usage.get('prompt_tokens', 'N/A')}")
                    print(f"  - 完成 Token: {usage.get('completion_tokens', 'N/A')}")
                    print(f"  - 总计 Token: {usage.get('total_tokens', 'N/A')}")

                    return {
                        "model": model_name,
                        "success": True,
                        "content": content,
                        "usage": usage,
                        "response_time": response.elapsed.total_seconds(),
                    }
            else:
                print(f"❌ HTTP 错误: {response.status_code}")
                print(f"响应内容: {response.text}")

                return {
                    "model": model_name,
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "details": response.text,
                }

    except ConnectError as e:
        print(f"❌ 连接失败: {e}")
        return {"model": model_name, "success": False, "error": "ConnectError", "details": str(e)}

    except TimeoutException as e:
        print(f"❌ 请求超时: {e}")
        return {"model": model_name, "success": False, "error": "Timeout", "details": str(e)}

    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return {"model": model_name, "success": False, "error": type(e).__name__, "details": str(e)}


async def main():
    """主测试流程"""
    print("🚀 167778.xyz API 快速验证测试")
    print(f"URL: {API_URL}")
    print(f"密钥: {API_KEY[:20]}...{API_KEY[-10:]}")

    # 逐个测试模型
    results = []
    for model in TEST_MODELS:
        result = await test_model(model)
        results.append(result)

        # 如果找到可用的模型，停止测试
        if result["success"]:
            print(f"\n✅ 找到可用模型: {model}")
            break

    # 总结
    print(f"\n{'=' * 60}")
    print("📊 测试总结")
    print(f"{'=' * 60}")

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    if successful:
        result = successful[0]
        print("\n✅ 测试成功！")
        print(f"可用模型: {result['model']}")
        print(f"响应时间: {result.get('response_time', 'N/A')} 秒")

        # Admin 配置建议
        print(f"\n{'=' * 60}")
        print("🎛️ Admin 配置建议:")
        print(f"{'=' * 60}")
        print("1. 访问: http://10.30.5.62:8000/admin/models/modelprovider/")
        print("2. 添加新 ModelProvider:")
        print("   - Name: 167778.xyz API")
        print("   - Provider Type: LLM")
        print("   - Executor: OpenAIClient")
        print("   - API URL: https://api.167778.xyz/v1")
        print(f"   - API Key: {API_KEY}")
        print(f"   - Model Name: {result['model']}")
        print("   - Timeout: 60")
        print("   - Max Tokens: 2000")
        print("   - Temperature: 0.7")

        return 0

    else:
        print("\n❌ 所有模型测试失败！")
        print("\n失败的模型:")
        for r in failed:
            print(f"  - {r['model']}: {r['error']}")

        print("\n💡 可能的原因:")
        print("  1. 网络不可达（需要配置代理）")
        print("  2. API Key 无效或已过期")
        print("  3. 模型名称不正确")
        print("  4. 服务暂时不可用")

        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
