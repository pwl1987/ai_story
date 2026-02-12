"""
AI 脚本解析服务

职责:
- 使用 AI 分析小说/剧本内容
- 自动提取故事结构信息
- 识别角色、场景、物品实体
- 支持 AI 推荐角色造型
- 处理大文本分段分析

Epic 10 Story 10.4: AI 脚本解析服务
"""

import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional

from django.conf import settings

from core.ai_client.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class ScriptParserService:
    """
    AI 脚本解析服务

    职责:
    - 章节自动拆分
    - 角色信息提取
    - 场景信息提取
    - 物品信息提取
    - AI 推荐角色造型

    配置:
    - llm_client: Ollama LLM 客户端
    - max_chunk_size: 最大文本块大小
    - temperature: AI 温度参数
    """

    def __init__(
        self,
        ollama_url: Optional[str] = None,
        model_name: str = "llama2",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        初始化脚本解析服务

        Args:
            ollama_url: Ollama 服务地址
            model_name: 模型名称
            temperature: AI 温度参数
            max_tokens: 最大生成 tokens
        """
        ollama_url = ollama_url or getattr(settings, "OLLAMA_API_URL", "http://localhost:11434")

        self.llm_client = OllamaClient(
            api_url=ollama_url,
            api_key="ollama",
            model_name=model_name
        )
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_chunk_size = 10000  # 最大文本块大小

    def parse_script(
        self,
        script_text: str,
        artwork_id: Optional[int] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """
        解析完整脚本

        Args:
            script_text: 脚本文本内容
            artwork_id: 作品 ID (可选)
            progress_callback: 进度回调函数

        Returns:
            Dict[str, Any]: 解析结果
                {
                    "success": bool,
                    "chapters": [...],
                    "characters": [...],
                    "scenes": [...],
                    "items": [...],
                    "summary": str,
                    "metadata": {...}
                }
        """
        try:
            # 1. 生成故事概要
            if progress_callback:
                progress_callback(10.0)

            summary = self._generate_summary(script_text)

            # 2. 拆分章节
            if progress_callback:
                progress_callback(30.0)

            chapters = self._split_chapters(script_text)

            # 3. 提取角色信息
            if progress_callback:
                progress_callback(50.0)

            characters = self._extract_characters(script_text)

            # 4. 提取场景信息
            if progress_callback:
                progress_callback(70.0)

            scenes = self._extract_scenes(script_text)

            # 5. 提取物品信息
            if progress_callback:
                progress_callback(90.0)

            items = self._extract_items(script_text)

            if progress_callback:
                progress_callback(100.0)

            return {
                "success": True,
                "chapters": chapters,
                "characters": characters,
                "scenes": scenes,
                "items": items,
                "summary": summary,
                "metadata": {
                    "total_chapters": len(chapters),
                    "total_characters": len(characters),
                    "total_scenes": len(scenes),
                    "total_items": len(items),
                    "text_length": len(script_text)
                }
            }

        except Exception as e:
            logger.error(f"脚本解析失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_summary(self, script_text: str) -> str:
        """
        生成故事概要

        Args:
            script_text: 脚本文本

        Returns:
            str: 故事概要
        """
        # 截取前 2000 字符用于概要生成
        text_sample = script_text[:2000]

        prompt = f"""请分析以下小说/剧本内容，生成一个简洁的故事概要（200字以内）。

内容：
{text_sample}

请以JSON格式返回：
{{
    "summary": "故事概要...",
    "genre": "题材（如：奇幻/科幻/都市）",
    "main_theme": "主要主题"
}}"""

        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                response = loop.run_until_complete(
                    self.llm_client.generate(
                        prompt=prompt,
                        max_tokens=500,
                        temperature=self.temperature
                    )
                )
            finally:
                loop.close()

            if response.success:
                # 解析 JSON 结果
                result = self._extract_json(response.text)
                return result.get("summary", response.text)

            return response.text

        except Exception as e:
            logger.error(f"生成概要失败: {e}")
            return "AI 概要生成失败"

    def _split_chapters(self, script_text: str) -> List[Dict[str, Any]]:
        """
        拆分章节

        Args:
            script_text: 脚本文本

        Returns:
            List[Dict[str, Any]]: 章节列表
        """
        # 先尝试 AI 分析
        prompt = f"""分析以下小说/剧本内容，识别章节结构。

内容（前 3000 字符）：
{script_text[:3000]}

请以JSON格式返回章节列表：
{{
    "chapters": [
        {{"title": "章节标题", "start_index": 0, "summary": "章节概要"}}
    ]
}}

如果没有明确章节，请按照情节划分。"""

        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                response = loop.run_until_complete(
                    self.llm_client.generate(
                        prompt=prompt,
                        max_tokens=1000,
                        temperature=self.temperature
                    )
                )
            finally:
                loop.close()

            if response.success:
                result = self._extract_json(response.text)
                if "chapters" in result:
                    return result["chapters"]

        except Exception as e:
            logger.warning(f"AI 章节分析失败，使用规则方法: {e}")

        # 规则方法：按常见章节标记拆分
        return self._split_chapters_by_rules(script_text)

    def _split_chapters_by_rules(self, script_text: str) -> List[Dict[str, Any]]:
        """
        使用规则方法拆分章节

        Args:
            script_text: 脚本文本

        Returns:
            List[Dict[str, Any]]: 章节列表
        """
        chapters = []
        lines = script_text.split('\n')

        current_chapter = None
        current_content = []
        chapter_index = 0
        char_count = 0

        # 常见章节标记模式
        chapter_patterns = [
            r'^[第\s\d]+章\s*.*',  # 第X章 标题
            r'^Chapter\s*\d+.*',  # Chapter X
            r'^\d+\.\s+.*',  # 1. 标题
            r'^【.*】',  # 【章节】
            r'^第.*章',  # 第*章
        ]

        for line in lines:
            stripped = line.strip()

            # 检查是否是章节标题
            is_chapter = False
            for pattern in chapter_patterns:
                if re.match(pattern, stripped):
                    is_chapter = True
                    break

            if is_chapter:
                # 保存上一章
                if current_chapter:
                    chapters.append({
                        "title": current_chapter,
                        "chapter_number": chapter_index,
                        "content": '\n'.join(current_content),
                        "char_count": char_count,
                        "summary": ""
                    })
                    chapter_index += 1

                current_chapter = stripped
                current_content = []
                char_count = 0
            elif stripped:
                current_content.append(line)
                char_count += len(line)

        # 保存最后一章
        if current_chapter and current_content:
            chapters.append({
                "title": current_chapter,
                "chapter_number": chapter_index,
                "content": '\n'.join(current_content),
                "char_count": char_count,
                "summary": ""
            })

        # 如果没有检测到章节，整个文本作为一章
        if not chapters:
            chapters = [{
                "title": "全文",
                "chapter_number": 0,
                "content": script_text,
                "char_count": len(script_text),
                "summary": ""
            }]

        return chapters

    def _extract_characters(self, script_text: str) -> List[Dict[str, Any]]:
        """
        提取角色信息

        Args:
            script_text: 脚本文本

        Returns:
            List[Dict[str, Any]]: 角色列表
        """
        # 截取分析文本（避免超出上下文限制）
        text_sample = script_text[:5000] if len(script_text) > 5000 else script_text

        prompt = f"""分析以下小说/剧本内容，提取所有角色信息。

内容：
{text_sample}

请以JSON格式返回角色列表：
{{
    "characters": [
        {{
            "name": "角色名",
            "display_name": "显示名",
            "description": "角色描述（外貌、性格等）",
            "personality": "性格特点",
            "role": "角色定位（主角/配角/反派等）",
            "appearance_count": "预估出现次数",
            "dialogue_count": "预估对话次数"
        }}
    ]
}}

只提取有明确名字和描述的角色，不要包含背景角色。"""

        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                response = loop.run_until_complete(
                    self.llm_client.generate(
                        prompt=prompt,
                        max_tokens=1500,
                        temperature=self.temperature
                    )
                )
            finally:
                loop.close()

            if response.success:
                result = self._extract_json(response.text)
                if "characters" in result:
                    return result["characters"]

        except Exception as e:
            logger.error(f"AI 角色提取失败: {e}")

        # 规则方法：简单提取
        return self._extract_characters_by_rules(script_text)

    def _extract_characters_by_rules(self, script_text: str) -> List[Dict[str, Any]]:
        """
        使用规则方法提取角色

        Args:
            script_text: 脚本文本

        Returns:
            List[Dict[str, Any]]: 角色列表
        """
        characters = {}

        # 常见中文人名模式（2-4个汉字）
        name_pattern = r'[\u4e00-\u9fa5]{2,4}'

        # 寻找对话标记
        dialogue_pattern = r'["「]([^"]+)["」]'

        # 统计对话中的名字
        for match in re.finditer(dialogue_pattern, script_text):
            dialogue = match.group(1)
            # 尝试提取说话人
            if '说' in dialogue or '道' in dialogue:
                # 可能在对话中，跳过
                continue

        # 提取引号外的名字（简单实现）
        words = re.findall(name_pattern, script_text[:10000])
        for word in words:
            # 过滤常见虚词
            if word in ['这个', '那个', '什么', '怎么', '一个', '两个', '时候']:
                continue
            if word not in characters:
                characters[word] = {
                    "name": word,
                    "display_name": word,
                    "description": "",
                    "personality": "",
                    "role": "unknown",
                    "appearance_count": 1,
                    "dialogue_count": 0
                }
            else:
                characters[word]["appearance_count"] += 1

        # 按出现次数排序
        sorted_characters = sorted(
            characters.values(),
            key=lambda x: x["appearance_count"],
            reverse=True
        )[:10]  # 最多返回 10 个角色

        return sorted_characters

    def _extract_scenes(self, script_text: str) -> List[Dict[str, Any]]:
        """
        提取场景信息

        Args:
            script_text: 脚本文本

        Returns:
            List[Dict[str, Any]]: 场景列表
        """
        # 常见场景关键词
        scene_keywords = {
            '室内': ['房间', '客厅', '卧室', '办公室', '教室', '餐厅', '厨房', '浴室'],
            '室外': ['街道', '公园', '广场', '森林', '山', '河', '海边', '广场'],
            '特殊': ['实验室', '医院', '学校', '城堡', '宫殿', '飞船', '战场']
        }

        scenes = {}
        text_lower = script_text.lower()

        for category, keywords in scene_keywords.items():
            for keyword in keywords:
                # 统计出现次数
                count = text_lower.count(keyword.lower())
                if count > 0:
                    scene_key = f"{keyword}_{category}"
                    if scene_key not in scenes:
                        scenes[scene_key] = {
                            "name": keyword,
                            "category": category,
                            "type": "physical" if category == "室内" else "outdoor",
                            "appearance_count": count
                        }
                    else:
                        scenes[scene_key]["appearance_count"] += count

        # 按出现次数排序
        sorted_scenes = sorted(
            scenes.values(),
            key=lambda x: x["appearance_count"],
            reverse=True
        )

        # 添加场景编号
        for i, scene in enumerate(sorted_scenes):
            scene["scene_number"] = i + 1

        return sorted_scenes

    def _extract_items(self, script_text: str) -> List[Dict[str, Any]]:
        """
        提取物品信息

        Args:
            script_text: 脚本文本

        Returns:
            List[Dict[str, Any]]: 物品列表
        """
        # 常见物品关键词
        item_keywords = [
            '武器', '剑', '刀', '枪', '弓箭',
            '饰品', '项链', '戒指', '手镯',
            '道具', '药水', '卷轴', '地图',
            '交通工具', '车', '船', '马',
            '日常用品', '手机', '电脑', '钱包'
        ]

        items = {}

        for keyword in item_keywords:
            count = script_text.count(keyword)
            if count > 0:
                items[keyword] = {
                    "name": keyword,
                    "item_type": self._guess_item_type(keyword),
                    "appearance_count": count,
                    "description": ""
                }

        # 按出现次数排序
        sorted_items = sorted(
            items.values(),
            key=lambda x: x["appearance_count"],
            reverse=True
        )

        return sorted_items

    def _guess_item_type(self, item_name: str) -> str:
        """
        猜测物品类型

        Args:
            item_name: 物品名称

        Returns:
            str: 物品类型
        """
        type_map = {
            '武器': 'weapon',
            '剑': 'weapon', '刀': 'weapon', '枪': 'weapon',
            '饰品': 'accessory',
            '项链': 'accessory', '戒指': 'accessory',
            '道具': 'tool',
            '交通工具': 'vehicle',
            '车': 'vehicle', '船': 'vehicle',
            '日常用品': 'daily'
        }

        for key, item_type in type_map.items():
            if key in item_name:
                return item_type

        return 'unknown'

    def analyze_character_poses(
        self,
        character_description: str,
        scene_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        AI 分析角色造型推荐

        Args:
            character_description: 角色描述
            scene_context: 场景上下文（可选）

        Returns:
            Dict[str, Any]: 造型推荐结果
        """
        context = f"\n场景上下文：{scene_context}" if scene_context else ""

        prompt = f"""分析以下角色描述，推荐合适的造型类型。

角色描述：
{character_description}
{context}

可选造型类型：
- casual: 休闲装（适合日常、居家场景）
- formal: 正式装（适合宴会、会议场景）
- battle: 战斗装（适合战斗、冲突场景）
- school: 校服（适合校园场景）
- home: 居家服（适合家庭场景）

请以JSON格式返回推荐结果：
{{
    "recommended_poses": [
        {{
            "pose_type": "casual",
            "confidence": 0.9,
            "reason": "推荐理由"
        }}
    ]
}}"""

        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                response = loop.run_until_complete(
                    self.llm_client.generate(
                        prompt=prompt,
                        max_tokens=500,
                        temperature=self.temperature
                    )
                )
            finally:
                loop.close()

            if response.success:
                result = self._extract_json(response.text)
                if "recommended_poses" in result:
                    return {
                        "success": True,
                        "recommendations": result["recommended_poses"]
                    }

        except Exception as e:
            logger.error(f"AI 造型推荐失败: {e}")

        # 默认推荐
        return {
            "success": True,
            "recommendations": [
                {
                    "pose_type": "casual",
                    "confidence": 0.7,
                    "reason": "默认推荐休闲造型"
                }
            ]
        }

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取 JSON

        Args:
            text: 包含 JSON 的文本

        Returns:
            Dict[str, Any]: 解析后的 JSON 对象
        """
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 代码块
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取大括号内容
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {}

    def parse_large_script(
        self,
        script_text: str,
        chunk_size: Optional[int] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """
        解析大文本脚本（分段处理）

        Args:
            script_text: 脚本文本
            chunk_size: 每段大小
            progress_callback: 进度回调函数

        Returns:
            Dict[str, Any]: 解析结果
        """
        chunk_size = chunk_size or self.max_chunk_size
        text_length = len(script_text)

        # 如果文本不大，直接使用常规解析
        if text_length <= chunk_size:
            return self.parse_script(script_text, progress_callback=progress_callback)

        # 分段处理
        chunks = []
        start = 0

        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunk = script_text[start:end]
            chunks.append(chunk)
            start = end

        # 合并各段的结果
        all_characters = {}
        all_scenes = {}
        all_items = {}

        for i, chunk in enumerate(chunks):
            progress = (i + 1) / len(chunks) * 100
            if progress_callback:
                progress_callback(progress * 0.7)  # 分析占 70%

            result = self.parse_script(chunk)

            if result.get("success"):
                # 合并角色
                for char in result.get("characters", []):
                    name = char.get("name")
                    if name:
                        if name not in all_characters:
                            all_characters[name] = char
                        else:
                            all_characters[name]["appearance_count"] += char.get("appearance_count", 0)

                # 合并场景
                for scene in result.get("scenes", []):
                    key = f"{scene.get('name')}_{scene.get('category', '')}"
                    if key not in all_scenes:
                        all_scenes[key] = scene
                    else:
                        all_scenes[key]["appearance_count"] += scene.get("appearance_count", 0)

                # 合并物品
                for item in result.get("items", []):
                    name = item.get("name")
                    if name:
                        if name not in all_items:
                            all_items[name] = item
                        else:
                            all_items[name]["appearance_count"] += item.get("appearance_count", 0)

        # 转换为列表并排序
        sorted_characters = sorted(
            all_characters.values(),
            key=lambda x: x.get("appearance_count", 0),
            reverse=True
        )

        sorted_scenes = sorted(
            all_scenes.values(),
            key=lambda x: x.get("appearance_count", 0),
            reverse=True
        )

        sorted_items = sorted(
            all_items.values(),
            key=lambda x: x.get("appearance_count", 0),
            reverse=True
        )

        # 生成整体概要（使用第一段的结果）
        summary = ""
        chapters = []

        if chunks:
            first_result = self.parse_script(chunks[0])
            if first_result.get("success"):
                summary = first_result.get("summary", "")
                chapters = first_result.get("chapters", [])

        if progress_callback:
            progress_callback(100.0)

        return {
            "success": True,
            "chapters": chapters,
            "characters": sorted_characters,
            "scenes": sorted_scenes,
            "items": sorted_items,
            "summary": summary,
            "metadata": {
                "total_chunks": len(chunks),
                "total_characters": len(sorted_characters),
                "total_scenes": len(sorted_scenes),
                "total_items": len(sorted_items),
                "text_length": text_length
            }
        }


# 单例模式
_service_instance: Optional[ScriptParserService] = None


def get_script_parser_service() -> ScriptParserService:
    """获取脚本解析服务单例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ScriptParserService()
    return _service_instance
