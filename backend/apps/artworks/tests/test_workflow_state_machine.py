"""
工作流状态机单元测试 (Story 12-1.2)

测试范围：
- WorkflowState 枚举
- WorkflowStateMachine 状态转换
- 状态验证方法
- 转换历史记录
- 边界条件处理
"""

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.artworks.services.workflow_state_machine import (
    WorkflowState,
    WorkflowStateMachine,
)


class WorkflowStateTest(TestCase):
    """WorkflowState 枚举测试"""

    def test_state_enum_values(self):
        """测试状态枚举值"""
        self.assertEqual(WorkflowState.PENDING, "pending")
        self.assertEqual(WorkflowState.RUNNING, "running")
        self.assertEqual(WorkflowState.PAUSED, "paused")
        self.assertEqual(WorkflowState.COMPLETED, "completed")
        self.assertEqual(WorkflowState.FAILED, "failed")

    def test_state_enum_is_string(self):
        """测试状态枚举继承自 str"""
        # 确保状态可以与字符串比较
        state = WorkflowState.PENDING
        self.assertEqual(state, "pending")
        self.assertIn(state, ["pending", "running", "paused"])


class WorkflowStateMachineInitializationTest(TestCase):
    """WorkflowStateMachine 初始化测试"""

    def test_default_initial_state(self):
        """测试默认初始状态为 PENDING"""
        sm = WorkflowStateMachine()
        self.assertEqual(sm.current_state, WorkflowState.PENDING)
        self.assertEqual(len(sm.transition_history), 0)

    def test_custom_initial_state(self):
        """测试自定义初始状态"""
        sm = WorkflowStateMachine(WorkflowState.RUNNING)
        self.assertEqual(sm.current_state, WorkflowState.RUNNING)

    def test_repr(self):
        """测试字符串表示"""
        sm = WorkflowStateMachine()
        repr_str = repr(sm)
        self.assertIn("WorkflowStateMachine", repr_str)
        self.assertIn("current_state", repr_str)
        self.assertIn("transitions=0", repr_str)


class WorkflowStateTransitionTest(TestCase):
    """状态转换测试"""

    def test_pending_to_running(self):
        """测试 pending → running 转换"""
        sm = WorkflowStateMachine(WorkflowState.PENDING)

        result = sm.transition_to(WorkflowState.RUNNING)

        self.assertTrue(result)
        self.assertEqual(sm.current_state, WorkflowState.RUNNING)
        self.assertEqual(len(sm.transition_history), 1)

    def test_running_to_paused(self):
        """测试 running → paused 转换"""
        sm = WorkflowStateMachine(WorkflowState.RUNNING)

        result = sm.transition_to(WorkflowState.PAUSED)

        self.assertTrue(result)
        self.assertEqual(sm.current_state, WorkflowState.PAUSED)

    def test_running_to_completed(self):
        """测试 running → completed 转换"""
        sm = WorkflowStateMachine(WorkflowState.RUNNING)

        result = sm.transition_to(WorkflowState.COMPLETED)

        self.assertTrue(result)
        self.assertEqual(sm.current_state, WorkflowState.COMPLETED)

    def test_running_to_failed(self):
        """测试 running → failed 转换"""
        sm = WorkflowStateMachine(WorkflowState.RUNNING)

        result = sm.transition_to(WorkflowState.FAILED)

        self.assertTrue(result)
        self.assertEqual(sm.current_state, WorkflowState.FAILED)

    def test_paused_to_running(self):
        """测试 paused → running 转换（恢复）"""
        sm = WorkflowStateMachine(WorkflowState.PAUSED)

        result = sm.transition_to(WorkflowState.RUNNING)

        self.assertTrue(result)
        self.assertEqual(sm.current_state, WorkflowState.RUNNING)

    def test_failed_to_pending(self):
        """测试 failed → pending 转换（重试）"""
        sm = WorkflowStateMachine(WorkflowState.FAILED)

        result = sm.transition_to(WorkflowState.PENDING)

        self.assertTrue(result)
        self.assertEqual(sm.current_state, WorkflowState.PENDING)


class NoneValueTest(TestCase):
    """None 值验证测试 (DEV-003 修复验证)"""

    def test_can_transition_to_none_returns_false(self):
        """测试 can_transition_to 对 None 返回 False"""
        sm = WorkflowStateMachine(WorkflowState.PENDING)
        self.assertFalse(sm.can_transition_to(None))

    def test_transition_to_none_raises_error(self):
        """测试 transition_to 对 None 抛出 ValidationError"""
        sm = WorkflowStateMachine(WorkflowState.PENDING)

        with self.assertRaises(ValidationError) as cm:
            sm.transition_to(None)

        self.assertIn("不能为 None", str(cm.exception))


