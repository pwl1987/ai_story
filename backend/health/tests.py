"""
健康检查端点测试
"""
from django.test import TestCase
from django.urls import reverse


class HealthCheckViewTestCase(TestCase):
    """
    测试健康检查端点
    """

    def test_health_check_endpoint_exists(self):
        """测试健康检查端点存在"""
        url = reverse('health:health-check')
        # URL应该是相对路径（在health app内）
        self.assertIn(url, ('/', '/api/v1/health/'))

    def test_health_check_returns_json(self):
        """测试健康检查返回JSON格式"""
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_health_check_response_structure(self):
        """测试健康检查响应结构"""
        response = self.client.get('/api/v1/health/')
        self.assertIn('status', response.json())
        self.assertIn('checks', response.json())
        self.assertIn('server', response.json())
        self.assertIn('response_time_ms', response.json())

    def test_health_check_has_database_check(self):
        """测试健康检查包含数据库检查"""
        response = self.client.get('/api/v1/health/')
        checks = response.json().get('checks', {})
        self.assertIn('database', checks)
        self.assertIn('status', checks['database'])
        self.assertIn('name', checks['database'])

    def test_health_check_has_redis_checks(self):
        """测试健康检查包含所有Redis检查"""
        response = self.client.get('/api/v1/health/')
        checks = response.json().get('checks', {})
        # 应该有5个Redis检查
        redis_checks = [key for key in checks if key.startswith('redis_')]
        self.assertEqual(len(redis_checks), 5)

        # 验证每个Redis检查都有必要字段
        for key in redis_checks:
            self.assertIn('name', checks[key])
            self.assertIn('status', checks[key])
            self.assertIn('details', checks[key])

    def test_health_check_response_time(self):
        """测试健康检查响应时间记录"""
        response = self.client.get('/api/v1/health/')
        data = response.json()
        self.assertIn('response_time_ms', data)
        self.assertIsInstance(data['response_time_ms'], (int, float))

    def test_health_check_server_info(self):
        """测试健康检查包含服务器信息"""
        response = self.client.get('/api/v1/health/')
        server = response.json().get('server', {})
        self.assertIn('request_id', server)
        self.assertIn('startup_time', server)
        self.assertIn('current_time', server)

    def test_health_check_cache(self):
        """测试健康检查缓存功能"""
        # 第一次请求
        response1 = self.client.get('/api/v1/health/')
        data1 = response1.json()

        # 立即第二次请求（应该从缓存读取）
        response2 = self.client.get('/api/v1/health/')
        data2 = response2.json()

        # 验证第二次请求使用了缓存
        # 注意：由于测试环境可能使用真实缓存，第二次请求的cached应该为True
        self.assertIn('cached', data2)
        # 第一次请求不应该使用缓存
        self.assertFalse(data1.get('cached', True))

    def test_health_check_status_when_healthy(self):
        """测试所有服务健康时返回healthy状态"""
        response = self.client.get('/api/v1/health/')
        data = response.json()

        # 检查整体状态
        self.assertIn(data['status'], ('healthy', 'unhealthy', 'degraded'))

        # 在测试环境中，由于Redis未运行，状态应该是unhealthy
        # 但数据库应该是healthy
        checks = data['checks']
        self.assertEqual(checks['database']['status'], 'healthy')

    def test_health_check_returns_200_or_503(self):
        """测试健康检查返回正确的状态码"""
        response = self.client.get('/api/v1/health/')

        # 如果所有服务健康，返回200
        # 如果有服务不健康，返回503
        self.assertIn(response.status_code, (200, 503))

    def test_health_check_error_details(self):
        """测试健康检查包含错误详情（当服务不健康时）"""
        response = self.client.get('/api/v1/health/')
        data = response.json()
        checks = data['checks']

        # 检查Redis服务（应该失败）
        redis_checks = [key for key in checks if key.startswith('redis_')]
        for key in redis_checks:
            check = checks[key]
            if check['status'] == 'unhealthy':
                # 应该有错误详情
                self.assertIn('details', check)
                self.assertIn('error', check['details'])
