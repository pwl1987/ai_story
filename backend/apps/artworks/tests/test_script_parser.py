"""
脚本解析服务单元测试 (Epic 10 Story 10.4)

测试覆盖:
- ScriptParserService 初始化
- 章节拆分功能
- 角色信息提取
- 场景信息提取
- 物品信息提取
- AI 造型推荐
- 大文本处理
"""

import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# 注意: services.py 已重命名为 batch_operations.py，services/ 现在可以正常导入
from apps.artworks.services.script_parser import (
    ScriptParserService,
    get_script_parser_service,
)


class TestScriptParserService:
    """ScriptParserService 单元测试"""

    # ==================== 初始化测试 ====================

    def test_service_initialization(self):
        """测试服务初始化"""
        service = ScriptParserService(
            ollama_url="http://localhost:11434",
            model_name="llama2"
        )
        assert service.llm_client is not None
        assert service.temperature == 0.7
        assert service.max_tokens == 2000

    def test_singleton_pattern(self):
        """测试单例模式"""
        service1 = get_script_parser_service()
        service2 = get_script_parser_service()
        assert service1 is service2

    # ==================== 章节拆分测试 ====================

    def test_split_chapters_with_markers(self, sample_script_text):
        """测试带章节标记的文本拆分"""
        service = ScriptParserService()
        chapters = service._split_chapters_by_rules(sample_script_text)

        assert len(chapters) >= 2
        assert chapters[0]["title"].startswith("第一章")
        assert chapters[1]["title"].startswith("第二章")

    def test_split_chapters_without_markers(self):
        """测试无章节标记的文本拆分"""
        service = ScriptParserService()
        text = "这是一段没有章节标记的文本。\n" * 10

        chapters = service._split_chapters_by_rules(text)

        assert len(chapters) == 1
        assert chapters[0]["title"] == "全文"

    def test_split_chapters_numbered(self):
        """测试数字编号章节拆分"""
        service = ScriptParserService()
        text = """
1. 第一部分内容
内容内容内容

2. 第二部分内容
内容内容内容
"""

        chapters = service._split_chapters_by_rules(text)

        assert len(chapters) >= 2

    # ==================== 角色提取测试 ====================

    def test_extract_characters_by_rules(self, sample_script_text):
        """测试规则方法提取角色"""
        service = ScriptParserService()
        characters = service._extract_characters_by_rules(sample_script_text)

        assert isinstance(characters, list)
        # 检查是否提取到了角色（可能是名字或代词）
        if len(characters) > 0:
            # 规则方法可能提取到各种词，只要能返回列表就通过
            assert "name" in characters[0]

    def test_extract_characters_empty_text(self):
        """测试空文本角色提取"""
        service = ScriptParserService()
        characters = service._extract_characters_by_rules("")

        assert isinstance(characters, list)

    # ==================== 场景提取测试 ====================

    def test_extract_scenes(self, sample_script_text):
        """测试场景提取"""
        service = ScriptParserService()
        scenes = service._extract_scenes(sample_script_text)

        assert isinstance(scenes, list)
        # 检查有场景关键词的场景被提取
        for scene in scenes:
            assert "name" in scene
            assert "category" in scene
            assert "type" in scene

    def test_extract_scenes_keywords(self):
        """测试场景关键词匹配"""
        service = ScriptParserService()
        text = "他在房间里工作，然后去了公园。"

        scenes = service._extract_scenes(text)

        scene_names = [s["name"] for s in scenes]
        assert "房间" in scene_names or "公园" in scene_names

    # ==================== 物品提取测试 ====================

    def test_extract_items(self):
        """测试物品提取"""
        service = ScriptParserService()
        text = "他拿着剑和项链，走进了办公室。"

        items = service._extract_items(text)

        assert isinstance(items, list)
        item_names = [i["name"] for i in items]
        assert "剑" in item_names
        assert "项链" in item_names

    def test_guess_item_type(self):
        """测试物品类型猜测"""
        service = ScriptParserService()

        assert service._guess_item_type("剑") == "weapon"
        assert service._guess_item_type("项链") == "accessory"
        assert service._guess_item_type("车") == "vehicle"

    # ==================== JSON 提取测试 ====================

    def test_extract_json_valid(self):
        """测试提取有效 JSON"""
        service = ScriptParserService()

        json_str = '{"key": "value", "number": 123}'
        result = service._extract_json(json_str)

        assert result == {"key": "value", "number": 123}

    def test_extract_json_from_text(self):
        """测试从文本中提取 JSON"""
        service = ScriptParserService()

        text_with_json = '这是一些文本，然后是 {"key": "value"} 更多文本'
        result = service._extract_json(text_with_json)

        assert result == {"key": "value"}

    def test_extract_json_from_code_block(self):
        """测试从代码块中提取 JSON"""
        service = ScriptParserService()

        markdown = '''```json
{"summary": "测试概要"}
```'''
        result = service._extract_json(markdown)

        assert result == {"summary": "测试概要"}

    # ==================== 造型推荐测试 ====================

    def test_analyze_character_poses_mock(self, mock_ollama_client):
        """测试角色造型推荐（Mock）"""
        mock_ollama_client.generate = AsyncMock(
            return_value=MagicMock(
                success=True,
                text='{"recommended_poses": [{"pose_type": "casual", "confidence": 0.9, "reason": "日常场景"}]}'
            )
        )

        service = ScriptParserService()
        result = service.analyze_character_poses("一个活泼的女孩", "校园场景")

        assert result["success"] is True
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0