class InvalidTransitionTest(TestCase):
    """无效状态转换测试"""

    def test_pending_to_completed_invalid(self):
        """测试 pending → completed 无效转换"""
        sm = WorkflowStateMachine(WorkflowState.PENDING)

        with self.assertRaises(ValidationError) as cm:
            sm.transition_to(WorkflowState.COMPLETED)

        self.assertIn("Invalid transition", str(cm.exception))

    def test_completed_to_any_invalid(self):
        """测试 completed 是终态，不能转换到其他状态"""
        sm = WorkflowStateMachine(WorkflowState.COMPLETED)

        # 尝试转换到任何状态都应该失败
        with self.assertRaises(ValidationError):
            sm.transition_to(WorkflowState.RUNNING)

        with self.assertRaises(ValidationError):
            sm.transition_to(WorkflowState.PAUSED)

        with self.assertRaises(ValidationError):
            sm.transition_to(WorkflowState.PENDING)

    def test_running_to_pending_invalid(self):
        """测试 running → pending 无效转换"""
        sm = WorkflowStateMachine(WorkflowState.RUNNING)

        with self.assertRaises(ValidationError):
            sm.transition_to(WorkflowState.PENDING)

    def test_paused_to_completed_invalid(self):
        """测试 paused → completed 无效转换"""
        sm = WorkflowStateMachine(WorkflowState.PAUSED)

        with self.assertRaises(ValidationError):
            sm.transition_to(WorkflowState.COMPLETED)


class CanTransitionToTest(TestCase):
    """状态转换验证测试"""

    def test_can_transition_from_pending(self):
        """测试从 pending 可以转换到的状态"""
        sm = WorkflowStateMachine(WorkflowState.PENDING)

        self.assertTrue(sm.can_transition_to(WorkflowState.RUNNING))
        self.assertFalse(sm.can_transition_to(WorkflowState.PAUSED))
        self.assertFalse(sm.can_transition_to(WorkflowState.COMPLETED))
        self.assertFalse(sm.can_transition_to(WorkflowState.FAILED))

    def test_can_transition_from_running(self):
        """测试从 running 可以转换到的状态"""
        sm = WorkflowStateMachine(WorkflowState.RUNNING)

        self.assertTrue(sm.can_transition_to(WorkflowState.PAUSED))
        self.assertTrue(sm.can_transition_to(WorkflowState.COMPLETED))
        self.assertTrue(sm.can_transition_to(WorkflowState.FAILED))
        self.assertFalse(sm.can_transition_to(WorkflowState.PENDING))

    def test_can_transition_from_paused(self):
        """测试从 paused 可以转换到的状态"""
        sm = WorkflowStateMachine(WorkflowState.PAUSED)

        self.assertTrue(sm.can_transition_to(WorkflowState.RUNNING))
        self.assertFalse(sm.can_transition_to(WorkflowState.PENDING))
        self.assertFalse(sm.can_transition_to(WorkflowState.COMPLETED))

    def test_can_transition_from_completed(self):
        """测试从 completed 无法转换到任何状态"""
        sm = WorkflowStateMachine(WorkflowState.COMPLETED)

        self.assertFalse(sm.can_transition_to(WorkflowState.RUNNING))
        self.assertFalse(sm.can_transition_to(WorkflowState.PAUSED))
        self.assertFalse(sm.can_transition_to(WorkflowState.PENDING))

    def test_can_transition_from_failed(self):
        """测试从 failed 可以转换到的状态"""
        sm = WorkflowStateMachine(WorkflowState.FAILED)

        self.assertTrue(sm.can_transition_to(WorkflowState.PENDING))
        self.assertFalse(sm.can_transition_to(WorkflowState.RUNNING))


