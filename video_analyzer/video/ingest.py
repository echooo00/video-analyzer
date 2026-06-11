"""视频元数据提取 — 通过 ffmpeg stderr 解析 + OpenCV 补充."""
import os
from dataclasses import dataclass

from video_analyzer.utils.ffmpeg import probe_streams


@dataclass
class VideoMeta:
    file_path: str
    duration: float       # 秒
    fps: float
    width: int
    height: int
    codec: str
    has_audio: bool
    file_size_mb: float


def ingest(file_path: str) -> VideoMeta:
    """提取视频元数据."""
    probe = probe_streams(file_path)

    video_stream = None
    for s in probe["streams"]:
        if s.get("codec_type") == "video":
            video_stream = s
            break

    if video_stream is None:
        raise ValueError(f"未找到视频流: {file_path}")

    # 如果 ffmpeg 没解析出 duration，用 OpenCV 补充
    duration = probe.get("duration_sec") or 0.0
    if duration <= 0:
        import cv2
        cap = cv2.VideoCapture(file_path)
        if cap.isOpened():
            fps_cv = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if fps_cv > 0:
                duration = frame_count / fps_cv
            cap.release()

    file_size = os.path.getsize(file_path) / (1024 * 1024)

    return VideoMeta(
        file_path=file_path,
        duration=round(duration, 2),
        fps=round(video_stream.get("fps", 30.0), 2),
        width=video_stream.get("width", 0),
        height=video_stream.get("height", 0),
        codec=video_stream.get("codec_name", "unknown"),
        has_audio=probe.get("has_audio", False),
        file_size_mb=round(file_size, 2),
    )
