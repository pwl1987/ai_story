"""
提示词评估服务测试
测试PromptEvaluationService的业务逻辑
遵循SOLID原则和TDD红绿重构循环
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from asgiref.sync import sync_to_async

from apps.prompts.services import PromptEvaluationService
from apps.prompts.tests.factories import PromptTemplateFactory


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestPromptEvaluationService:
    """测试PromptEvaluationService"""

    async def test_evaluate_prompt_success(self):
        """测试评估提示词 - 成功场景"""
        # Given
        service = PromptEvaluationService()
        template = await sync_to_async(PromptTemplateFactory)(
            template_content="测试提示词: {{topic}}",
            variables={'topic': 'string'}
        )

        mock_response = Mock()
        mock_response.success = True
        mock_response.data = {
            'score': 8.5,
            'clarity': 9.0,
            'specificity': 8.0,
            'creativity': 8.5,
            'strengths': ['清晰明确', '结构良好'],
            'weaknesses': ['可以更具体'],
            'suggestions': ['添加更多细节']
        }

        mock_client = AsyncMock()
        mock_client.generate_text.return_value = mock_response

        # When
        with patch.object(
            service,
            '_get_ai_client',
            return_value=mock_client
        ):
            result = await service.evaluate_prompt(template)

        # Then
        assert result['score'] == 8.5
        assert result['clarity'] == 9.0
        assert result['specificity'] == 8.0
        assert result['creativity'] == 8.5
        assert len(result['strengths']) == 2
        assert len(result['weaknesses']) == 1
        assert len(result['suggestions']) == 1

        # 验证AI客户端被正确调用
        mock_client.generate_text.assert_called_once()
        call_args = mock_client.generate_text.call_args
        assert '测试提示词' in str(call_args)

    async def test_evaluate_prompt_ai_failure(self):
        """测试评估提示词 - AI调用失败"""
        # Given
        service = PromptEvaluationService()
        template = await sync_to_async(PromptTemplateFactory)()

        mock_response = Mock()
        mock_response.success = False
        mock_response.error = "AI服务不可用"

        mock_client = AsyncMock()
        mock_client.generate_text.return_value = mock_response

        # When & Then
        with patch.object(
            service,
            '_get_ai_client',
            return_value=mock_client
        ), pytest.raises(Exception, match="AI评估失败"):
            await service.evaluate_prompt(template)

    async def test_evaluate_prompt_missing_fields(self):
        """测试评估提示词 - 响应缺少字段"""
        # Given
        service = PromptEvaluationService()
        template = await sync_to_async(PromptTemplateFactory)()

        mock_response = Mock()
        mock_response.success = True
        mock_response.data = {
            'score': 8.5,
            # 缺少其他字段
        }

        mock_client = AsyncMock()
        mock_client.generate_text.return_value = mock_response

        # When
        with patch.object(
            service,
            '_get_ai_client',
            return_value=mock_client
        ):
            result = await service.evaluate_prompt(template)

        # Then - 应该提供默认值
        assert result['score'] == 8.5
        assert result['clarity'] == 0.0
        assert result['specificity'] == 0.0
        assert result['creativity'] == 0.0
        assert result['strengths'] == []
        assert result['weaknesses'] == []
        assert result['suggestions'] == []

    async def test_compare_prompts(self):
        """测试对比两个提示词"""
        # Given
        service = PromptEvaluationService()
        template1 = await sync_to_async(PromptTemplateFactory)(
            template_content="提示词1: {{topic}}"
        )
        template2 = await sync_to_async(PromptTemplateFactory)(
            template_content="提示词2: {{topic}} {{style}}"
        )

        # Mock AI评估结果
        mock_response1 = Mock()
        mock_response1.success = True
        mock_response1.data = {
            'score': 7.0, 'clarity': 7.0, 'specificity': 7.0, 'creativity': 7.0,
            'strengths': [], 'weaknesses': [], 'suggestions': []
        }

        mock_response2 = Mock()
        mock_response2.success = True
        mock_response2.data = {
            'score': 8.5, 'clarity': 9.0, 'specificity': 8.0, 'creativity': 8.5,
            'strengths': [], 'weaknesses': [], 'suggestions': []
        }

        mock_client = AsyncMock()
        mock_client.generate_text.side_effect = [mock_response1, mock_response2]

        # When
        with patch.object(
            service,
            '_get_ai_client',
            return_value=mock_client
        ):
            result = await service.compare_prompts(template1, template2)

        # Then
        assert result['prompt1_score'] == 7.0
        assert result['prompt2_score'] == 8.5
        assert result['score_difference'] == 1.5
        assert result['better_prompt'] == 'prompt2'
        assert result['prompt1_evaluation'] == mock_response1.data
        assert result['prompt2_evaluation'] == mock_response2.data
        assert len(result['recommendations']) > 0

    async def test_compare_promps_equal_scores(self):
        """测试对比两个提示词 - 分数相同"""
        # Given
        service = PromptEvaluationService()
        template1 = await sync_to_async(PromptTemplateFactory)()
        template2 = await sync_to_async(PromptTemplateFactory)()

        mock_response = Mock()
        mock_response.success = True
        mock_response.data = {
            'score': 8.0,
            'clarity': 8.0,
            'specificity': 8.0,
            'creativity': 8.0
        }

        mock_client = AsyncMock()
        mock_client.generate_text.return_value = mock_response

        # When
        with patch.object(
            service,
            '_get_ai_client',
            return_value=mock_client
        ):
            result = await service.compare_prompts(template1, template2)

        # Then
        assert result['prompt1_score'] == 8.0
        assert result['prompt2_score'] == 8.0
        assert result['score_difference'] == 0.0
        assert result['better_prompt'] == 'prompt1'  # 相等时返回第一个

    async def test_suggest_improvements(self):
        """测试生成改进建议"""
        # Given
        service = PromptEvaluationService()
        template = await sync_to_async(PromptTemplateFactory)(
            template_content="简单提示词"
        )

        mock_response = Mock()
        mock_response.success = True
        mock_response.data = {
            'suggestions': [
                {
                    'title': '添加更多细节',
                    'description': '提供具体的指导',
                    'example': '改进后的提示词'
                }
            ],
            'improved_template': '改进后的完整提示词'
        }

        mock_client = AsyncMock()
        mock_client.generate_text.return_value = mock_response

        # When
        with patch.object(
            service,
            '_get_ai_client',
            return_value=mock_client
        ):
            result = await service.suggest_improvements(template)

        # Then
        assert 'suggestions' in result
        assert len(result['suggestions']) == 1
        assert result['suggestions'][0]['title'] == '添加更多细节'
        assert result['improved_template'] == '改进后的完整提示词'

    async def test_suggest_improvements_ai_failure(self):
        """测试生成改进建议 - AI调用失败"""
        # Given
        service = PromptEvaluationService()
        template = await sync_to_async(PromptTemplateFactory)()

        mock_response = Mock()
        mock_response.success = False
        mock_response.error = "网络错误"

        mock_client = AsyncMock()
        mock_client.generate_text.return_value = mock_response

        # When & Then
        with patch.object(
            service,
            '_get_ai_client',
            return_value=mock_client
        ), pytest.raises(Exception, match="生成改进建议失败"):
            await service.suggest_improvements(template)

    async def test_get_ai_client_caching(self):
        """测试AI客户端缓存机制"""
        # Given
        service = PromptEvaluationService()

        # Mock AI客户端
        mock_client = AsyncMock()

        # When
        with patch.object(service, '_get_ai_client', AsyncMock(return_value=mock_client)):
            # 第一次调用
            client1 = await service._get_ai_client()
            # 第二次调用
            client2 = await service._get_ai_client()

        # Then - 应该返回同一个实例(缓存)
            assert client1 is client2

    async def test_evaluate_prompt_with_variables(self):
        """测试评估带变量的提示词"""
        # Given
        service = PromptEvaluationService()
        template = await sync_to_async(PromptTemplateFactory)(
            template_content="主题: {{topic}}, 风格: {{style}}",
            variables={
                'topic': 'string',
                'style': 'string'
            }
        )

        mock_response = Mock()
        mock_response.success = True
        mock_response.data = {
            'score': 9.0,
            'clarity': 9.0,
            'specificity': 9.0,
            'creativity': 9.0,
            'strengths': ['变量定义清晰'],
            'weaknesses': [],
            'suggestions': []
        }

        mock_client = AsyncMock()
        mock_client.generate_text.return_value = mock_response

        # When
        with patch.object(
            service,
            '_get_ai_client',
            return_value=mock_client
        ):
            result = await service.evaluate_prompt(template)

        # Then
        assert result['score'] == 9.0
        # 验证variables被包含在评估提示词中
        call_args = mock_client.generate_text.call_args
        assert 'variables' in str(call_args) or '变量' in str(call_args)

    async def test_evaluate_prompt_no_provider(self):
        """测试评估提示词 - 无可用的模型提供商"""
        # Given
        service = PromptEvaluationService()
        template = await sync_to_async(PromptTemplateFactory)()

        # When - Mock ModelProvider.objects.filter().afirst()返回None
        with patch('apps.prompts.services.ModelProvider.objects') as mock_objects:
            # 创建mock queryset
            mock_qs = Mock()
            mock_qs.afirst = AsyncMock(return_value=None)  # 返回None表示没有找到
            mock_objects.filter.return_value = mock_qs

            # Then
            with pytest.raises(ValueError, match="未找到可用的LLM模型提供商"):
                await service.evaluate_prompt(template)

    async def test_compare_promps_all_dimensions(self):
        """测试对比提示词 - 所有维度对比"""
        # Given
        service = PromptEvaluationService()

        await sync_to_async(PromptTemplateFactory)()
        await sync_to_async(PromptTemplateFactory)()

        eval1 = {
            'score': 7.0,
            'clarity': 6.0,
            'specificity': 8.0,
            'creativity': 7.0
        }

        eval2 = {
            'score': 8.0,
            'clarity': 9.0,
            'specificity': 7.0,
            'creativity': 8.0
        }

        # When
        result = service._generate_comparison_recommendations(eval1, eval2)

        # Then
        assert len(result) == 3  # 每个维度一个建议
        assert any('清晰度' in r for r in result)
        assert any('具体性' in r for r in result)
        assert any('创造性' in r for r in result)

    def test_evaluation_prompt_constant(self):
        """测试评估提示词模板常量"""
        # Given & When & Then
        assert hasattr(PromptEvaluationService, 'EVALUATION_PROMPT')
        assert '{stage_type}' in PromptEvaluationService.EVALUATION_PROMPT
        assert '{template_content}' in PromptEvaluationService.EVALUATION_PROMPT
        assert '{variables}' in PromptEvaluationService.EVALUATION_PROMPT

    async def test_evaluate_prompt_temperature_setting(self):
        """测试评估提示词 - 温度参数设置"""
        # Given
        service = PromptEvaluationService()
        template = await sync_to_async(PromptTemplateFactory)()

        mock_response = Mock()
        mock_response.success = True
        mock_response.data = {
            'score': 8.0,
            'clarity': 8.0,
            'specificity': 8.0,
            'creativity': 8.0,
            'strengths': [],
            'weaknesses': [],
            'suggestions': []
        }

        mock_client = AsyncMock()
        mock_client.generate_text.return_value = mock_response

        # When
        with patch.object(
            service,
            '_get_ai_client',
            return_value=mock_client
        ):
            await service.evaluate_prompt(template)

        # Then - 验证使用了正确的温度参数
        mock_client.generate_text.assert_called_once()
        call_kwargs = mock_client.generate_text.call_args[1]
        assert call_kwargs['temperature'] == 0.3

    async def test_evaluate_prompt_response_format(self):
        """测试评估提示词 - 响应格式设置"""
        # Given
        service = PromptEvaluationService()
        template = await sync_to_async(PromptTemplateFactory)()

        mock_response = Mock()
        mock_response.success = True
        mock_response.data = {}

        mock_client = AsyncMock()
        mock_client.generate_text.return_value = mock_response

        # When
        with patch.object(
            service,
            '_get_ai_client',
            return_value=mock_client
        ):
            await service.evaluate_prompt(template)

        # Then - 验证请求JSON格式响应
        mock_client.generate_text.assert_called_once()
        call_kwargs = mock_client.generate_text.call_args[1]
        assert call_kwargs['response_format'] == 'json'