class TransitionHistoryTest(TestCase):
    """转换历史记录测试"""

    def test_transition_records_history(self):
        """测试状态转换记录历史"""
        sm = WorkflowStateMachine(WorkflowState.PENDING)

        sm.transition_to(WorkflowState.RUNNING)
        sm.transition_to(WorkflowState.PAUSED)
        sm.transition_to(WorkflowState.RUNNING)

        self.assertEqual(len(sm.transition_history), 3)

        # 验证历史记录内容
        self.assertEqual(sm.transition_history[0]["from"], WorkflowState.PENDING)
        self.assertEqual(sm.transition_history[0]["to"], WorkflowState.RUNNING)
        self.assertIsNotNone(sm.transition_history[0]["timestamp"])

        self.assertEqual(sm.transition_history[1]["from"], WorkflowState.RUNNING)
        self.assertEqual(sm.transition_history[1]["to"], WorkflowState.PAUSED)

        self.assertEqual(sm.transition_history[2]["from"], WorkflowState.PAUSED)
        self.assertEqual(sm.transition_history[2]["to"], WorkflowState.RUNNING)

    def test_get_last_transition(self):
        """测试获取最后一次转换"""
        sm = WorkflowStateMachine(WorkflowState.PENDING)

        sm.transition_to(WorkflowState.RUNNING)
        sm.transition_to(WorkflowState.PAUSED)

        last = sm.get_last_transition()
        self.assertEqual(last["from"], WorkflowState.RUNNING)
        self.assertEqual(last["to"], WorkflowState.PAUSED)
        self.assertIsNotNone(last["timestamp"])

    def test_get_last_transition_empty(self):
        """测试无转换历史时返回 None"""
        sm = WorkflowStateMachine()
        self.assertIsNone(sm.get_last_transition())

    def test_get_transition_count(self):
        """测试获取转换次数"""
        sm = WorkflowStateMachine(WorkflowState.PENDING)

        self.assertEqual(sm.get_transition_count(), 0)

        sm.transition_to(WorkflowState.RUNNING)
        self.assertEqual(sm.get_transition_count(), 1)

        sm.transition_to(WorkflowState.PAUSED)
        self.assertEqual(sm.get_transition_count(), 2)


class StatePropertyTest(TestCase):
    """状态属性测试"""

    def test_is_terminal_completed(self):
        """测试 COMPLETED 是终态"""
        sm = WorkflowStateMachine(WorkflowState.COMPLETED)
        self.assertTrue(sm.is_terminal)

    def test_is_terminal_other_states(self):
        """测试其他状态不是终态"""
        for state in [
            WorkflowState.PENDING,
            WorkflowState.RUNNING,
            WorkflowState.PAUSED,
            WorkflowState.FAILED,
        ]:
            sm = WorkflowStateMachine(state)
            self.assertFalse(sm.is_terminal, f"{state} should not be terminal")

    def test_is_active_running(self):
        """测试 RUNNING 是活跃状态"""
        sm = WorkflowStateMachine(WorkflowState.RUNNING)
        self.assertTrue(sm.is_active)

    def test_is_active_paused(self):
        """测试 PAUSED 是活跃状态"""
        sm = WorkflowStateMachine(WorkflowState.PAUSED)
        self.assertTrue(sm.is_active)

    def test_is_active_non_active_states(self):
        """测试其他状态不是活跃状态"""
        for state in [WorkflowState.PENDING, WorkflowState.COMPLETED, WorkflowState.FAILED]:
            sm = WorkflowStateMachine(state)
            self.assertFalse(sm.is_active, f"{state} should not be active")

    def test_is_failed(self):
        """测试失败状态判断"""
        sm = WorkflowStateMachine(WorkflowState.FAILED)
        self.assertTrue(sm.is_failed)

        sm2 = WorkflowStateMachine(WorkflowState.RUNNING)
        self.assertFalse(sm2.is_failed)

    def test_can_start(self):
        """测试是否可以启动"""
        self.assertTrue(WorkflowStateMachine(WorkflowState.PENDING).can_start)
        self.assertFalse(WorkflowStateMachine(WorkflowState.RUNNING).can_start)

    def test_can_pause(self):
        """测试是否可以暂停"""
        self.assertTrue(WorkflowStateMachine(WorkflowState.RUNNING).can_pause)
        self.assertFalse(WorkflowStateMachine(WorkflowState.PENDING).can_pause)

    def test_can_resume(self):
        """测试是否可以恢复"""
        self.assertTrue(WorkflowStateMachine(WorkflowState.PAUSED).can_resume)
        self.assertFalse(WorkflowStateMachine(WorkflowState.RUNNING).can_resume)

    def test_can_complete(self):
        """测试是否可以完成"""
        self.assertTrue(WorkflowStateMachine(WorkflowState.RUNNING).can_complete)
        self.assertFalse(WorkflowStateMachine(WorkflowState.PENDING).can_complete)

    def test_can_fail(self):
        """测试是否可以失败"""
        self.assertTrue(WorkflowStateMachine(WorkflowState.RUNNING).can_fail)
        self.assertFalse(WorkflowStateMachine(WorkflowState.PAUSED).can_fail)

    def test_can_retry(self):
        """测试是否可以重试"""
        self.assertTrue(WorkflowStateMachine(WorkflowState.FAILED).can_retry)
        self.assertFalse(WorkflowStateMachine(WorkflowState.RUNNING).can_retry)


