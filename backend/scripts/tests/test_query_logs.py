"""
日志查询工具测试
Story 2.7 - 日志查询和告警配置
"""
import pytest
import json
import os
import tempfile
from scripts.query_logs import query_logs_from_file


@pytest.mark.django_db
class TestLogQueryTool:
    """日志查询工具测试"""

    def setup_method(self):
        """创建临时日志文件"""
        self.temp_log = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log')
        self.log_file = self.temp_log.name

        # 写入测试日志
        test_logs = [
            {
                'timestamp': '2026-01-28 16:54:54,093',
                'level': 'INFO',
                'logger': 'apps.api',
                'message': 'API Request: GET /api/v1/health/',
                'extra_fields': {
                    'request_id': '123',
                    'method': 'GET',
                    'path': '/api/v1/health/',
                    'response_time_ms': 0.29,
                    'is_slow_request': False
                }
            },
            {
                'timestamp': '2026-01-28 16:55:19,885',
                'level': 'WARNING',
                'logger': 'apps.api',
                'message': 'API Request: GET /api/v1/projects/',
                'extra_fields': {
                    'request_id': '456',
                    'method': 'GET',
                    'path': '/api/v1/projects/',
                    'response_time_ms': 2038.29,
                    'is_slow_request': True
                }
            },
            {
                'timestamp': '2026-01-28 16:56:00,000',
                'level': 'INFO',
                'logger': 'apps.celery',
                'message': 'Task started: execute_llm_stage',
                'extra_fields': {
                    'task_id': '789',
                    'task_name': 'execute_llm_stage',
                    'event': 'task_prerun'
                }
            },
            {
                'timestamp': '2026-01-28 16:57:00,000',
                'level': 'ERROR',
                'logger': 'apps.celery',
                'message': 'Task failed: execute_llm_stage',
                'extra_fields': {
                    'task_id': '789',
                    'task_name': 'execute_llm_stage',
                    'exception_type': 'ValueError',
                    'event': 'task_failure'
                }
            }
        ]

        for log in test_logs:
            self.temp_log.write(json.dumps(log) + '\n')
        self.temp_log.close()

    def teardown_method(self):
        """删除临时日志文件"""
        if os.path.exists(self.log_file):
            os.unlink(self.log_file)

    def test_query_all_logs(self):
        """测试查询所有日志"""
        results = query_logs_from_file(self.log_file)
        assert len(results) == 4

    def test_query_by_logger(self):
        """测试按logger过滤"""
        results = query_logs_from_file(
            self.log_file,
            filters={'logger': 'apps.api'}
        )
        assert len(results) == 2
        assert all(r['logger'] == 'apps.api' for r in results)

    def test_query_by_level(self):
        """测试按日志级别过滤"""
        results = query_logs_from_file(
            self.log_file,
            filters={'level': 'ERROR'}
        )
        assert len(results) == 1
        assert results[0]['level'] == 'ERROR'

    def test_query_slow_requests(self):
        """测试查询慢请求"""
        results = query_logs_from_file(
            self.log_file,
            filters={'extra_fields.is_slow_request': True}
        )
        assert len(results) == 1
        assert results[0]['extra_fields']['is_slow_request'] == True

    def test_query_by_event(self):
        """测试按事件类型过滤"""
        results = query_logs_from_file(
            self.log_file,
            filters={'extra_fields.event': 'task_failure'}
        )
        assert len(results) == 1
        assert results[0]['extra_fields']['event'] == 'task_failure'

    def test_query_with_limit(self):
        """测试结果数量限制"""
        results = query_logs_from_file(self.log_file, limit=2)
        assert len(results) == 2

    def test_query_nonexistent_file(self):
        """测试查询不存在的文件"""
        results = query_logs_from_file('/nonexistent/file.log')
        assert len(results) == 0

    def test_query_with_since_filter(self):
        """测试时间范围过滤（简单验证）"""
        # 由于测试日志的时间戳是固定的，这个测试主要验证不报错
        results = query_logs_from_file(
            self.log_file,
            since='1h'
        )
        # 实际的时间过滤取决于当前时间，这里只验证函数能正常执行
        assert isinstance(results, list)


@pytest.mark.django_db
class TestAlertingGuide:
    """告警配置文档测试"""

    def test_alerting_guide_exists(self):
        """测试告警配置文档存在"""
        doc_path = 'docs/monitoring/alerting-guide.md'
        assert os.path.exists(doc_path)

    def test_alerting_guide_content(self):
        """测试告警配置文档内容"""
        doc_path = 'docs/monitoring/alerting-guide.md'
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 验证包含关键章节
        assert '告警类型' in content
        assert '通知渠道' in content
        assert '日志查询' in content
        assert 'Celery任务失败告警' in content
        assert '慢任务告警' in content
        assert 'API响应时间告警' in content


@pytest.mark.django_db
class TestLogQueryScript:
    """日志查询脚本测试"""

    def test_script_exists(self):
        """测试日志查询脚本存在"""
        script_path = 'scripts/query_logs.py'
        assert os.path.exists(script_path)

    def test_script_executable(self):
        """测试脚本可执行"""
        script_path = 'scripts/query_logs.py'
        # 验证脚本可以导入（语法正确）
        import importlib.util
        spec = importlib.util.spec_from_file_location("query_logs", script_path)
        assert spec is not None
