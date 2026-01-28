#!/usr/bin/env python
"""
日志查询工具
Story 2.7 - 日志查询功能

使用示例:
    # 查询所有Celery任务失败日志
    python scripts/query_logs.py --logger apps.celery --event task_failure

    # 查询慢请求
    python scripts/query_logs.py --logger apps.api --is-slow-request true

    # 查询最近10条日志
    python scripts/query_logs.py --limit 10

    # 按时间范围查询
    python scripts/query_logs.py --since 1h
"""
import argparse
import json
import os
import sys
import django
from datetime import datetime, timedelta

# Django环境设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from django.conf import settings


def query_logs_from_file(log_file, filters=None, limit=100, since=None):
    """
    从日志文件查询日志

    Args:
        log_file: 日志文件路径
        filters: 过滤条件字典
        limit: 返回结果数量限制
        since: 时间范围（如1h, 30m）

    Returns:
        list: 匹配的日志条目
    """
    results = []

    # 计算时间阈值
    since_time = None
    if since:
        now = datetime.now()
        if since.endswith('h'):
            hours = int(since[:-1])
            since_time = now - timedelta(hours=hours)
        elif since.endswith('m'):
            minutes = int(since[:-1])
            since_time = now - timedelta(minutes=minutes)

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if len(results) >= limit:
                    break

                try:
                    log_entry = json.loads(line.strip())

                    # 应用过滤条件
                    if filters:
                        match = True
                        for key, value in filters.items():
                            # 处理嵌套的extra_fields
                            if '.' in key:
                                parts = key.split('.')
                                if parts[0] == 'extra_fields':
                                    field_value = log_entry.get('extra_fields', {}).get(parts[1])
                                else:
                                    # 其他嵌套字段暂不支持
                                    match = False
                                    break
                            else:
                                if key not in log_entry:
                                    match = False
                                    break
                                field_value = log_entry.get(key)

                            if field_value != value:
                                match = False
                                break

                        if not match:
                            continue

                    # 应用时间过滤
                    if since_time:
                        log_time_str = log_entry.get('timestamp', '')
                        if log_time_str:
                            try:
                                # 解析时间戳（格式: 2026-01-28 16:54:54,093）
                                log_time = datetime.strptime(log_time_str.split(',')[0], '%Y-%m-%d %H:%M:%S')
                                if log_time < since_time:
                                    continue
                            except:
                                pass

                    results.append(log_entry)

                except (json.JSONDecodeError, KeyError):
                    # 跳过无法解析的行
                    continue

    except FileNotFoundError:
        print(f"错误: 日志文件不存在: {log_file}")
        return []

    return results


def print_results(results, format='text'):
    """
    打印查询结果

    Args:
        results: 查询结果列表
        format: 输出格式（text/json）
    """
    if format == 'json':
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for i, entry in enumerate(results, 1):
            print(f"\n[{i}] {entry.get('timestamp', '')} - {entry.get('level', '')}")
            print(f"Logger: {entry.get('logger', '')}")
            print(f"Message: {entry.get('message', '')}")

            # 打印extra_fields
            extra = entry.get('extra_fields', {})
            if extra:
                print("Details:")
                for key, value in extra.items():
                    print(f"  {key}: {value}")


def main():
    parser = argparse.ArgumentParser(description='AI Story 日志查询工具')
    parser.add_argument('--log-file', default='logs/app.log',
                       help='日志文件路径 (默认: logs/app.log)')
    parser.add_argument('--logger', help='按logger过滤')
    parser.add_argument('--level', help='按日志级别过滤 (INFO/WARNING/ERROR)')
    parser.add_argument('--event', help='按事件类型过滤')
    parser.add_argument('--is-slow-request', type=str,
                       help='按慢请求过滤 (true/false)')
    parser.add_argument('--task-name', help='按任务名过滤')
    parser.add_argument('--limit', type=int, default=50,
                       help='返回结果数量限制 (默认: 50)')
    parser.add_argument('--since', help='时间范围 (如: 1h, 30m)')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='输出格式 (默认: text)')
    parser.add_argument('--watch', action='store_true',
                       help='监控模式，持续输出新日志')

    args = parser.parse_args()

    # 构建过滤条件
    filters = {}
    if args.logger:
        filters['logger'] = args.logger
    if args.level:
        filters['level'] = args.level.upper()

    # 处理event字段（在extra_fields中）
    if args.event:
        filters['extra_fields.event'] = args.event
    if args.is_slow_request:
        filters['extra_fields.is_slow_request'] = args.is_slow_request.lower() == 'true'
    if args.task_name:
        filters['extra_fields.task_name'] = args.task_name

    # 查询日志
    results = query_logs_from_file(
        args.log_file,
        filters=filters if filters else None,
        limit=args.limit,
        since=args.since
    )

    # 打印结果
    if results:
        print(f"找到 {len(results)} 条日志:")
        print_results(results, format=args.format)
    else:
        print("未找到匹配的日志")

    # 监控模式
    if args.watch:
        print("\n监控模式 (Ctrl+C 退出)...")
        import time
        try:
            last_count = len(results)
            while True:
                time.sleep(5)
                new_results = query_logs_from_file(
                    args.log_file,
                    filters=filters if filters else None,
                    limit=0,  # 不限制
                    since='1m'  # 只看最近1分钟
                )
                if len(new_results) > last_count:
                    new_entries = new_results[last_count:]
                    print(f"\n新增 {len(new_entries)} 条日志:")
                    print_results(new_entries, format=args.format)
                    last_count = len(new_results)
        except KeyboardInterrupt:
            print("\n监控已停止")


if __name__ == '__main__':
    main()
