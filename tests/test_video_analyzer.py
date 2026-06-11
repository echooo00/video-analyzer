import pytest
import sys
from pathlib import Path

# 确保 video_analyzer 可导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestConfig:
    def test_config_imports(self):
        """验证配置模块可以正常加载."""
        from video_analyzer.config import (
            TRANSCRIPTION_BACKEND,
            WHISPER_MODEL_SIZE,
            WHISPER_LANGUAGE,
            VLM_MODEL,
            LLM_MODEL,
            CACHE_DIR,
            API_RETRY_ATTEMPTS,
        )
        assert TRANSCRIPTION_BACKEND in ("local", "whisper", "faster", "dashscope")
        assert WHISPER_MODEL_SIZE in ("tiny", "base", "small", "medium", "large")
        assert WHISPER_LANGUAGE == "zh"
        assert VLM_MODEL == "qwen-vl-max"
        assert LLM_MODEL == "deepseek-chat"
        assert CACHE_DIR.exists()
        assert API_RETRY_ATTEMPTS > 0


class TestCache:
    def test_cache_key_deterministic(self):
        """验证缓存 key 是幂等的."""
        from video_analyzer.utils.cache import _cache_key
        k1 = _cache_key("test", "hello", "world")
        k2 = _cache_key("test", "hello", "world")
        assert k1 == k2
        assert len(k1) == 32  # SHA256 truncated to 16 bytes hex

    def test_image_key(self):
        """验证图片 hash 计算."""
        from video_analyzer.utils.cache import image_key
        data = b"fake_image_bytes"
        key = image_key(data)
        assert len(key) == 16
        assert key == image_key(data)  # 幂等


class TestFrameAnalysisParse:
    def test_parse_chinese_keys(self):
        """验证中英文 JSON key 都能解析."""
        from video_analyzer.ai.frame_analyzer import _parse_frame_response
        import json

        # 中文 key
        cn = json.dumps({
            "画面类型": "户外",
            "主要物体": ["树", "建筑"],
            "文字": "标题",
            "动作或事件": "有人在走路",
            "是否关键时刻": "是",
        })
        result = _parse_frame_response(cn)
        assert result["scene_type"] == "户外"
        assert result["objects"] == ["树", "建筑"]
        assert result["text_on_screen"] == "标题"
        assert result["action"] == "有人在走路"
        assert result["is_key_moment"] is True

    def test_parse_english_keys(self):
        """验证英文 JSON key 解析."""
        from video_analyzer.ai.frame_analyzer import _parse_frame_response
        import json

        en = json.dumps({
            "scene_type": "indoor",
            "objects": ["desk", "laptop"],
            "text_on_screen": "PPT",
            "action": "talking",
            "is_key_moment": False,
            "description_cn": "一个人在房间里讲话",
        })
        result = _parse_frame_response(en)
        assert result["scene_type"] == "indoor"
        assert len(result["objects"]) == 2
        assert result["description_cn"] == "一个人在房间里讲话"


class TestSummaryParse:
    def test_parse_chinese_keys(self):
        """验证总结中英文 key 兼容."""
        from video_analyzer.ai.summarizer import _parse_summary_response
        import json

        cn = json.dumps({
            "视频标题建议": "测试",
            "视频时长摘要": "5分钟",
            "关键要点列表": [
                {"时间戳": "10s", "要点": "关键点1", "重要性": "high"}
            ],
            "话题分类": ["科技"],
            "完整总结": "这是一个测试",
            "建议标签": ["测试"],
        })
        result = _parse_summary_response(cn)
        assert result.title == "测试"
        assert result.duration_summary == "5分钟"
        assert len(result.key_points) == 1
        assert result.key_points[0].point == "关键点1"
        assert "科技" in result.topics
        assert result.full_summary_cn == "这是一个测试"
