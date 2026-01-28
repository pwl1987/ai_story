"""
Pipeline适配器测试配置
解决SQLite数据库锁和SynchronousOnlyOperation问题
"""
import os
import tempfile

import pytest


# 配置测试使用文件数据库而非内存数据库
@pytest.fixture(scope='session')
def django_db_setup():
    """
    配置测试使用文件型SQLite数据库而非内存数据库
    解决sync_to_async跨线程访问导致的数据库锁问题
    """
    # 创建临时文件数据库
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test_db.sqlite3')

    # 返回配置
    yield {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': db_path,
        'TEST': {
            'NAME': db_path,
        }
    }

    # 清理临时文件
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        os.rmdir(temp_dir)
    except:
        pass


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    为所有测试启用数据库访问
    """
    pass


# 为所有django_db标记的测试启用transaction
@pytest.fixture(autouse=True)
def django_db_use_transaction(db):
    """
    使用真实事务而不是内存数据库
    """
    pass


# 为测试添加必要的设置
@pytest.fixture(scope='session')
def django_db_blocked():
    """
    覆盖默认的数据库阻止行为
    """
    pass
