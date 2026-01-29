"""
pytest配置文件 - apps/models模块
共享测试辅助函数
"""


def filter_mock_data(queryset):
    """
    过滤掉Mock迁移数据的辅助函数

    Args:
        queryset: Django QuerySet或列表

    Returns:
        过滤后的列表，排除名称以'Mock'开头的对象
    """
    return [item for item in queryset if not item.name.startswith("Mock")]
