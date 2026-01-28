"""
提示词评估服务
职责: 使用AI分析提示词质量并提供优化建议
遵循单一职责原则(SRP): 专注于提示词评估
遵循依赖倒置原则(DIP): 依赖AI客户端抽象而非具体实现
"""

from typing import Any, Dict, List

from apps.models.models import ModelProvider

# 导入异步ORM包装函数
from apps.projects.pipeline_adapters import sync_to_async_wrapper
from core.ai_client.openai_client import OpenAIClient


class PromptEvaluationService:
    """
    提示词评估服务
    使用AI模型分析提示词质量
    """

    EVALUATION_PROMPT = """请评估以下提示词模板的质量,并给出详细分析:

提示词类型: {stage_type}
提示词内容:
{template_content}

变量定义:
{variables}

请从以下维度评分(0-10分):
1. 清晰度(Clarity): 指令是否清晰明确
2. 具体性(Specificity): 是否提供足够的细节
3. 创造性(Creativity): 是否能激发创造性输出

请以JSON格式返回评估结果:
{{
    "score": 总分(0-10),
    "clarity": 清晰度得分,
    "specificity": 具体性得分,
    "creativity": 创造性得分,
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["缺点1", "缺点2"],
    "suggestions": ["建议1", "建议2"]
}}
"""

    def __init__(self):
        """初始化评估服务"""
        self.ai_client = None

    async def _get_ai_client(self) -> OpenAIClient:
        """
        获取AI客户端
        优先使用配置的评估专用模型,否则使用默认LLM
        """
        if self.ai_client:
            return self.ai_client

        # 查找评估专用的模型提供商
        # 使用sync_to_async_wrapper包装ORM调用（Django 3.2不支持原生异步ORM）
        provider = await sync_to_async_wrapper(
            ModelProvider.objects.filter(
                provider_type='llm',
                is_active=True
            ).first
        )()

        if not provider:
            raise ValueError('未找到可用的LLM模型提供商')

        # 创建OpenAI客户端
        self.ai_client = OpenAIClient(
            api_key=provider.api_key,
            api_url=provider.api_url,
            model_name=provider.model_name,
            config=provider.config
        )

        return self.ai_client

    async def evaluate_prompt(self, prompt_template) -> Dict[str, Any]:
        """
        评估提示词模板

        Args:
            prompt_template: PromptTemplate实例

        Returns:
            评估结果字典
        """
        # 构建评估提示词
        evaluation_prompt = self.EVALUATION_PROMPT.format(
            stage_type=prompt_template.get_stage_type_display(),
            template_content=prompt_template.template_content,
            variables=prompt_template.variables
        )

        # 获取AI客户端
        client = await self._get_ai_client()

        # 调用AI进行评估
        response = await client.generate_text(
            prompt=evaluation_prompt,
            temperature=0.3,  # 降低温度以获得更一致的评估
            response_format='json'
        )

        if not response.success:
            raise Exception(f'AI评估失败: {response.error}')

        # 解析评估结果
        evaluation_data = response.data

        # 验证和补充数据
        return {
            'score': float(evaluation_data.get('score', 0)),
            'clarity': float(evaluation_data.get('clarity', 0)),
            'specificity': float(evaluation_data.get('specificity', 0)),
            'creativity': float(evaluation_data.get('creativity', 0)),
            'strengths': evaluation_data.get('strengths', []),
            'weaknesses': evaluation_data.get('weaknesses', []),
            'suggestions': evaluation_data.get('suggestions', [])
        }

    async def compare_prompts(
        self,
        prompt1,
        prompt2
    ) -> Dict[str, Any]:
        """
        对比两个提示词模板

        Args:
            prompt1: 第一个PromptTemplate实例
            prompt2: 第二个PromptTemplate实例

        Returns:
            对比结果
        """
        # 分别评估两个提示词
        eval1 = await self.evaluate_prompt(prompt1)
        eval2 = await self.evaluate_prompt(prompt2)

        # 计算差异
        return {
            'prompt1_score': eval1['score'],
            'prompt2_score': eval2['score'],
            'score_difference': eval2['score'] - eval1['score'],
            'better_prompt': 'prompt2' if eval2['score'] > eval1['score'] else 'prompt1',
            'prompt1_evaluation': eval1,
            'prompt2_evaluation': eval2,
            'recommendations': self._generate_comparison_recommendations(eval1, eval2)
        }

    def _generate_comparison_recommendations(
        self,
        eval1: Dict[str, Any],
        eval2: Dict[str, Any]
    ) -> List[str]:
        """
        生成对比建议
        """
        recommendations = []

        # 对比各维度
        if eval2['clarity'] > eval1['clarity']:
            recommendations.append('第二个提示词在清晰度方面更优')
        elif eval1['clarity'] > eval2['clarity']:
            recommendations.append('第一个提示词在清晰度方面更优')

        if eval2['specificity'] > eval1['specificity']:
            recommendations.append('第二个提示词在具体性方面更优')
        elif eval1['specificity'] > eval2['specificity']:
            recommendations.append('第一个提示词在具体性方面更优')

        if eval2['creativity'] > eval1['creativity']:
            recommendations.append('第二个提示词在创造性方面更优')
        elif eval1['creativity'] > eval2['creativity']:
            recommendations.append('第一个提示词在创造性方面更优')

        return recommendations

    async def suggest_improvements(
        self,
        prompt_template
    ) -> Dict[str, Any]:
        """
        AI生成改进建议

        Args:
            prompt_template: PromptTemplate实例

        Returns:
            改进建议
        """
        improvement_prompt = f"""请为以下提示词模板提供具体的改进建议:

提示词类型: {prompt_template.get_stage_type_display()}
当前内容:
{prompt_template.template_content}

请提供:
1. 3-5个具体的改进建议
2. 改进后的示例内容(保持原有变量)

返回JSON格式:
{{
    "suggestions": [
        {{
            "title": "建议标题",
            "description": "详细说明",
            "example": "改进示例"
        }}
    ],
    "improved_template": "完整的改进后模板"
}}
"""

        client = await self._get_ai_client()
        response = await client.generate_text(
            prompt=improvement_prompt,
            temperature=0.7,
            response_format='json'
        )

        if not response.success:
            raise Exception(f'生成改进建议失败: {response.error}')

        return response.data
