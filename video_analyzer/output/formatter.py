"""格式化输出 — 将 VideoSummary 渲染为 Markdown / JSON / TXT."""
import json
from datetime import timedelta

from video_analyzer.ai.summarizer import VideoSummary
from video_analyzer.ai.frame_analyzer import FrameAnalysis
from video_analyzer.ai.transcriber import TranscriptSegment


def _fmt_timestamp(seconds: float) -> str:
    td = timedelta(seconds=int(seconds))
    return str(td)


def to_markdown(
    summary: VideoSummary,
    frame_analyses: list[FrameAnalysis] | None = None,
    transcript: list[TranscriptSegment] | None = None,
) -> str:
    """生成 Markdown 格式报告."""
    lines = [
        f"# {summary.title}",
        f"",
        f"**{summary.duration_summary}**",
        f"",
    ]

    if summary.topics:
        tags = " | ".join(f"`{t}`" for t in summary.topics)
        lines.append(f"**话题分类**：{tags}")
        lines.append("")

    # 关键要点
    lines.append("## 关键要点")
    lines.append("")
    if summary.key_points:
        for kp in summary.key_points:
            imp_icon = {"high": "⭐", "medium": "●", "low": "○"}.get(kp.importance, "●")
            lines.append(f"- {imp_icon} **[{kp.timestamp}]** {kp.point}")
    lines.append("")

    # 完整总结
    lines.append("## 完整总结")
    lines.append("")
    lines.append(summary.full_summary_cn)
    lines.append("")

    # 画面分析
    if frame_analyses:
        lines.append("## 关键帧画面")
        lines.append("")
        for fa in frame_analyses:
            ts = _fmt_timestamp(fa.timestamp)
            lines.append(f"### 场景 {fa.scene_id} — {ts}")
            lines.append(f"- 类型：{fa.scene_type}")
            lines.append(f"- 内容：{fa.description_cn}")
            if fa.text_on_screen:
                lines.append(f"- 画面文字：{fa.text_on_screen}")
            lines.append("")

    # 语音转文字
    if transcript:
        lines.append("## 语音转文字")
        lines.append("")
        for seg in transcript:
            ts = f"{_fmt_timestamp(seg.start)} — {_fmt_timestamp(seg.end)}"
            lines.append(f"- **[{ts}]** {seg.text}")
        lines.append("")

    # 标签 & 后续行动
    if summary.suggested_tags:
        lines.append("## 建议标签")
        lines.append("")
        lines.append(" ".join(f"`{t}`" for t in summary.suggested_tags))
        lines.append("")

    if summary.action_items:
        lines.append("## 后续行动项")
        lines.append("")
        for item in summary.action_items:
            lines.append(f"- [ ] {item}")
        lines.append("")

    return "\n".join(lines)


def to_json(
    summary: VideoSummary,
    frame_analyses: list[FrameAnalysis] | None = None,
    transcript: list[TranscriptSegment] | None = None,
) -> str:
    """生成 JSON 格式."""
    result = {
        "title": summary.title,
        "duration_summary": summary.duration_summary,
        "key_points": [
            {"timestamp": kp.timestamp, "point": kp.point, "importance": kp.importance}
            for kp in summary.key_points
        ],
        "topics": summary.topics,
        "full_summary_cn": summary.full_summary_cn,
        "suggested_tags": summary.suggested_tags,
        "action_items": summary.action_items,
    }
    if frame_analyses:
        result["frame_analyses"] = [
            {
                "scene_id": fa.scene_id,
                "timestamp": fa.timestamp,
                "scene_type": fa.scene_type,
                "description_cn": fa.description_cn,
                "text_on_screen": fa.text_on_screen,
            }
            for fa in frame_analyses
        ]
    if transcript:
        result["transcript"] = [
            {"start": s.start, "end": s.end, "text": s.text}
            for s in transcript
        ]
    return json.dumps(result, ensure_ascii=False, indent=2)


def to_txt(summary: VideoSummary) -> str:
    """生成纯文本格式."""
    lines = [
        f"标题：{summary.title}",
        f"摘要：{summary.duration_summary}",
        f"话题：{' / '.join(summary.topics)}" if summary.topics else "",
        "",
        "关键要点：",
    ]
    for kp in summary.key_points:
        lines.append(f"  [{kp.timestamp}] {kp.point}")
    lines.append("")
    lines.append(f"完整总结：\n{summary.full_summary_cn}")
    if summary.action_items:
        lines.append("")
        lines.append("后续行动：")
        for item in summary.action_items:
            lines.append(f"  - {item}")
    return "\n".join(lines)