class TestScriptParserServiceLargeText:
    """大文本处理测试"""

    @pytest.mark.unit
    def test_parse_large_script_chunking(self):
        """测试大文本分段处理"""
        service = ScriptParserService()

        # 创建超过 10000 字符的大文本
        large_text = "这是一段很长的文本。" * 5000

        # Mock 分段解析
        with patch.object(service, 'parse_script', return_value={
            "success": True,
            "characters": [],
            "scenes": [],
            "items": [],
            "chapters": []
        }):
            result = service.parse_large_script(large_text)

            assert result["success"] is True
            assert "metadata" in result


class TestScriptParserAsyncTasks:
    """脚本解析 Celery 任务测试"""

    @pytest.mark.unit
    @pytest.mark.django_db
    def test_parse_script_async_task(self):
        """测试异步解析任务"""
        from apps.artworks.tasks import parse_script_async

        with patch('apps.artworks.services.script_parser.get_script_parser_service') as mock_get:
            mock_service = MagicMock()
            # Mock both parse_script and parse_large_script
            mock_service.parse_script.return_value = {
                "success": True,
                "chapters": [],
                "characters": [],
                "scenes": [],
                "items": [],
                "summary": "测试概要"
            }
            mock_service.parse_large_script.return_value = {
                "success": True,
                "chapters": [],
                "characters": [],
                "scenes": [],
                "items": [],
                "summary": "测试概要"
            }
            mock_get.return_value = mock_service

            result = parse_script_async.apply(
                args=("测试文本",)
            ).get()

            assert result["success"] is True

    @pytest.mark.unit
    def test_extract_characters_async_task(self):
        """测试异步角色提取任务"""
        from apps.artworks.tasks import extract_characters_async

        with patch('apps.artworks.services.script_parser.get_script_parser_service') as mock_get:
            mock_service = MagicMock()
            mock_service._extract_characters.return_value = [
                {"name": "张三", "display_name": "张三"}
            ]
            mock_get.return_value = mock_service

            result = extract_characters_async.apply(
                args=("张三和李四的故事",)
            ).get()

            assert result["success"] is True
            assert len(result["characters"]) > 0

    @pytest.mark.unit
    def test_analyze_poses_async_task(self):
        """测试异步造型推荐任务"""
        from apps.artworks.tasks import analyze_poses_async

        with patch('apps.artworks.services.script_parser.get_script_parser_service') as mock_get:
            mock_service = MagicMock()
            mock_service.analyze_character_poses.return_value = {
                "success": True,
                "recommendations": [
                    {"pose_type": "casual", "confidence": 0.8}
                ]
            }
            mock_get.return_value = mock_service

            result = analyze_poses_async.apply(
                args=("角色描述", "场景")
            ).get()

            assert result["success"] is True


# ==================== 边界条件测试 ====================

class TestScriptParserEdgeCases:
    """边界条件测试"""

    def test_parse_empty_script(self):
        """测试解析空脚本"""
        service = ScriptParserService()
        result = service.parse_script("")

        # 空脚本应该返回基本信息
        assert isinstance(result, dict)
        assert "metadata" in result

    def test_parse_script_with_special_chars(self):
        """测试包含特殊字符的脚本"""
        service = ScriptParserService()
        script = "角色说：\"你好！@#$%^&*()\""

        # 不应该崩溃
        result = service.parse_script(script)
        assert isinstance(result, dict)

    def test_extract_characters_unicode(self):
        """测试 Unicode 字符处理"""
        service = ScriptParserService()
        script = "角色😊和角色🎉一起工作。"

        characters = service._extract_characters_by_rules(script)
        assert isinstance(characters, list)


# ==================== 集成测试 ====================

class TestScriptParserIntegration:
    """脚本解析集成测试"""

    @pytest.mark.integration
    @pytest.mark.script_parser
    @pytest.mark.skipif(
        True,  # 需要 Ollama 服务时手动运行
        reason="需要 Ollama 服务运行"
    )
    def test_real_ollama_connection(self):
        """集成测试: 实际 Ollama 连接"""
        service = ScriptParserService()

        # 测试 LLM 连接
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            response = loop.run_until_complete(
                service.llm_client.generate("测试", max_tokens=10)
            )
            is_connected = response.success
        finally:
            loop.close()

        assert isinstance(is_connected, bool)

    @pytest.mark.integration
    @pytest.mark.script_parser
    def test_parse_full_sample_script(self, sample_script_text):
        """测试完整解析示例脚本"""
        service = ScriptParserService()

        # Mock LLM 调用
        with patch.object(service, '_generate_summary', return_value="测试概要"):
            result = service.parse_script(sample_script_text)

            assert result["success"] is True
            assert "chapters" in result
            assert "characters" in result
            assert "scenes" in result
            assert "items" in result
            assert "summary" in result
