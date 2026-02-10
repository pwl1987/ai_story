# Engines Tests Configuration

import pytest


@pytest.fixture
def sample_llm_config():
    """示例 LLM 引擎配置"""
    return {
        "engine_type": "llm",
        "name": "测试 LLM 引擎",
        "description": "用于文本生成的测试引擎",
        "primary_provider": "ollama",
        "primary_config": {
            "base_url": "http://localhost:11434",
            "model": "llama2:7b",
            "temperature": 0.7,
            "max_tokens": 2000,
        },
        "fallback_provider": "openai",
        "fallback_config": {
            "api_key": "sk-test",
            "model": "gpt-4",
        },
        "fallback_threshold": 3,
        "fallback_timeout": 30,
    }


@pytest.fixture
def sample_image_config():
    """示例图像引擎配置"""
    return {
        "engine_type": "image",
        "name": "测试图像引擎",
        "description": "用于图像生成的测试引擎",
        "primary_provider": "comfyui",
        "primary_config": {
            "base_url": "http://localhost:8188",
            "workflow": "sdxl",
        },
        "fallback_provider": "dalle",
        "fallback_config": {
            "api_key": "sk-test",
        },
    }


@pytest.fixture
def sample_tts_config():
    """示例 TTS 引擎配置"""
    return {
        "engine_type": "tts",
        "name": "测试 TTS 引擎",
        "description": "用于语音合成的测试引擎",
        "primary_provider": "edge-tts",
        "primary_config": {
            "voice": "zh-CN-XiaoxiaoNeural",
            "rate": "+0%",
        },
        "fallback_provider": "elevenlabs",
        "fallback_config": {
            "api_key": "sk-test",
            "voice": "rachel",
        },
    }
