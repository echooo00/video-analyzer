"""综合总结生成 — 组合帧描述 + 字幕 → LLM 生成结构化总结."""
import json
import time
from dataclasses import dataclass

from openai import OpenAI

from video_analyzer.config import (
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    API_RETRY_ATTEMPTS,
    API_RETRY_BACKOFF_SEC,
    MAX_TRANSCRIPT_TOKENS,
)
from video_analyzer.ai.prompts import SUMMARY_SYSTEM, SUMMARY_USER
from video_analyzer.ai.frame_analyzer import FrameAnalysis
from video_analyzer.ai.transcriber import TranscriptSegment


@dataclass
class KeyPoint:
    timestamp: str
    point: str
    importance: str


@dataclass
class VideoSummary:
    title: str
    duration_summary: str
    key_points: list[KeyPoint]
    topics: list[str]
    full_summary_cn: str
    suggested_tags: list[str]
    action_items: list[str]


def summarize(
    frame_analyses: list[FrameAnalysis],
    transcript: list[TranscriptSegment],
    duration: float,
    width: int,
    height: int,
) -> VideoSummary:
    """综合帧分析和字幕生成最终总结."""
    if not LLM_API_KEY:
        raise RuntimeError("未配置 LLM_API_KEY，请在 .env 中设置 DeepSeek API Key")

    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    # 构建帧描述文本
    frame_desc_lines = []
    for fa in frame_analyses:
        scene_label = f"[{fa.timestamp:.0f}s 场景{fa.scene_id}]"
        frame_desc_lines.append(
            f"{scene_label} ({fa.scene_type})\n  {fa.description_cn}"
        )
    frame_desc_text = "\n".join(frame_desc_lines)

    # 构建字幕文本（限制 token 数）
    transcript_lines = []
    char_count = 0
    for seg in transcript:
        line = f"[{seg.start:.0f}-{seg.end:.0f}s] {seg.text}"
        char_count += len(line)
        # 粗略估计：中文 1 字符 ≈ 1 token，英文 4 字符 ≈ 1 token
        if char_count > MAX_TRANSCRIPT_TOKENS * 2:
            transcript_lines.append("... (后续内容已截断)")
            break
        transcript_lines.append(line)
    transcript_text = "\n".join(transcript_lines) if transcript_lines else "（无语音内容）"

    user_prompt = SUMMARY_USER.format(
        duration=duration,
        duration_min=duration / 60,
        width=width,
        height=height,
        frame_count=len(frame_analyses),
        frame_descriptions=frame_desc_text,
        transcript=transcript_text,
    )

    for attempt in range(API_RETRY_ATTEMPTS):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
                max_tokens=2000,
            )
            content = response.choices[0].message.content
            return _parse_summary_response(content)

        except Exception as e:
            if attempt < API_RETRY_ATTEMPTS - 1:
                wait = API_RETRY_BACKOFF_SEC * (2 ** attempt)
                print(f"  [总结] API 错误 (尝试 {attempt+1}/{API_RETRY_ATTEMPTS}): {e}，{wait}s 后重试")
                time.sleep(wait)
            else:
                raise RuntimeError(f"总结生成失败: {e}")


def _parse_summary_response(content: str) -> VideoSummary:
    """解析 LLM 返回的 JSON 总结 — 兼容中英文 JSON key."""
    try:
        obj = json.loads(content)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{[\s\S]*\}', content)
        obj = json.loads(match.group(0)) if match else {}

    # 兼容中英文 key
    title = obj.get("title") or obj.get("视频标题建议", "未命名视频")
    duration_summary = obj.get("duration_summary") or obj.get("视频时长摘要", "")
    topics = obj.get("topics") or obj.get("话题分类", [])
    full_summary_cn = obj.get("full_summary_cn") or obj.get("完整总结", "")
    suggested_tags = obj.get("suggested_tags") or obj.get("建议标签", [])
    action_items = obj.get("action_items") or obj.get("后续行动项", [])

    # 关键要点列表 — 兼容中英文 key
    raw_points = obj.get("key_points") or obj.get("关键要点列表", [])
    key_points = []
    for kp in raw_points:
        key_points.append(KeyPoint(
            timestamp=str(kp.get("timestamp") or kp.get("时间戳", "")),
            point=kp.get("point") or kp.get("要点", ""),
            importance=kp.get("importance") or kp.get("重要性", "medium"),
        ))

    return VideoSummary(
        title=title,
        duration_summary=duration_summary,
        key_points=key_points,
        topics=topics,
        full_summary_cn=full_summary_cn or content[:500],
        suggested_tags=suggested_tags,
        action_items=action_items,
    )
