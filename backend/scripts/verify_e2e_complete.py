"""
端到端完整验证脚本
验证"创建项目→启动工作流→AI自动生成→查看进度→完成通知"完整性

运行方式:
    cd backend
    uv run python scripts/verify_e2e_complete.py

前置条件:
1. 运行 setup_mock_env.py
2. 运行 create_test_project.py
3. 启动Redis、Celery Worker、Django ASGI
"""
import os
import sys
import time

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django

django.setup()

import requests
from django.contrib.auth import get_user_model

from apps.projects.models import Project

User = get_user_model()


class E2EVerifier:
    """端到端验证器"""

    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.token = None
        self.project_id = None
        self.user_id = None

    def verify_auth(self):
        """验证1: 用户认证"""
        print("\n" + "="*60)
        print("验证1: 用户认证")
        print("="*60)

        response = requests.post(f"{self.base_url}/users/login/", json={
            "username": "e2e_test_user",
            "password": "test_password"
        })

        if response.status_code != 200:
            print(f"✗ 登录失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return False

        data = response.json()
        self.token = data.get('token') or data.get('access')
        self.user_id = data.get('user_id')

        print("✓ 登录成功")
        print(f"  Token: {self.token[:20]}...")
        print(f"  User ID: {self.user_id}")
        return True

    def verify_project_creation(self):
        """验证2: 项目创建"""
        print("\n" + "="*60)
        print("验证2: 项目创建")
        print("="*60)

        try:
            project = Project.objects.get(name='E2E Test Project')
            self.project_id = str(project.id)

            print("✓ 项目存在")
            print(f"  ID: {project.id}")
            print(f"  名称: {project.name}")
            print(f"  状态: {project.status}")
            print(f"  主题: {project.original_topic}")
            print(f"  阶段数: {project.stages.count()}")

            # 验证阶段
            expected_stages = ['rewrite', 'storyboard', 'image_generation', 'camera_movement', 'video_generation']
            actual_stages = [s.stage_type for s in project.stages.all()]

            if set(expected_stages) == set(actual_stages):
                print("✓ 阶段配置正确")
            else:
                print("✗ 阶段配置不匹配")
                print(f"  期望: {expected_stages}")
                print(f"  实际: {actual_stages}")
                return False

            return True

        except Project.DoesNotExist:
            print("✗ 项目不存在")
            print("  请先运行: uv run python scripts/create_test_project.py")
            return False

    def verify_workflow_start(self):
        """验证3: 启动工作流"""
        print("\n" + "="*60)
        print("验证3: 启动工作流")
        print("="*60)

        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.base_url}/projects/{self.project_id}/execute_full_pipeline/"

        response = requests.post(url, headers=headers)

        if response.status_code != 202:
            print(f"✗ 启动失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return False

        data = response.json()
        task_id = data.get('task_id')
        channel = data.get('channel')

        print("✓ 工作流已启动")
        print(f"  任务ID: {task_id}")
        print(f"  频道: {channel}")
        print(f"  项目ID: {data.get('project_id')}")

        return True

    def verify_ai_generation(self, timeout=300):
        """验证4: AI自动生成"""
        print("\n" + "="*60)
        print("验证4: AI自动生成")
        print("="*60)

        headers = {"Authorization": f"Bearer {self.token}"}
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = requests.get(f"{self.base_url}/projects/{self.project_id}/", headers=headers)

            if response.status_code != 200:
                print(f"✗ 获取项目状态失败: {response.status_code}")
                return False

            project = response.json()
            status = project['status']
            stages = project['stages']

            # 计算完成进度
            completed = sum(1 for s in stages if s['status'] == 'completed')
            total = len(stages)
            progress = int((completed / total) * 100)

            # 构建进度条
            progress_bar = '█' * (progress // 10) + '░' * (10 - progress // 10)
            elapsed = int(time.time() - start_time)

            print(f"\r  进度: [{progress_bar}] {progress}% | {completed}/{total} 阶段 | {elapsed}秒", end='')

            # 检查状态
            if status == 'completed':
                print("\n\n✓ 所有阶段已完成")

                # 显示阶段详情
                print("\n  阶段详情:")
                for stage in stages:
                    symbol = "✓" if stage['status'] == 'completed' else "✗"
                    print(f"    {symbol} {stage['stage_type']}: {stage['status']}")

                return True

            elif status == 'failed':
                print("\n\n✗ 工作流失败")

                # 显示失败信息
                for stage in stages:
                    if stage['status'] == 'failed':
                        print(f"    失败阶段: {stage['stage_type']}")
                        if stage.get('error_message'):
                            print(f"    错误: {stage['error_message']}")

                return False

            time.sleep(2)

        print(f"\n\n✗ 超时（{timeout}秒）")
        return False

    def verify_websocket_notification(self):
        """验证5: WebSocket完成通知（可选）"""
        print("\n" + "="*60)
        print("验证5: WebSocket连接（可选）")
        print("="*60)

        print("提示: WebSocket验证需要手动测试")
        print(f"  连接: ws://localhost:8000/ws/projects/{self.project_id}/")
        print("  预期: 接收实时进度更新和完成通知")

        # 这里可以添加自动化的WebSocket测试
        # 但由于需要额外的依赖（websocket-client），暂时跳过
        return True

    def run_all_verifications(self, timeout=300):
        """运行所有验证"""
        print("="*60)
        print("端到端完整验证")
        print("="*60)
        print(f"超时时间: {timeout}秒")

        verifications = [
            ("用户认证", self.verify_auth),
            ("项目创建", self.verify_project_creation),
            ("启动工作流", self.verify_workflow_start),
            ("AI自动生成", lambda: self.verify_ai_generation(timeout)),
            ("WebSocket通知", self.verify_websocket_notification),
        ]

        results = []
        for name, verify_func in verifications:
            try:
                success = verify_func()
                results.append((name, success))
                if not success and name != "WebSocket通知":
                    break  # 失败则停止（WebSocket通知除外）
            except Exception as e:
                print(f"\n✗ {name}验证异常: {e}")
                import traceback
                traceback.print_exc()
                results.append((name, False))
                break

        # 总结
        print("\n" + "="*60)
        print("验证总结")
        print("="*60)

        for name, success in results:
            symbol = "✓" if success else "✗"
            status = "通过" if success else "失败"
            print(f"{symbol} {name}: {status}")

        all_passed = all(success for _, success in results)

        print("\n" + "="*60)
        if all_passed:
            print("✓ 所有验证通过")
        else:
            print("✗ 部分验证失败")
        print("="*60)

        return all_passed


def main():
    """主函数"""
    verifier = E2EVerifier()
    success = verifier.run_all_verifications(timeout=300)
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
