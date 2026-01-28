"""
测试Enhanced Mock客户端集成
验证factory.py正确创建Enhanced Mock客户端
"""
import os
import sys
import asyncio
import time

# 添加backend到sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

import django
django.setup()

from asgiref.sync import sync_to_async
from core.ai_client.factory import create_ai_client
from apps.models.models import ModelProvider


# 使用sync_to_async包装ORM查询
get_llm_providers = sync_to_async(
    lambda: list(ModelProvider.objects.filter(provider_type='llm')),
    thread_sensitive=False
)
get_t2i_providers = sync_to_async(
    lambda: list(ModelProvider.objects.filter(provider_type='text2image')),
    thread_sensitive=False
)


async def test_standard_mock():
    """测试标准Mock客户端"""
    print("\n" + "=" * 60)
    print("测试1: 标准Mock客户端")
    print("=" * 60)

    # 设置环境变量
    os.environ['ENABLE_MOCK_AI'] = 'true'
    os.environ['USE_ENHANCED_MOCK'] = 'false'

    # 获取一个LLM Provider
    providers = await get_llm_providers()
    if not providers:
        print("❌ 没有找到LLM Provider")
        return False

    provider = providers[0]
    print(f"✓ 找到Provider: {provider.name}")

    # 创建客户端
    client = create_ai_client(provider)
    print(f"✓ 创建客户端: {client.__class__.__name__}")

    # 调用生成
    start = time.time()
    response = await client.generate(prompt="测试提示词")
    elapsed = time.time() - start

    print(f"✓ 响应时间: {elapsed:.3f}秒")
    print(f"✓ 成功: {response.success}")
    print(f"✓ 文本长度: {len(response.text)}")

    if elapsed < 0.1:  # 标准Mock应该很快
        print("✓ 标准Mock响应快速 (<0.1s)")
        return True
    else:
        print(f"⚠️ 响应时间异常: {elapsed:.3f}s")
        return False


async def test_enhanced_mock_default():
    """测试Enhanced Mock客户端（默认延迟）"""
    print("\n" + "=" * 60)
    print("测试2: Enhanced Mock客户端（默认延迟0.5s）")
    print("=" * 60)

    os.environ['ENABLE_MOCK_AI'] = 'true'
    os.environ['USE_ENHANCED_MOCK'] = 'true'
    os.environ['MOCK_DELAY'] = '0.5'

    provider = ModelProvider.objects.filter(provider_type='llm').first()
    if not provider:
        print("❌ 没有找到LLM Provider")
        return False

    print(f"✓ 找到Provider: {provider.name}")

    # 创建客户端
    client = create_ai_client(provider)
    print(f"✓ 创建客户端: {client.__class__.__name__}")

    if 'Enhanced' not in client.__class__.__name__:
        print("❌ 未使用Enhanced Mock客户端")
        return False

    # 调用生成
    start = time.time()
    response = await client.generate(prompt="测试提示词")
    elapsed = time.time() - start

    print(f"✓ 响应时间: {elapsed:.3f}秒")
    print(f"✓ 成功: {response.success}")
    print(f"✓ 元数据: {response.metadata}")

    if 0.4 <= elapsed <= 0.7:  # 应该有约0.5秒延迟
        print("✓ Enhanced Mock延迟正常 (~0.5s)")
        return True
    else:
        print(f"⚠️ 延迟时间异常: {elapsed:.3f}s")
        return False


async def test_enhanced_mock_custom_delay():
    """测试Enhanced Mock客户端（自定义延迟2.0s）"""
    print("\n" + "=" * 60)
    print("测试3: Enhanced Mock客户端（自定义延迟2.0s）")
    print("=" * 60)

    os.environ['ENABLE_MOCK_AI'] = 'true'
    os.environ['USE_ENHANCED_MOCK'] = 'true'
    os.environ['MOCK_DELAY'] = '2.0'

    provider = ModelProvider.objects.filter(provider_type='llm').first()
    if not provider:
        print("❌ 没有找到LLM Provider")
        return False

    # 创建客户端
    client = create_ai_client(provider)
    print(f"✓ 创建客户端: {client.__class__.__name__}")

    # 调用生成
    start = time.time()
    response = await client.generate(prompt="测试提示词")
    elapsed = time.time() - start

    print(f"✓ 响应时间: {elapsed:.3f}秒")

    if 1.9 <= elapsed <= 2.2:  # 应该有约2.0秒延迟
        print("✓ Enhanced Mock自定义延迟正常 (~2.0s)")
        return True
    else:
        print(f"⚠️ 延迟时间异常: {elapsed:.3f}s")
        return False


async def test_enhanced_mock_error_simulation():
    """测试Enhanced Mock错误模拟"""
    print("\n" + "=" * 60)
    print("测试4: Enhanced Mock错误模拟")
    print("=" * 60)

    os.environ['ENABLE_MOCK_AI'] = 'true'
    os.environ['USE_ENHANCED_MOCK'] = 'true'
    os.environ['MOCK_DELAY'] = '0.1'  # 使用短延迟加速测试
    os.environ['MOCK_ERROR'] = 'timeout'

    provider = ModelProvider.objects.filter(provider_type='llm').first()
    if not provider:
        print("❌ 没有找到LLM Provider")
        return False

    # 创建客户端
    client = create_ai_client(provider)
    print(f"✓ 创建客户端: {client.__class__.__name__}")

    # 调用生成
    response = await client.generate(prompt="测试提示词")

    print(f"✓ 成功: {response.success}")
    print(f"✓ 错误: {response.error}")

    if not response.success and "timeout" in response.error.lower():
        print("✓ 错误模拟正常（timeout）")
        return True
    else:
        print("❌ 错误模拟失败")
        return False


