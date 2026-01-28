"""
文件存储工具
职责: 提供基于日期分层的文件存储功能，自动处理文件名重复
"""

from datetime import datetime
from pathlib import Path
from typing import Tuple


class DateBasedFileStorage:
    """
    基于日期的文件存储工具

    功能:
    - 在指定目录下创建日期子目录 (格式: YYYY-MM-DD)
    - 自动处理文件名重复 (添加后缀 _1, _2, _3...)
    - 支持自定义基础目录和文件扩展名

    示例:
        storage/image/
            2025-11-30/
                abc123.png
                abc123_1.png
                def456.png
            2025-12-01/
                xyz789.png
    """

    def __init__(self, base_dir: str):
        """
        初始化文件存储器

        Args:
            base_dir: 基础存储目录 (例如: 'storage/image' 或 'storage/video')
        """
        self.base_dir = Path(base_dir)

    def get_unique_filepath(
        self,
        filename: str,
        date: datetime = None,
        create_dirs: bool = True
    ) -> Tuple[Path, str]:
        """
        获取唯一的文件保存路径

        Args:
            filename: 原始文件名 (例如: 'image.png')
            date: 日期对象 (默认为今天)
            create_dirs: 是否自动创建目录 (默认True)

        Returns:
            Tuple[完整路径对象, 相对路径字符串]

        示例:
            >>> storage = DateBasedFileStorage('storage/image')
            >>> full_path, rel_path = storage.get_unique_filepath('test.png')
            >>> print(full_path)  # Path('storage/image/2025-11-30/test.png')
            >>> print(rel_path)   # '2025-11-30/test.png'

            # 如果文件已存在,自动添加后缀
            >>> full_path, rel_path = storage.get_unique_filepath('test.png')
            >>> print(full_path)  # Path('storage/image/2025-11-30/test_1.png')
        """
        # 使用传入的日期或今天
        if date is None:
            date = datetime.now()

        # 创建日期目录 (格式: YYYY-MM-DD)
        date_str = date.strftime('%Y-%m-%d')
        date_dir = self.base_dir / date_str

        # 如果需要，创建目录
        if create_dirs:
            date_dir.mkdir(parents=True, exist_ok=True)

        # 分离文件名和扩展名
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2:
            base_name, extension = name_parts
            extension = f'.{extension}'
        else:
            base_name = filename
            extension = ''

        # 检查文件是否存在，如果存在则添加后缀
        counter = 0
        while True:
            if counter == 0:
                # 第一次尝试使用原始文件名
                new_filename = f'{base_name}{extension}'
            else:
                # 添加后缀 _1, _2, _3...
                new_filename = f'{base_name}_{counter}{extension}'

            full_path = date_dir / new_filename

            # 如果文件不存在，返回这个路径
            if not full_path.exists():
                # 计算相对路径 (相对于base_dir)
                relative_path = f'{date_str}/{new_filename}'
                return full_path, relative_path

            counter += 1

            # 安全检查：防止无限循环 (超过1000个重复文件就报错)
            if counter > 1000:
                raise ValueError(f'文件名重复次数过多: {filename}')

    def save_file(
        self,
        filename: str,
        content: bytes,
        date: datetime = None
    ) -> Tuple[Path, str]:
        """
        保存文件到日期目录

        Args:
            filename: 文件名
            content: 文件内容 (字节)
            date: 日期对象 (默认为今天)

        Returns:
            Tuple[完整路径对象, 相对路径字符串]
        """
        # 获取唯一文件路径
        full_path, relative_path = self.get_unique_filepath(
            filename=filename,
            date=date,
            create_dirs=True
        )

        # 写入文件
        full_path.write_bytes(content)

        return full_path, relative_path

    def get_date_dir(self, date: datetime = None) -> Path:
        """
        获取指定日期的目录路径

        Args:
            date: 日期对象 (默认为今天)

        Returns:
            Path: 日期目录路径
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime('%Y-%m-%d')
        return self.base_dir / date_str

    def ensure_date_dir_exists(self, date: datetime = None) -> Path:
        """
        确保日期目录存在

        Args:
            date: 日期对象 (默认为今天)

        Returns:
            Path: 创建的日期目录路径
        """
        date_dir = self.get_date_dir(date)
        date_dir.mkdir(parents=True, exist_ok=True)
        return date_dir


# 全局实例（可直接导入使用）
image_storage = DateBasedFileStorage('storage/image')
video_storage = DateBasedFileStorage('storage/video')
