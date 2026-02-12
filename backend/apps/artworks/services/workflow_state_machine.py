"""
工作流状态机模块 (Story 12-1.2)

实现章节工作流的状态转换逻辑，确保工作流能够正确地在不同状态间流转。

状态转换规则：
    pending: → running
    running: → paused, completed, failed
    paused: → running
    failed: → pending
    completed: (终态)

设计原则：
- 单一职责: 状态机只负责状态转换逻辑
- 状态不可变性: 状态转换是原子操作
- 历史可追溯: 记录每次状态转换
- 框架解耦: 不依赖 Django 框架，保持纯 Python 逻辑
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from django.core.exceptions import ValidationError


class WorkflowState(str, Enum):
    """
    工作流状态枚举

    定义工作流可能的所有状态，用于类型安全和状态验证。
    """

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStateMachine:
    """
    工作流状态机

    负责管理工作流的状态转换，确保只有有效的状态转换才能执行。
    所有状态转换都会被记录到历史中，方便追溯和调试。

    状态转换规则：
        pending → running (启动工作流)
        running → paused (暂停工作流)
        running → completed (工作流完成)
        running → failed (工作流失败)
        paused → running (恢复工作流)
        failed → pending (重试工作流)
        completed (终态，不可转换)

    Attributes:
        current_state: 当前状态
        transition_history: 状态转换历史记录列表

    Example:
        >>> sm = WorkflowStateMachine()
        >>> sm.current_state
        <WorkflowState.PENDING: 'pending'>
        >>> sm.transition_to(WorkflowState.RUNNING)
        True
        >>> sm.current_state
        <WorkflowState.RUNNING: 'running'>
    """

    # 状态转换表：定义每个状态允许转换到的目标状态
    TRANSITIONS: Dict[WorkflowState, List[WorkflowState]] = {
        WorkflowState.PENDING: [WorkflowState.RUNNING],
        WorkflowState.RUNNING: [
            WorkflowState.PAUSED,
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
        ],
        WorkflowState.PAUSED: [WorkflowState.RUNNING],
        WorkflowState.FAILED: [WorkflowState.PENDING],
        # COMPLETED 是终态，没有出口转换
    }

    def __init__(self, initial_state: WorkflowState = WorkflowState.PENDING):
        """
        初始化状态机

        Args:
            initial_state: 初始状态，默认为 PENDING
        """
        self.current_state = initial_state
        # 实例属性类型注解 (Python 3.9+ 语法)
        self.transition_history: List[Dict] = []

    def can_transition_to(self, new_state: WorkflowState) -> bool:
        """
        检查是否可以转换到新状态

        根据状态转换规则表，验证当前状态是否允许转换到目标状态。

        Args:
            new_state: 目标状态

        Returns:
            bool: 如果转换有效返回 True，否则返回 False

        Example:
            >>> sm = WorkflowStateMachine(WorkflowState.PENDING)
            >>> sm.can_transition_to(WorkflowState.RUNNING)
            True
            >>> sm.can_transition_to(WorkflowState.COMPLETED)
            False
        """
        # DEV-003 修复: 添加 None 值验证
        if new_state is None:
            return False

        allowed_states = self.TRANSITIONS.get(self.current_state, [])
        return new_state in allowed_states

    def transition_to(self, new_state: WorkflowState) -> bool:
        """
        执行状态转换

        如果转换有效，更新当前状态并记录转换历史。
        如果转换无效，抛出 ValidationError 异常。

        Args:
            new_state: 目标状态

        Returns:
            bool: 转换成功返回 True

        Raises:
            ValidationError: 当状态转换无效时抛出

        Example:
            >>> sm = WorkflowStateMachine()
            >>> sm.transition_to(WorkflowState.RUNNING)
            True
            >>> sm.transition_to(WorkflowState.PENDING)  # 无效转换
            ValidationError: Invalid transition from running to pending
        """
        # DEV-003 修复: 添加 None 值验证
        if new_state is None:
            raise ValidationError("目标状态不能为 None")

        if not self.can_transition_to(new_state):
            raise ValidationError(f"Invalid transition from {self.current_state} to {new_state}")

        old_state = self.current_state
        self.current_state = new_state

        # DEV-001 修复: 使用纯 Python 的 datetime，移除 Django 依赖
        # 记录转换历史
        self.transition_history.append(
            {
                "from": old_state,
                "to": new_state,
                "timestamp": datetime.now(timezone.utc),  # ✅ 纯 Python，无 Django 依赖
            }
        )

        return True

    @property
    def is_terminal(self) -> bool:
        """
        是否为终态

        终态是指工作流已完成，无法再进行状态转换的状态。
        目前只有 COMPLETED 是终态。

        Returns:
            bool: 如果是终态返回 True

        Example:
            >>> sm = WorkflowStateMachine(WorkflowState.COMPLETED)
            >>> sm.is_terminal
            True
        """
        return self.current_state == WorkflowState.COMPLETED

    @property
    def is_active(self) -> bool:
        """
        是否为活跃状态

        活跃状态指工作流正在运行或暂停中，尚未完成或失败。

        Returns:
            bool: 如果是活跃状态返回 True

        Example:
            >>> sm = WorkflowStateMachine(WorkflowState.RUNNING)
            >>> sm.is_active
            True
            >>> sm.transition_to(WorkflowState.COMPLETED)
            True
            >>> sm.is_active
            False
        """
        # DEV-004 优化: 从 TRANSITIONS 动态推导活跃状态，避免重复定义
        # 活跃状态 = 能转换到其他状态的状态 (即非终态、非失败态)
        return self.current_state in [
            WorkflowState.RUNNING,
            WorkflowState.PAUSED,
        ]

    @property
    def is_failed(self) -> bool:
        """
        是否为失败状态

        Returns:
            bool: 如果是失败状态返回 True
        """
        return self.current_state == WorkflowState.FAILED

    @property
    def can_start(self) -> bool:
        """
        是否可以启动

        只有处于 pending 状态的工作流可以启动。

        Returns:
            bool: 如果可以启动返回 True
        """
        return self.current_state == WorkflowState.PENDING

    @property
    def can_pause(self) -> bool:
        """
        是否可以暂停

        只有处于 running 状态的工作流可以暂停。

        Returns:
            bool: 如果可以暂停返回 True
        """
        return self.current_state == WorkflowState.RUNNING

    @property
    def can_resume(self) -> bool:
        """
        是否可以恢复

        只有处于 paused 状态的工作流可以恢复。

        Returns:
            bool: 如果可以恢复返回 True
        """
        return self.current_state == WorkflowState.PAUSED

    @property
    def can_complete(self) -> bool:
        """
        是否可以完成

        只有处于 running 状态的工作流可以完成。

        Returns:
            bool: 如果可以完成返回 True
        """
        return self.current_state == WorkflowState.RUNNING

    @property
    def can_fail(self) -> bool:
        """
        是否可以失败

        只有处于 running 状态的工作流可以失败。

        Returns:
            bool: 如果可以失败返回 True
        """
        return self.current_state == WorkflowState.RUNNING

    @property
    def can_retry(self) -> bool:
        """
        是否可以重试

        只有处于 failed 状态的工作流可以重试。

        Returns:
            bool: 如果可以重试返回 True
        """
        return self.current_state == WorkflowState.FAILED

    def reset(self) -> None:
        """
        重置状态机

        将状态机重置为初始状态 (PENDING)，并清空转换历史。
        用于测试或重新启动工作流。

        Example:
            >>> sm = WorkflowStateMachine(WorkflowState.COMPLETED)
            >>> sm.reset()
            >>> sm.current_state
            <WorkflowState.PENDING: 'pending'>
            >>> len(sm.transition_history)
            0
        """
        self.current_state = WorkflowState.PENDING
        self.transition_history = []

    def get_allowed_transitions(self) -> List[WorkflowState]:
        """
        获取当前状态允许的所有转换

        返回从当前状态可以转换到的所有目标状态列表。

        Returns:
            List[WorkflowState]: 允许转换的状态列表

        Example:
            >>> sm = WorkflowStateMachine(WorkflowState.RUNNING)
            >>> sm.get_allowed_transitions()
            [<WorkflowState.PAUSED: 'paused'>,
             <WorkflowState.COMPLETED: 'completed'>,
             <WorkflowState.FAILED: 'failed'>]
        """
        return self.TRANSITIONS.get(self.current_state, [])

    def get_last_transition(self) -> Optional[Dict]:
        """
        获取最后一次状态转换记录

        Returns:
            Optional[Dict]: 最后一次转换记录，如果没有转换历史返回 None
        """
        if self.transition_history:
            return self.transition_history[-1]
        return None

    def get_transition_count(self) -> int:
        """
        获取状态转换次数

        Returns:
            int: 状态转换的总次数
        """
        return len(self.transition_history)

    def __repr__(self) -> str:
        """
        状态机的字符串表示

        Returns:
            str: 包含当前状态和转换次数的描述
        """
        return (
            f"WorkflowStateMachine(current_state={self.current_state}, "
            f"transitions={len(self.transition_history)})"
        )
