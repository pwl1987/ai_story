"""
探测 167778.xyz API 支持的模型名称
运行: uv run python scripts/probe_models.py
"""

import asyncio
import json
from httpx import AsyncClient

API_BASE = "https://api.167778.xyz/v1"
API_KEY = "sk-AT5hnGAl2aq0uJAd2lAOu8WTcCA4GAhkhybfeEfaxExOt00C"

# 常见模型名称变体
MODEL_VARIANTS = [
    # OpenAI 标准
    "gpt-3.5-turbo",
    "gpt-4",
    "gpt-4o",
    "gpt-4o-mini",
    # 去点号变体
    "gpt-35-turbo",
    "gpt35-turbo",
    "gpt-4-32k",
    "gpt-4-1106-preview",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-16k",
    # 下划线变体
    "gpt_3_5_turbo",
    "gpt_4_turbo",
    # 简化名称
    "chatgpt",
    "gpt",
    "gpt4",
    "gpt35",
    # 错误信息提到的
    "default",
    # 其他可能
    "claude-3-sonnet",
    "claude-3-opus",
]


async def try_model(model_name: str) -> dict:
    """尝试使用指定模型"""
    url = f"{API_BASE}/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 10,
    }

    try:
        async with AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                return {"model": model_name, "success": True, "status": response.status_code}
            else:
                data = response.json()
                return {
                    "model": model_name,
                    "success": False,
                    "status": response.status_code,
                    "error": data.get("error", {}).get("code", "unknown"),
                }
    except Exception as e:
        return {"model": model_name, "success": False, "error": type(e).__name__}


async def main():
    """主探测流程"""
    print("🔍 开始探测支持的模型名称...")
    print(f"API Base: {API_BASE}")
    print(f"将尝试 {len(MODEL_VARIANTS)} 种模型名称\n")

    successful = []
    failed = []

    for i, model in enumerate(MODEL_VARIANTS, 1):
        print(f"[{i}/{len(MODEL_VARIANTS)}] 测试: {model}...", end=" ")
        result = await try_model(model)

        if result["success"]:
            print("✅ 成功！")
            successful.append(result)
        else:
            error = result.get("error", "unknown")
            print(f"❌ ({error})")
            failed.append(result)

    # 尝试获取模型列表
    print(f"\n{'=' * 60}")
    print("📋 尝试获取官方模型列表...")
    print(f"{'=' * 60}")

    try:
        url = f"{API_BASE}/models"
        headers = {"Authorization": f"Bearer {API_KEY}"}

        async with AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                print("✅ 成功获取模型列表！")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(f"❌ 获取失败: {response.status_code}")
                print(f"响应: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    # 总结
    print(f"\n{'=' * 60}")
    print("📊 探测总结")
    print(f"{'=' * 60}")

    if successful:
        print(f"\n✅ 找到 {len(successful)} 个可用模型:")
        for r in successful:
            print(f"  - {r['model']}")
    else:
        print("\n❌ 未找到可用模型")
        print("\n建议:")
        print("  1. 联系 API 提供商确认模型名称")
        print("  2. 查看官方文档")
        print("  3. 检查 API Key 配额和权限")


if __name__ == "__main__":
    asyncio.run(main())
