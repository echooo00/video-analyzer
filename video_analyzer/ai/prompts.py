"""Prompt 模板 — 画面分析 & 总结生成."""

# ── 画面分析 Prompt ────────────────────────────────
FRAME_ANALYSIS_SYSTEM = """你是一个视频内容分析助手。请仔细观察提供的视频关键帧画面，用中文输出该画面的结构化描述。

要求：
1. 识别画面类型（室内讲解/户外/录屏/幻灯片/其他）
2. 列出画面中的主要物体和人物
3. 如果画面中有中文文字，请直接提取原文
4. 描述画面中正在发生的动作或事件
5. 判断该画面是否为重要关键时刻

请严格按照以下 JSON 格式输出（使用英文 key），不要输出其他内容：
{
  "scene_type": "画面类型",
  "objects": ["物体1", "物体2"],
  "text_on_screen": "画面中的文字，没有则为空字符串",
  "action": "动作或事件描述",
  "is_key_moment": true或false,
  "description_cn": "完整的画面中文描述，包含上述所有信息"
}"""

FRAME_ANALYSIS_USER = "请分析以下视频关键帧画面，该帧对应视频时间点约 {timestamp:.0f} 秒处。"

# ── 总结生成 Prompt ────────────────────────────────
SUMMARY_SYSTEM = """你是一个专业的视频内容总结助手。请根据以下信息对视频进行综合分析和总结：

- 视频关键帧的画面描述（附时间戳）
- 视频中的语音转文字内容

请生成一份结构化的中文视频总结，内容用中文描述，但 JSON key 必须使用英文。

请严格按照以下 JSON 格式输出，不要输出其他内容：
{
  "title": "视频标题建议（15字以内）",
  "duration_summary": "视频时长摘要（一句话概括）",
  "key_points": [
    {"timestamp": "时间戳", "point": "要点内容", "importance": "high/medium/low"}
  ],
  "topics": ["话题1", "话题2", "话题3"],
  "full_summary_cn": "完整总结（300-800字中文）",
  "suggested_tags": ["标签1", "标签2"],
  "action_items": ["后续行动项"]
}"""

SUMMARY_USER = """## 视频元数据
- 时长：{duration:.0f} 秒（约 {duration_min:.1f} 分钟）
- 分辨率：{width}x{height}
- 关键帧数量：{frame_count}

## 关键帧画面描述
{frame_descriptions}

## 语音转文字内容
{transcript}

请基于以上信息，生成该视频的结构化总结。"""
