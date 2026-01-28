#!/usr/bin/env python
"""
端到端API测试脚本
调用execute_full_pipeline API并监控进度
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

def main():
    print("=" * 60)
    print("端到端API测试")
    print("=" * 60)
    
    # 1. 登录获取token
    print("\n1. 登录...")
    response = requests.post(f"{BASE_URL}/users/login/", json={
        "username": "e2e_test_user",
        "password": "test_password"
    })
    
    if response.status_code != 200:
        print(f"✗ 登录失败: {response.status_code}")
        print(response.text)
        return 1
    
    data = response.json().get('data', {})
    tokens = data.get('tokens', {})
    token = tokens.get('access')

    if not token:
        print("✗ 未获取到token")
        print("Response:", response.json())
        return 1

    print(f"✓ 登录成功")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 获取项目ID
    print("\n2. 获取项目ID...")
    response = requests.get(f"{BASE_URL}/projects/", headers=headers)
    
    if response.status_code != 200:
        print(f"✗ 获取项目列表失败: {response.status_code}")
        return 1
    
    projects = [p for p in response.json().get('results', []) if p['name'] == 'E2E Test Project']
    if not projects:
        print("✗ 未找到测试项目")
        return 1
    
    project_id = projects[0]['id']
    print(f"✓ 找到项目: {project_id}")
    
    # 3. 调用execute_full_pipeline API
    print(f"\n3. 启动完整工作流...")
    response = requests.post(f"{BASE_URL}/projects/{project_id}/execute_full_pipeline/", headers=headers)
    
    if response.status_code != 202:
        print(f"✗ 启动工作流失败: {response.status_code}")
        print(response.text)
        return 1
    
    data = response.json()
    task_id = data.get('task_id')
    channel = data.get('channel')
    
    print(f"✓ 工作流已启动")
    print(f"  Task ID: {task_id}")
    print(f"  Channel: {channel}")
    
    # 4. 监控进度
    print(f"\n4. 监控工作流进度...")
    print("-" * 60)
    
    max_wait = 300  # 最多等待5分钟
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{BASE_URL}/projects/{project_id}/", headers=headers)
        
        if response.status_code != 200:
            print(f"\n✗ 获取项目状态失败: {response.status_code}")
            break
        
        project = response.json()
        status = project.get('status')
        stages = project.get('stages', [])
        
        # 计算各阶段状态
        stage_summary = []
        for stage in stages:
            stage_type = stage.get('stage_type')
            stage_status = stage.get('status')
            stage_summary.append(f"{stage_type}:{stage_status}")
        
        completed = sum(1 for s in stages if s.get('status') == 'completed')
        total = len(stages)
        
        print(f"\r进度: {completed}/{total} 阶段完成 | {' '.join(stage_summary)}", end='', flush=True)
        
        if status == 'completed':
            print("\n\n✓ 工作流完成！")
            break
        elif status == 'failed':
            print("\n\n✗ 工作流失败")
            # 显示失败的阶段
            for stage in stages:
                if stage.get('status') == 'failed':
                    print(f"  失败阶段: {stage.get('stage_type')}")
                    print(f"  错误信息: {stage.get('error_message', 'Unknown')}")
            break
        
        time.sleep(2)
    else:
        print("\n\n✗ 超时")
        return 1
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    exit(main())
