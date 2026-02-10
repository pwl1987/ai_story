#!/usr/bin/env python
"""
创建测试用户 - Story 8.1手动验证
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth.models import User


def create_test_users():
    """创建测试用户"""

    users = [
        {
            "username": "admin",
            "password": "admin123",
            "email": "admin@example.com",
            "is_staff": True,
            "is_superuser": True,
        },
        {
            "username": "staff",
            "password": "staff123",
            "email": "staff@example.com",
            "is_staff": True,
            "is_superuser": False,
        },
        {
            "username": "normal",
            "password": "normal123",
            "email": "normal@example.com",
            "is_staff": False,
            "is_superuser": False,
        },
    ]

    for user_data in users:
        password = user_data.pop("password")
        username = user_data["username"]

        # 检查用户是否已存在
        if User.objects.filter(username=username).exists():
            print(f"⚠️  用户 {username} 已存在，跳过创建")
            continue

        # 创建用户
        user = User.objects.create_user(**user_data)
        user.set_password(password)
        user.save()

        print(f"✅ 创建用户: {username} (密码: {password})")
        print(f"   - is_staff: {user.is_staff}")
        print(f"   - is_superuser: {user.is_superuser}")

    print("\n📊 用户创建完成！当前用户列表:")
    for user in User.objects.all():
        print(f"   - {user.username} (staff={user.is_staff}, super={user.is_superuser})")


if __name__ == "__main__":
    create_test_users()
