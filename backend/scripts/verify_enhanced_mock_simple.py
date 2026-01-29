"""
快速验证Enhanced Mock集成
只验证客户端创建，不测试延迟等特性
"""

import os
import sys

# 添加backend到sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

import django

django.setup()

from apps.models.models import ModelProvider
from core.ai_client.factory import _create_mock_client


def main():
    """验证Enhanced Mock集成"""
    print("\n" + "=" * 60)
    print("Enhanced Mock客户端快速验证")
    print("=" * 60)

    # 获取一个LLM Provider
    provider = ModelProvider.objects.filter(provider_type="llm").first()
    if not provider:
        print("❌ 没有找到LLM Provider")
        return False

    print(f"✓ 找到Provider: {provider.name}")

    # 测试1: 标准Mock
    print("\n测试1: 标准Mock客户端")
    try:
        client = _create_mock_client(provider, use_enhanced=False)
        print(f"✓ 创建成功: {client.__class__.__name__}")
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return False

    # 测试2: Enhanced Mock
    print("\n测试2: Enhanced Mock客户端")
    try:
        client = _create_mock_client(provider, use_enhanced=True)
        print(f"✓ 创建成功: {client.__class__.__name__}")

        if "Enhanced" in client.__class__.__name__:
            print("✓ 使用了Enhanced Mock客户端")
        else:
            print("❌ 未使用Enhanced Mock客户端")
            return False
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return False

    # 测试3: Text2Image Enhanced Mock
    print("\n测试3: Text2Image Enhanced Mock")
    t2i_provider = ModelProvider.objects.filter(provider_type="text2image").first()
    if t2i_provider:
        try:
            client = _create_mock_client(t2i_provider, use_enhanced=True)
            print(f"✓ 创建成功: {client.__class__.__name__}")

            if "Enhanced" in client.__class__.__name__:
                print("✓ 使用了Enhanced Mock客户端")
            else:
                print("⚠️ 使用了标准Mock客户端（也可以）")
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            return False
    else:
        print("⚠️ 没有找到Text2Image Provider，跳过")

    print("\n" + "=" * 60)
    print("✅ Enhanced Mock集成验证成功！")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
