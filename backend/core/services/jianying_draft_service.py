"""
剪映草稿生成服务
职责: 将项目的视频片段和字幕拼接生成剪映草稿
遵循单一职责原则(SRP)
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import pyJianYingDraft as draft
from django.conf import settings
from pyJianYingDraft import IntroType, tim, trange

logger = logging.getLogger(__name__)


class JianyingDraftGenerator:
    """
    剪映草稿生成器

    职责:
    - 读取项目的视频文件和字幕数据
    - 创建剪映草稿项目
    - 拼接多个视频片段
    - 为每个视频添加对应字幕
    - 添加背景音乐、转场动画等
    - 保存草稿到剪映目录
    """

    # 支持的视频格式
    SUPPORTED_VIDEO_FORMATS = (".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv")

    # 支持的字幕格式
    SUPPORTED_SUBTITLE_FORMATS = (".txt", ".srt")

    def __init__(self, draft_folder_path: str = None):
        """
        初始化剪映草稿生成器

        Args:
            draft_folder_path: 剪映草稿文件夹路径，如果为None则从配置读取
        """
        if draft_folder_path:
            self.draft_folder_path = draft_folder_path
        else:
            # 从Django配置读取，如果没有则使用默认路径
            self.draft_folder_path = getattr(
                settings,
                "JIANYING_DRAFT_FOLDER",
                os.path.expanduser("~/Documents/JianyingPro Drafts"),
            )

        # 确保目录存在
        os.makedirs(self.draft_folder_path, exist_ok=True)

        # 初始化草稿文件夹对象
        self.draft_folder = draft.DraftFolder(self.draft_folder_path)

        logger.info(f"剪映草稿生成器初始化完成，草稿路径: {self.draft_folder_path}")

    def generate_draft(
        self,
        project_name: str,
        video_files: List[str],
        subtitles: List[str] = None,
        background_music: str = None,
        width: int = 1080,
        height: int = 1920,
        allow_replace: bool = True,
        **options,
    ) -> str:
        """
        生成剪映草稿

        Args:
            project_name: 项目名称
            video_files: 视频文件路径列表（按顺序拼接）
            subtitles: 字幕文本列表（与视频一一对应，可选）
            background_music: 背景音乐文件路径（可选）
            width: 视频宽度（默认1080）
            height: 视频高度（默认1920，竖屏）
            allow_replace: 是否允许替换已存在的草稿（默认True）
            **options: 其他可选参数
                - music_volume: 背景音乐音量（0-1，默认0.6）
                - music_fade_in: 音乐淡入时长（如"1s"，默认"1s"）
                - music_fade_out: 音乐淡出时长（如"0s"，默认"0s"）
                - add_intro_animation: 是否为第一个视频添加入场动画（默认True）
                - intro_type: 入场动画类型（默认IntroType.斜切）
                - subtitle_font: 字幕字体（默认draft.FontType.抖音美好体）
                - subtitle_color: 字幕颜色RGB元组（默认(1,0.749,0.09)黄色）
                - subtitle_size: 字幕大小（默认15）
                - subtitle_position_y: 字幕Y轴位置（-1到1，默认-0.73）

        Returns:
            str: 草稿保存路径

        Raises:
            ValueError: 参数验证失败
            FileNotFoundError: 视频或音乐文件不存在
            Exception: 草稿生成失败
        """
        # 参数验证
        if not video_files:
            raise ValueError("视频文件列表不能为空")

        # 验证视频文件是否存在
        for video_file in video_files:
            if not os.path.exists(video_file):
                raise FileNotFoundError(f"视频文件不存在: {video_file}")

        # 验证背景音乐文件
        if background_music and not os.path.exists(background_music):
            raise FileNotFoundError(f"背景音乐文件不存在: {background_music}")

        # 如果没有提供字幕，使用默认字幕
        if subtitles is None:
            subtitles = ["" for _ in video_files]
        elif len(subtitles) != len(video_files):
            raise ValueError(f"字幕数量({len(subtitles)})与视频数量({len(video_files)})不一致")

        logger.info(f"开始生成剪映草稿: {project_name}，共{len(video_files)}个视频片段")

        try:
            # 创建剪映草稿
            script = self.draft_folder.create_draft(
                project_name, width, height, allow_replace=allow_replace
            )

            # 添加轨道：音频、视频、文本
            script.add_track(draft.TrackType.audio)
            script.add_track(draft.TrackType.video)
            script.add_track(draft.TrackType.text)

            # 添加背景音乐
            if background_music:
                self._add_background_music(script, background_music, options)

            # 添加视频片段和字幕
            self._add_video_segments(script, video_files, subtitles, options)

            # 保存草稿
            script.save()

            draft_path = os.path.join(self.draft_folder_path, project_name)
            logger.info(f"剪映草稿生成成功: {draft_path}")

            return draft_path

        except Exception as e:
            logger.error(f"生成剪映草稿失败: {e!s}", exc_info=True)
            raise Exception(f"生成剪映草稿失败: {e!s}")

    def _add_background_music(self, script, music_file: str, options: Dict[str, Any]):
        """添加背景音乐"""
        try:
            # 获取音乐时长（这里简化处理，实际应该获取总视频时长）
            music_volume = options.get("music_volume", 0.6)
            fade_in = options.get("music_fade_in", "1s")
            fade_out = options.get("music_fade_out", "0s")

            # 创建音频片段
            audio_segment = draft.AudioSegment(
                music_file,
                trange("0s", "5s"),  # 音频时长，实际应根据总视频时长调整
                volume=music_volume,
            )

            # 添加淡入淡出效果
            audio_segment.add_fade(fade_in, fade_out)

            # 添加到轨道
            script.add_segment(audio_segment)

            logger.debug(f"已添加背景音乐: {music_file}")

        except Exception as e:
            logger.warning(f"添加背景音乐失败: {e!s}")
            # 背景音乐失败不影响主流程，只记录警告

    def _add_video_segments(
        self, script, video_files: List[str], subtitles: List[str], options: Dict[str, Any]
    ):
        """添加视频片段和字幕"""
        # 获取配置参数
        add_intro = options.get("add_intro_animation", True)
        intro_type = options.get("intro_type", IntroType.斜切)
        subtitle_font = options.get("subtitle_font", draft.FontType.抖音美好体)
        subtitle_color = options.get("subtitle_color", (1, 0.749, 0.09))
        subtitle_size = options.get("subtitle_size", 15)
        subtitle_position_y = options.get("subtitle_position_y", -0.73)

        current_start_time = tim("0s")

        for i, (video_file, subtitle_text) in enumerate(zip(video_files, subtitles)):
            try:
                # 获取视频素材信息
                video_material = draft.VideoMaterial(video_file)
                video_duration = video_material.duration

                # 视频片段时间范围
                timerange = trange(current_start_time, video_duration)

                # 创建视频片段
                video_segment = draft.VideoSegment(video_file, timerange)

                # 第一个视频添加入场动画
                if i == 0 and add_intro:
                    video_segment.add_animation(intro_type)

                # 添加视频片段到轨道
                script.add_segment(video_segment)

                logger.debug(
                    f"已添加视频片段 {i + 1}/{len(video_files)}: {os.path.basename(video_file)}"
                )

                # 添加字幕（如果有）
                if subtitle_text:
                    self._add_subtitle(
                        script,
                        subtitle_text,
                        timerange,
                        subtitle_font,
                        subtitle_color,
                        subtitle_size,
                        subtitle_position_y,
                    )

                # 更新变量，为下一个视频做准备
                current_start_time = timerange.end

            except Exception as e:
                logger.error(f"添加视频片段 {i + 1} 失败: {e!s}")
                raise

    def _add_subtitle(self, script, text: str, timerange, font, color, size, position_y):
        """添加字幕"""
        try:
            # 创建字幕片段
            text_segment = draft.TextSegment(
                text,
                timerange,
                font=font,
                style=draft.TextStyle(
                    color=color,
                    size=size,
                    align=1,  # 居中对齐
                    auto_wrapping=True,
                ),
                clip_settings=draft.ClipSettings(
                    transform_y=position_y,  # 位置在屏幕下方
                ),
            )

            # 添加字幕片段到文本轨道
            script.add_segment(text_segment)

            logger.debug(f"已添加字幕: {text[:20]}...")

        except Exception as e:
            logger.warning(f"添加字幕失败: {e!s}")
            # 字幕失败不影响主流程

    def generate_from_project_data(
        self,
        project_name: str,
        scenes: List[Dict[str, Any]],
        background_music: str = None,
        **options,
    ) -> str:
        """
        从项目场景数据生成剪映草稿

        Args:
            project_name: 项目名称
            scenes: 场景数据列表，每个场景包含:
                - video_urls: 视频URL列表或本地路径列表
                - narration_text: 旁白文本（用作字幕）
            background_music: 背景音乐文件路径（可选）
            **options: 其他可选参数

        Returns:
            str: 草稿保存路径
        """
        # 提取视频文件路径和字幕
        video_files = []
        subtitles = []

        for scene in scenes:
            # 获取视频路径（优先使用本地路径）
            video_urls = scene.get("video_urls", [])
            if not video_urls:
                logger.warning(f"场景 {scene.get('scene_number', '?')} 没有视频URL，跳过")
                continue

            # 处理视频URL/路径
            video_url = video_urls[0] if isinstance(video_urls, list) else video_urls

            # 如果是URL，需要先下载到本地（这里简化处理，假设已经是本地路径）
            if isinstance(video_url, dict):
                video_path = video_url.get("url", "")
            else:
                video_path = video_url

            # 转换为本地绝对路径
            if not os.path.isabs(video_path):
                # 假设视频存储在 STORAGE_ROOT/video 目录
                storage_root = getattr(settings, "STORAGE_ROOT", "")
                video_dir = Path(storage_root) / "video"
                path_list = video_path.split("/")[-2:]
                video_path = str(Path(video_dir, *path_list))

            if not os.path.exists(video_path):
                logger.warning(f"视频文件不存在: {video_path}，跳过")
                continue

            video_files.append(video_path)

            # 获取字幕文本
            subtitle = scene.get("narration", "")
            subtitles.append(subtitle)

        if not video_files:
            raise ValueError("没有可用的视频文件")

        logger.info(f"从 {len(scenes)} 个场景中提取了 {len(video_files)} 个有效视频")

        # 调用生成方法
        return self.generate_draft(
            project_name=project_name,
            video_files=video_files,
            subtitles=subtitles,
            background_music=background_music,
            **options,
        )
