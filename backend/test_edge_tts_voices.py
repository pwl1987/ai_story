"""测试 edge-tts 音色列表功能"""

import asyncio
import edge_tts


async def main():
    """获取并打印前3个中文音色"""
    voices = await edge_tts.list_voices()

    # 过滤中文音色
    zh_voices = [v for v in voices if v.get("Locale", "").startswith("zh-")]

    print(f"总音色数: {len(voices)}")
    print(f"中文音色数: {len(zh_voices)}")
    print("\n前5个中文音色:")
    for voice in zh_voices[:5]:
        print(f"  Name: {voice.get('Name')}")
        print(f"  Locale: {voice.get('Locale')}")
        print(f"  Gender: {voice.get('Gender')}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
