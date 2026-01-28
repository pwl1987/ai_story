"""
端到端工作流测试脚本
用于测试完整的工作流执行

前置条件:
1. 运行 setup_mock_env.py
2. 运行 create_test_project.py
3. 启动Redis: docker run -d -p 6379:6379 redis:latest
4. 启动Celery Worker: uv run celery -A config worker -Q llm,image,video -l info
5. 启动Django ASGI: ./run_asgi.sh

运行方式:
    cd backend
    uv run python scripts/test_e2e_workflow.py

依赖: 需要先运行 setup_mock_env.py 和 create_test_project.py
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


def get_auth_token(base_url="http://localhost:8000/api/v1"):
    """
    获取认证token

    Returns:
        tuple: (token, user_id)
    """
    print("\n1. 获取认证token...")

    # 尝试登录
    response = requests.post(f"{base_url}/users/login/", json={
        "username": "e2e_test_user",
        "password": "test_password"
    })

    if response.status_code == 200:
        data = response.json()
        token = data.get('token') or data.get('access')
        user_id = data.get('user_id')
        print("✓ 登录成功")
        return token, user_id
    else:
        print(f"✗ 登录失败: {response.status_code}")
        print(f"  响应: {response.text}")
        return None, None


def get_test_project():
    """
    获取测试项目

    Returns:
        Project: 测试项目对象
    """
    print("\n2. 获取测试项目...")

    try:
        project = Project.objects.get(name='E2E Test Project')
        print(f"✓ 找到测试项目: {project.name} (ID: {project.id})")
        print(f"  状态: {project.status}")
        print(f"  阶段数: {project.stages.count()}")
        return project
    except Project.DoesNotExist:
        print("✗ 测试项目不存在")
        print("  请先运行: uv run python scripts/create_test_project.py")
        return None


def start_workflow(project_id, token, base_url="http://localhost:8000/api/v1"):
    """
    启动工作流

    Args:
        project_id: 项目ID
        token: 认证token
        base_url: API基础URL

    Returns:
        dict: 包含task_id和channel的响应
    """
    print("\n3. 启动工作流...")

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{base_url}/projects/{project_id}/execute_full_pipeline/"

    response = requests.post(url, headers=headers)

    if response.status_code == 202:
        data = response.json()
        print("✓ 工作流已启动")
        print(f"  任务ID: {data['task_id']}")
        print(f"  频道: {data['channel']}")
        print(f"  项目ID: {data['project_id']}")
        return data
    else:
        print(f"✗ 启动失败: {response.status_code}")
        print(f"  响应: {response.text}")
        return None


def monitor_progress(project_id, token, base_url="http://localhost:8000/api/v1", timeout=300):
    """
    监控工作流进度

    Args:
        project_id: 项目ID
        token: 认证token
        base_url: API基础URL
        timeout: 超时时间（秒）

    Returns:
        bool: 工作流是否成功完成
    """
    print("\n4. 监控工作流进度...")

    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()

    while time.time() - start_time < timeout:
        # 获取项目状态
        response = requests.get(f"{base_url}/projects/{project_id}/", headers=headers)

        if response.status_code != 200:
            print(f"\n✗ 获取项目状态失败: {response.status_code}")
            return False

        project = response.json()
        status = project['status']
        stages = project['stages']

        # 计算完成进度
        completed = sum(1 for s in stages if s['status'] == 'completed')
        total = len(stages)

        # 构建进度条
        progress_bar = '█' * completed + '░' * (total - completed)
        elapsed = int(time.time() - start_time)

        print(f"\r  进度: [{progress_bar}] {completed}/{total} | 状态: {status} | 已用时: {elapsed}秒", end='')

        # 检查是否完成
        if status == 'completed':
            print("\n\n✓ 工作流完成！")
            print("\n  阶段详情:")
            for stage in stages:
                print(f"    - {stage['stage_type']}: {stage['status']}")
            return True
        elif status == 'failed':
            print("\n\n✗ 工作流失败")
            # 显示失败的阶段
            for stage in stages:
                if stage['status'] == 'failed':
                    print(f"    失败阶段: {stage['stage_type']}")
                    if stage.get('error_message'):
                        print(f"    错误信息: {stage['error_message']}")
            return False

        time.sleep(2)

    print(f"\n\n✗ 超时（{timeout}秒）")
    return False


def main():
    """主函数"""
    print("=" * 60)
    print("端到端工作流测试")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1"

    try:
        # 1. 获取认证token
        token, _user_id = get_auth_token(base_url)
        if not token:
            print("\n✗ 无法获取认证token")
            return 1

        # 2. 获取测试项目
        project = get_test_project()
        if not project:
            return 1

        # 3. 启动工作流
        workflow_data = start_workflow(str(project.id), token, base_url)
        if not workflow_data:
            return 1

        # 4. 监控进度
        success = monitor_progress(str(project.id), token, base_url, timeout=300)

        print("\n" + "=" * 60)
        if success:
            print("✓ 端到端测试通过")
            print("=" * 60)
            return 0
        else:
            print("✗ 端到端测试失败")
            print("=" * 60)
            return 1

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