class GetAllowedTransitionsTest(TestCase):
    """获取允许转换列表测试"""

    def test_allowed_from_pending(self):
        """测试从 pending 允许的转换"""
        sm = WorkflowStateMachine(WorkflowState.PENDING)
        allowed = sm.get_allowed_transitions()
        self.assertEqual(allowed, [WorkflowState.RUNNING])

    def test_allowed_from_running(self):
        """测试从 running 允许的转换"""
        sm = WorkflowStateMachine(WorkflowState.RUNNING)
        allowed = sm.get_allowed_transitions()
        self.assertIn(WorkflowState.PAUSED, allowed)
        self.assertIn(WorkflowState.COMPLETED, allowed)
        self.assertIn(WorkflowState.FAILED, allowed)
        self.assertEqual(len(allowed), 3)

    def test_allowed_from_paused(self):
        """测试从 paused 允许的转换"""
        sm = WorkflowStateMachine(WorkflowState.PAUSED)
        allowed = sm.get_allowed_transitions()
        self.assertEqual(allowed, [WorkflowState.RUNNING])

    def test_allowed_from_completed(self):
        """测试从 completed 允许的转换（终态）"""
        sm = WorkflowStateMachine(WorkflowState.COMPLETED)
        allowed = sm.get_allowed_transitions()
        self.assertEqual(allowed, [])

    def test_allowed_from_failed(self):
        """测试从 failed 允许的转换"""
        sm = WorkflowStateMachine(WorkflowState.FAILED)
        allowed = sm.get_allowed_transitions()
        self.assertEqual(allowed, [WorkflowState.PENDING])


class StateMachineResetTest(TestCase):
    """状态机重置测试"""

    def test_reset_clears_state(self):
        """测试重置清空状态"""
        sm = WorkflowStateMachine(WorkflowState.RUNNING)
        sm.transition_to(WorkflowState.PAUSED)
        sm.transition_to(WorkflowState.RUNNING)
        sm.transition_to(WorkflowState.COMPLETED)

        self.assertEqual(sm.get_transition_count(), 3)

        sm.reset()

        self.assertEqual(sm.current_state, WorkflowState.PENDING)
        self.assertEqual(sm.get_transition_count(), 0)

    def test_reset_allows_new_transitions(self):
        """测试重置后可以重新开始转换"""
        sm = WorkflowStateMachine(WorkflowState.COMPLETED)

        # 终态不能转换
        self.assertFalse(sm.can_transition_to(WorkflowState.RUNNING))

        sm.reset()

        # 重置后可以转换
        self.assertTrue(sm.can_transition_to(WorkflowState.RUNNING))
        sm.transition_to(WorkflowState.RUNNING)
        self.assertEqual(sm.current_state, WorkflowState.RUNNING)


class WorkflowLifecycleTest(TestCase):
    """工作流生命周期集成测试"""

    def test_full_workflow_lifecycle(self):
        """测试完整工作流生命周期"""
        sm = WorkflowStateMachine()

        # 开始
        sm.transition_to(WorkflowState.RUNNING)
        self.assertTrue(sm.is_active)
        self.assertFalse(sm.is_terminal)

        # 暂停
        sm.transition_to(WorkflowState.PAUSED)
        self.assertTrue(sm.is_active)

        # 恢复
        sm.transition_to(WorkflowState.RUNNING)
        self.assertTrue(sm.is_active)

        # 完成
        sm.transition_to(WorkflowState.COMPLETED)
        self.assertFalse(sm.is_active)
        self.assertTrue(sm.is_terminal)

        # 验证转换次数
        self.assertEqual(sm.get_transition_count(), 4)

    def test_workflow_with_failure(self):
        """测试包含失败的工作流"""
        sm = WorkflowStateMachine()

        # 开始
        sm.transition_to(WorkflowState.RUNNING)
        self.assertFalse(sm.is_failed)

        # 失败
        sm.transition_to(WorkflowState.FAILED)
        self.assertTrue(sm.is_failed)
        self.assertFalse(sm.is_active)

        # 重试
        sm.transition_to(WorkflowState.PENDING)
        self.assertFalse(sm.is_failed)

        # 重新开始
        sm.transition_to(WorkflowState.RUNNING)
        self.assertTrue(sm.is_active)

    def test_pause_resume_cycle(self):
        """测试多次暂停/恢复循环"""
        sm = WorkflowStateMachine(WorkflowState.RUNNING)

        # 第一次暂停/恢复 (2次转换)
        sm.transition_to(WorkflowState.PAUSED)
        sm.transition_to(WorkflowState.RUNNING)

        # 第二次暂停/恢复 (2次转换)
        sm.transition_to(WorkflowState.PAUSED)
        sm.transition_to(WorkflowState.RUNNING)

        # 第三次暂停/恢复 (2次转换)
        sm.transition_to(WorkflowState.PAUSED)
        sm.transition_to(WorkflowState.RUNNING)

        # 最终完成 (1次转换)
        sm.transition_to(WorkflowState.COMPLETED)

        # 验证转换次数: 2+2+2+1 = 7
        self.assertEqual(sm.get_transition_count(), 7)
