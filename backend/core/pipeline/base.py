"""
Pipeline工作流基础抽象
遵循责任链模式 + 策略模式
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class PipelineContext:
    """
    工作流上下文
    携带所有阶段的数据
    """

    project_id: str
    results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_result(self, stage: str, data: Any):
        """添加阶段结果"""
        self.results[stage] = data

    def get_result(self, stage: str) -> Optional[Any]:
        """获取阶段结果"""
        return self.results.get(stage)

    def add_metadata(self, key: str, value: Any):
        """添加元数据"""
        self.metadata[key] = value

    def get_metadata(self, key: str) -> Optional[Any]:
        """获取元数据"""
        return self.metadata.get(key)


@dataclass
class StageResult:
    """阶段执行结果"""

    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    can_retry: bool = True


class StageProcessor(ABC):
    """
    阶段处理器抽象基类
    遵循单一职责原则: 每个处理器只负责一个阶段
    """

    def __init__(self, stage_name: str):
        self.stage_name = stage_name

    @abstractmethod
    async def validate(self, context: PipelineContext) -> bool:
        """
        验证阶段是否可以执行

        Args:
            context: 工作流上下文

        Returns:
            bool: 是否可以执行
        """
        pass

    @abstractmethod
    async def on_failure(self, context: PipelineContext, error: Exception):
        """
        失败处理

        Args:
            context: 工作流上下文
            error: 异常信息
        """
        pass

    async def on_success(self, context: PipelineContext, result: StageResult):
        """
        成功处理(可选)

        Args:
            context: 工作流上下文
            result: 阶段结果
        """
        pass


class ValidationError(Exception):
    """验证错误"""

    pass


class ProcessingError(Exception):
    """处理错误"""

    pass