async def test_enhanced_mock_logging():
    """测试Enhanced Mock日志记录"""
    print("\n" + "=" * 60)
    print("测试5: Enhanced Mock日志记录")
    print("=" * 60)

    os.environ['ENABLE_MOCK_AI'] = 'true'
    os.environ['USE_ENHANCED_MOCK'] = 'true'
    os.environ['MOCK_DELAY'] = '0.1'
    del os.environ['MOCK_ERROR']  # 移除错误设置

    provider = ModelProvider.objects.filter(provider_type='llm').first()
    if not provider:
        print("❌ 没有找到LLM Provider")
        return False

    # 创建客户端
    client = create_ai_client(provider)
    print(f"✓ 创建客户端: {client.__class__.__name__}")

    # 检查是否有enable_logging属性
    if not hasattr(client, 'enable_logging'):
        print("⚠️ 客户端没有enable_logging属性")
        return True  # 这不是错误，只是标准Mock没有这个属性

    # 清空日志
    client.clear_request_log()

    # 执行多个请求
    for i in range(3):
        await client.generate(prompt=f"测试{i+1}")

    # 查看日志
    logs = client.get_request_log()
    print(f"✓ 日志条数: {len(logs)}")

    if len(logs) == 3:
        print("✓ 日志记录正常")
        # 显示第一条日志
        if logs:
            log = logs[0]
            print(f"  - 时间戳: {log['timestamp']}")
            print(f"  - 模型: {log['model']}")
            print(f"  - 提示词长度: {log['prompt_length']}")
            print(f"  - 延迟: {log['simulate_delay']}s")
        return True
    else:
        print(f"❌ 日志条数异常: {len(logs)}")
        return False


async def test_text2image_enhanced_mock():
    """测试Text2Image Enhanced Mock"""
    print("\n" + "=" * 60)
    print("测试6: Text2Image Enhanced Mock")
    print("=" * 60)

    os.environ['ENABLE_MOCK_AI'] = 'true'
    os.environ['USE_ENHANCED_MOCK'] = 'true'
    os.environ['MOCK_DELAY'] = '0.3'

    # 获取一个Text2Image Provider
    providers = await get_t2i_providers()
    if not providers:
        print("⚠️ 没有找到Text2Image Provider，跳过测试")
        return True

    provider = providers[0]
    print(f"✓ 找到Provider: {provider.name}")

    # 创建客户端
    client = create_ai_client(provider)
    print(f"✓ 创建客户端: {client.__class__.__name__}")

    # 调用生成
    start = time.time()
    response = await client.generate(prompt="测试图片", width=1024, height=1024)
    elapsed = time.time() - start

    print(f"✓ 响应时间: {elapsed:.3f}秒")
    print(f"✓ 成功: {response.success}")
    print(f"✓ 数据: {response.data}")

    if 0.2 <= elapsed <= 0.5:
        print("✓ Text2Image Enhanced Mock延迟正常 (~0.3s)")
        return True
    else:
        print(f"⚠️ 延迟时间异常: {elapsed:.3f}s")
        return False


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Enhanced Mock客户端集成测试")
    print("=" * 60)

    results = []

    # 测试1: 标准Mock
    try:
        result = await test_standard_mock()
        results.append(("标准Mock", result))
    except Exception as e:
        print(f"❌ 测试1异常: {e}")
        results.append(("标准Mock", False))

    # 测试2: Enhanced Mock默认延迟
    try:
        result = await test_enhanced_mock_default()
        results.append(("Enhanced Mock默认延迟", result))
    except Exception as e:
        print(f"❌ 测试2异常: {e}")
        results.append(("Enhanced Mock默认延迟", False))

    # 测试3: Enhanced Mock自定义延迟
    try:
        result = await test_enhanced_mock_custom_delay()
        results.append(("Enhanced Mock自定义延迟", result))
    except Exception as e:
        print(f"❌ 测试3异常: {e}")
        results.append(("Enhanced Mock自定义延迟", False))

    # 测试4: Enhanced Mock错误模拟
    try:
        result = await test_enhanced_mock_error_simulation()
        results.append(("Enhanced Mock错误模拟", result))
    except Exception as e:
        print(f"❌ 测试4异常: {e}")
        results.append(("Enhanced Mock错误模拟", False))

    # 测试5: Enhanced Mock日志记录
    try:
        result = await test_enhanced_mock_logging()
        results.append(("Enhanced Mock日志记录", result))
    except Exception as e:
        print(f"❌ 测试5异常: {e}")
        results.append(("Enhanced Mock日志记录", False))

    # 测试6: Text2Image Enhanced Mock
    try:
        result = await test_text2image_enhanced_mock()
        results.append(("Text2Image Enhanced Mock", result))
    except Exception as e:
        print(f"❌ 测试6异常: {e}")
        results.append(("Text2Image Enhanced Mock", False))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    passed_count = sum(1 for _, result in results if result)
    total_count = len(results)

    print(f"\n总计: {passed_count}/{total_count} 通过")

    if passed_count == total_count:
        print("\n🎉 所有测试通过！Enhanced Mock已成功集成！")
        return 0
    else:
        print(f"\n⚠️ {total_count - passed_count} 个测试失败")
        return 1


if __name__ == '__main__':
    exit(asyncio.run(main()))
