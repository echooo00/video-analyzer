"""音频轨提取 — FFmpeg 提取为 16kHz mono WAV."""
from pathlib import Path

from video_analyzer.utils.ffmpeg import run_ffmpeg


def extract_audio(video_path: str, output_dir: str) -> str | None:
    """提取音频为 16kHz mono WAV，返回输出路径；无音轨返回 None."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    audio_path = out_dir / f"{Path(video_path).stem}_audio.wav"

    result = run_ffmpeg([
        "-i", video_path,
        "-vn",                        # 不要视频
        "-acodec", "pcm_s16le",       # PCM 16-bit
        "-ar", "16000",               # 16kHz 采样率
        "-ac", "1",                   # 单声道
        str(audio_path),
    ])

    if result.returncode != 0:
        # 可能没有音轨
        if "Stream specifier" in result.stderr or "does not contain" in result.stderr:
            return None
        raise RuntimeError(f"音频提取失败: {result.stderr}")

    return str(audio_path) if audio_path.exists() else None
