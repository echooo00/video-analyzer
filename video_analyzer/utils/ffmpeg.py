"""FFmpeg 查找与命令行调用封装."""
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from video_analyzer.config import FFMPEG_PATH

_FFMPEG_EXE: Optional[str] = None


def _find_exe(name: str, configured_path: str) -> Optional[str]:
    """按优先级查找可执行文件：配置路径 → PATH → 常见路径."""
    if configured_path and Path(configured_path).exists():
        return configured_path
    found = shutil.which(name)
    if found:
        return found
    common_dirs = [
        r"D:\Tecplot\Tecplot 360 EX 2022 R1\bin",
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
    ]
    for d in common_dirs:
        p = Path(d) / f"{name}.exe"
        if p.exists():
            return str(p)
    return None


def get_ffmpeg() -> str:
    """返回 ffmpeg 可执行文件路径，找不到抛 RuntimeError."""
    global _FFMPEG_EXE
    if _FFMPEG_EXE is None:
        _FFMPEG_EXE = _find_exe("ffmpeg", FFMPEG_PATH)
    if _FFMPEG_EXE is None:
        raise RuntimeError(
            "找不到 ffmpeg.exe，请设置环境变量 FFMPEG_PATH 或将 ffmpeg 加入 PATH"
        )
    return _FFMPEG_EXE


def run_ffmpeg(
    args: list[str],
    timeout: int = 600,
    pipe_stderr: bool = False,
) -> subprocess.CompletedProcess:
    """运行 ffmpeg 命令。pipe_stderr=True 时保留 stderr（用于解析元数据）。"""
    loglevel = "info" if pipe_stderr else "error"
    cmd = [get_ffmpeg(), "-hide_banner", "-loglevel", loglevel, "-y"] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def probe_streams(video_path: str) -> dict:
    """使用 ffmpeg 提取视频流信息（替代 ffprobe）。
    解析 ffmpeg stderr 中的 Stream 行和 Duration 行。
    """
    result = run_ffmpeg(["-i", video_path, "-f", "null", "-"], pipe_stderr=True)
    stderr = result.stderr

    info = {"streams": [], "duration_sec": None, "has_audio": False}

    # 解析 Duration: 00:00:30.05, start: 0.000000, bitrate: 1234 kb/s
    dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", stderr)
    if dur_match:
        h, m, s, cs = map(int, dur_match.groups())
        info["duration_sec"] = h * 3600 + m * 60 + s + cs / 100.0

    # 解析 Video stream 行
    #   Stream #0:0[0x1](und): Video: h264 (Main) (avc1 / 0x31637661), yuv420p, 1920x1080, 1379 kb/s, 29.97 fps, 30 tbr, 16k tbn (default)
    video_match = re.search(
        r"Stream #\d+:\d+.*?Video:\s*(\S+).*?,\s*(\d+)x(\d+).*?,\s*([\d.]+)\s*fps",
        stderr,
    )
    if video_match:
        info["streams"].append({
            "codec_type": "video",
            "codec_name": video_match.group(1),
            "width": int(video_match.group(2)),
            "height": int(video_match.group(3)),
            "fps": float(video_match.group(4)),
        })

    # 解析 Audio stream 行
    if re.search(r"Stream #\d+:\d+.*?Audio:", stderr):
        info["has_audio"] = True

    return info
