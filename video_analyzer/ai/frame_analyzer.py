"""调用 VLM API 分析关键帧画面."""
import json
import time
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

from video_analyzer.config import (
    VLM_API_KEY,
    VLM_BASE_URL,
    VLM_MODEL,
    API_RETRY_ATTEMPTS,
    API_RETRY_BACKOFF_SEC,
)
from video_analyzer.utils.cache import get as cache_get, set_cache as cache_set, image_key
from video_analyzer.utils.image_utils import load_and_compress
from video_analyzer.ai.prompts import FRAME_ANALYSIS_SYSTEM, FRAME_ANALYSIS_USER


@dataclass
class FrameAnalysis:
    scene_id: int
    timestamp: float
    scene_type: str
    objects: list[str]
    text_on_screen: str
    action: str
    is_key_moment: bool
    description_cn: str


def analyze_frames(
    keyframe_paths: list[tuple[int, float, str]],  # [(scene_id, timestamp, path)]
) -> list[FrameAnalysis]:
    """逐帧提交 VLM API 分析，返回结构化描述列表."""
    if not VLM_API_KEY:
        raise RuntimeError("未配置 VLM_API_KEY，请在 .env 中设置阿里百炼 API Key")

    client = OpenAI(api_key=VLM_API_KEY, base_url=VLM_BASE_URL)
    results: list[FrameAnalysis] = []
    total = len(keyframe_paths)

    for idx, (scene_id, timestamp, path) in enumerate(keyframe_paths):
        print(f"  [画面分析] 第 {idx+1}/{total} 帧 (场景{scene_id}, {timestamp:.0f}s)")

        # 读取并压缩图片
        img_bytes = load_and_compress(path)
        img_hash = image_key(img_bytes)

        # 查缓存
        cached = cache_get("frame", str(scene_id), img_hash)
        if cached:
            results.append(FrameAnalysis(**cached))
            print(f"    ↳ 缓存命中")
            continue

        # 调用 VLM API
        user_prompt = FRAME_ANALYSIS_USER.format(timestamp=timestamp)

        for attempt in range(API_RETRY_ATTEMPTS):
            try:
                response = client.chat.completions.create(
                    model=VLM_MODEL,
                    messages=[
                        {"role": "system", "content": FRAME_ANALYSIS_SYSTEM},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{_bytes_to_b64(img_bytes)}"
                                    },
                                },
                            ],
                        },
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,
                    max_tokens=500,
                )
                content = response.choices[0].message.content
                parsed = _parse_frame_response(content)
                parsed["scene_id"] = scene_id
                parsed["timestamp"] = timestamp

                # 写入缓存
                cache_set("frame", parsed, str(scene_id), img_hash)

                results.append(FrameAnalysis(**parsed))
                break

            except Exception as e:
                if attempt < API_RETRY_ATTEMPTS - 1:
                    wait = API_RETRY_BACKOFF_SEC * (2 ** attempt)
                    print(f"    ↳ API 错误 (尝试 {attempt+1}/{API_RETRY_ATTEMPTS}): {e}，{wait}s 后重试")
                    time.sleep(wait)
                else:
                    # 最终失败，填入占位结果
                    print(f"    ↳ API 最终失败: {e}")
                    results.append(FrameAnalysis(
                        scene_id=scene_id,
                        timestamp=timestamp,
                        scene_type="unknown",
                        objects=[],
                        text_on_screen="",
                        action="API 调用失败",
                        is_key_moment=False,
                        description_cn="[分析失败]",
                    ))

    return results


def _bytes_to_b64(data: bytes) -> str:
    import base64
    return base64.b64encode(data).decode("ascii")


def _parse_frame_response(content: str) -> dict:
    """解析 API 返回的 JSON，含容错处理 — 兼容中英文 JSON key."""
    try:
        obj = json.loads(content)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{[\s\S]*\}', content)
        obj = json.loads(match.group(0)) if match else {}

    # 兼容中英文两种 JSON key
    scene_type = obj.get("scene_type") or obj.get("画面类型", "unknown")
    objects = obj.get("objects") or obj.get("主要物体", [])
    text_on_screen = obj.get("text_on_screen") or obj.get("文字", "")
    action = obj.get("action") or obj.get("动作或事件", "")
    is_key_moment = obj.get("is_key_moment", False)
    if isinstance(is_key_moment, str):
        is_key_moment = is_key_moment in ("是", "true", "True", "yes")
    people = obj.get("人物", "")

    # 取 API 返回的自然语言描述（优先英文 key，再中文 key）
    api_desc = obj.get("description_cn") or obj.get("完整描述", "")
    if api_desc and not api_desc.startswith("{"):
        description_cn = api_desc
    else:
        # 没有自然描述时，从结构化字段拼接
        parts = []
        if scene_type and scene_type != "unknown":
            parts.append(f"[{scene_type}]")
        if objects:
            parts.append("物体: " + "、".join(objects))
        if people and people != "无":
            parts.append(f"人物: {people}")
        if text_on_screen and text_on_screen != "无":
            parts.append(f"文字: {text_on_screen}")
        if action:
            parts.append(action)
        description_cn = "；".join(parts) if parts else content[:200]

    return {
        "scene_type": scene_type,
        "objects": objects if isinstance(objects, list) else [objects],
        "text_on_screen": text_on_screen,
        "action": action,
        "is_key_moment": bool(is_key_moment),
        "description_cn": description_cn,
    }
