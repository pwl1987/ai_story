"""
Mock LLM客户端单元测试
"""
import pytest
from core.ai_client.mock_llm_client import MockLLMClient


@pytest.mark.django_db
class TestMockLLMClient:
    """Mock LLM客户端测试"""
    
    @pytest.fixture
    def client(self):
        """创建Mock客户端实例"""
        return MockLLMClient(
            api_url='http://localhost:8000/api/mock/llm/',
            api_key='mock_key',
            model_name='mock_llm'
        )
    
    def test_initialization(self, client):
        """测试客户端初始化"""
        assert client.api_url == 'http://localhost:8000/api/mock/llm/'
        assert client.api_key == 'mock_key'
        assert client.model_name == 'mock_llm'
    
    @pytest.mark.asyncio
    async def test_generate_success(self, client):
        """测试生成成功"""
        response = await client.generate(
            prompt='测试提示词',
            max_tokens=2000
        )
        
        assert response.success is True
        assert response.text != ''
        assert response.metadata.get('is_mock') is True
    
    @pytest.mark.asyncio
    async def test_generate_with_stage_type(self, client):
        """测试带stage_type的生成"""
        response = await client.generate(
            prompt='测试',
            stage_type='rewrite',
            max_tokens=2000
        )
        
        assert response.success is True
        assert response.metadata.get('stage_type') == 'rewrite'
    
    @pytest.mark.asyncio
    async def test_validate_config(self, client):
        """测试配置验证"""
        result = await client.validate_config()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查"""
        result = await client.health_check()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_generate_with_temperature(self, client):
        """测试带温度参数的生成"""
        response = await client.generate(
            prompt='测试提示词',
            temperature=0.5,
            max_tokens=1000
        )
        
        assert response.success is True
        assert response.metadata.get('temperature') == 0.5
    
    @pytest.mark.asyncio
    async def test_generate_empty_prompt(self, client):
        """测试空提示词"""
        response = await client.generate(
            prompt='',
            max_tokens=1000
        )
        
        # Mock客户端应该能处理空提示词
        assert response.success is True
        assert response.text != ''
