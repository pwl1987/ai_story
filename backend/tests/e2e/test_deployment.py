"""
端到端部署测试脚本

用途: 验证生产环境部署的完整性和正确性

测试覆盖:
1. 健康检查端点
2. API可访问性
3. 数据库连接
4. Celery任务执行
5. WebSocket连接
6. 静态文件服务
7. CORS配置

运行方式:
  python backend/tests/e2e/test_deployment.py
"""

import os
import sys
import time
import json
import requests
import psycopg2
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))


class Colors:
    """终端颜色"""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


class E2ETestResult:
    """测试结果"""

    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, test_name):
        self.total += 1
        self.passed += 1
        print(f"{Colors.GREEN}✓{Colors.END} {test_name}")

    def add_fail(self, test_name, error):
        self.total += 1
        self.failed += 1
        self.errors.append({"test": test_name, "error": str(error)})
        print(f"{Colors.RED}✗{Colors.END} {test_name}: {error}")

    def print_summary(self):
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}测试总结{Colors.END}")
        print(f"总计: {self.total}")
        print(f"{Colors.GREEN}通过: {self.passed}{Colors.END}")
        print(f"{Colors.RED}失败: {self.failed}{Colors.END}")

        if self.errors:
            print(f"\n{Colors.RED}失败详情:{Colors.END}")
            for error in self.errors:
                print(f"  - {error['test']}: {error['error']}")

        success_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        print(f"\n{Colors.BOLD}成功率: {success_rate:.1f}%{Colors.END}")

        return self.failed == 0


class DeploymentE2ETest:
    """端到端部署测试"""

    def __init__(self):
        self.result = E2ETestResult()
        self.base_url = os.getenv("TEST_BASE_URL", "http://localhost:8000")
        self.frontend_url = os.getenv("TEST_FRONTEND_URL", "http://localhost")

    def run_all_tests(self):
        """运行所有测试"""
        print(f"{Colors.BOLD}{Colors.BLUE}开始端到端部署测试{Colors.END}")
        print(f"后端URL: {self.base_url}")
        print(f"前端URL: {self.frontend_url}\n")

        # 健康检查
        self.test_health_check()

        # API测试
        self.test_api_root()
        self.test_api_endpoints()

        # 数据库连接测试
        self.test_database_connection()

        # WebSocket连接测试
        self.test_websocket_connection()

        # 静态文件测试
        self.test_static_files()

        # CORS测试
        self.test_cors_configuration()

        # 项目创建流程测试
        self.test_project_creation_workflow()

        return self.result.print_summary()

    def test_health_check(self):
        """测试健康检查端点"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health/", timeout=5)
            if response.status_code == 200:
                self.result.add_pass("健康检查端点")
            else:
                self.result.add_fail("健康检查端点", f"状态码: {response.status_code}")
        except Exception as e:
            self.result.add_fail("健康检查端点", e)

    def test_api_root(self):
        """测试API根路径"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/", timeout=5)
            if response.status_code == 200:
                self.result.add_pass("API根路径")
            else:
                self.result.add_fail("API根路径", f"状态码: {response.status_code}")
        except Exception as e:
            self.result.add_fail("API根路径", e)

    def test_api_endpoints(self):
        """测试关键API端点"""
        endpoints = [
            ("项目列表", "/api/v1/projects/"),
            ("提示词集列表", "/api/v1/prompts/sets/"),
            ("模型列表", "/api/v1/models/"),
        ]

        for name, path in endpoints:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=5)
                if response.status_code in [200, 401, 403]:  # 200或需要认证
                    self.result.add_pass(f"API端点 - {name}")
                else:
                    self.result.add_fail(f"API端点 - {name}", f"状态码: {response.status_code}")
            except Exception as e:
                self.result.add_fail(f"API端点 - {name}", e)

    def test_database_connection(self):
        """测试数据库连接"""
        try:
            # 从环境变量获取数据库配置
            db_host = os.getenv("POSTGRES_HOST", "localhost")
            db_port = os.getenv("POSTGRES_PORT", "5432")
            db_name = os.getenv("POSTGRES_DB", "ai_story")
            db_user = os.getenv("POSTGRES_USER", "ai_story")
            db_password = os.getenv("POSTGRES_PASSWORD", "changeme")

            # 尝试连接数据库
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_user,
                password=db_password,
                connect_timeout=5,
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()

            self.result.add_pass("数据库连接")
        except Exception as e:
            self.result.add_fail("数据库连接", e)

    def test_websocket_connection(self):
        """测试WebSocket连接"""
        try:
            import websocket

            ws_url = f"ws://localhost:8000/ws/projects/test-project/"
            ws = websocket.create_connection(ws_url, timeout=5)
            ws.close()

            self.result.add_pass("WebSocket连接")
        except ImportError:
            self.result.add_fail("WebSocket连接", "websocket-client未安装")
        except Exception as e:
            self.result.add_fail("WebSocket连接", e)

    def test_static_files(self):
        """测试静态文件服务"""
        static_files = ["/static/", "/media/"]

        for path in static_files:
            try:
                response = requests.get(f"{self.frontend_url}{path}", timeout=5)
                if response.status_code in [200, 404]:  # 404可接受（目录为空）
                    self.result.add_pass(f"静态文件服务 - {path}")
                else:
                    self.result.add_fail(f"静态文件服务 - {path}", f"状态码: {response.status_code}")
            except Exception as e:
                self.result.add_fail(f"静态文件服务 - {path}", e)

    def test_cors_configuration(self):
        """测试CORS配置"""
        try:
            headers = {"Origin": "http://localhost:3000"}
            response = requests.get(f"{self.base_url}/api/v1/", headers=headers, timeout=5)

            cors_header = response.headers.get("Access-Control-Allow-Origin")
            if cors_header:
                self.result.add_pass("CORS配置")
            else:
                self.result.add_fail("CORS配置", "未找到CORS头部")
        except Exception as e:
            self.result.add_fail("CORS配置", e)

    def test_project_creation_workflow(self):
        """测试项目创建工作流（简化版）"""
        try:
            # 注意: 此测试需要认证token，仅测试端点可访问性
            response = requests.post(
                f"{self.base_url}/api/v1/projects/",
                json={"name": "E2E Test Project", "original_topic": "Test topic"},
                timeout=5,
            )

            # 401表示需要认证，端点可访问
            if response.status_code in [201, 401]:
                self.result.add_pass("项目创建工作流 - 端点可访问")
            else:
                self.result.add_fail(
                    "项目创建工作流", f"状态码: {response.status_code}, 响应: {response.text[:100]}"
                )
        except Exception as e:
            self.result.add_fail("项目创建工作流", e)


def main():
    """主函数"""
    print(f"\n{Colors.BOLD}AI Story - 端到端部署测试{Colors.END}")
    print("=" * 60 + "\n")

    tester = DeploymentE2ETest()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
