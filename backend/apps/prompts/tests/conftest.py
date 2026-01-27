"""
pytest配置文件 - prompts模块
处理async测试中的Django ORM调用
"""

import pytest
from asgiref.sync import sync_to_async


@pytest.fixture
def async_prompt_template_factory():
    """异步工厂函数 - 用于创建PromptTemplate"""
    async def _factory(**kwargs):
        from apps.prompts.tests.factories import PromptTemplateFactory
        return await sync_to_async(PromptTemplateFactory)(**kwargs)
    return _factory


@pytest.fixture
def async_prompt_template_set_factory():
    """异步工厂函数 - 用于创建PromptTemplateSet"""
    async def _factory(**kwargs):
        from apps.prompts.tests.factories import PromptTemplateSetFactory
        return await sync_to_async(PromptTemplateSetFactory)(**kwargs)
    return _factory


@pytest.fixture
def async_global_variable_factory():
    """异步工厂函数 - 用于创建GlobalVariable"""
    async def _factory(**kwargs):
        from apps.prompts.tests.factories import GlobalVariableFactory
        return await sync_to_async(GlobalVariableFactory)(**kwargs)
    return _factory
