"""全局配置 — 所有模块统一从此处读取配置."""
import os
from pathlib import Path
from dotenv import load_dotenv

# 按优先级查找 .env: 当前目录 > 用户目录 > 包目录
_load_order = [
    Path.cwd() / ".env",
    Path.home() / ".video_analyzer" / ".env",
    Path(__file__).resolve().parent / ".env",
]
for _p in _load_order:
    if _p.exists():
        load_dotenv(_p)
        break
else:
    load_dotenv()  # 兜底

# ── 项目路径 ──────────────────────────────────────
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
MODEL_CACHE_DIR = Path(os.getenv("MODEL_CACHE_DIR", str(Path.home() / ".video_analyzer" / "models")))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(Path.cwd() / "output")))
CACHE_DIR = Path(os.getenv("CACHE_DIR", str(Path.home() / ".video_analyzer_cache")))
CACHE_DIR.mkdir(parents=True, exist_ok=True)
MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 确保用户配置目录存在
_user_config_dir = Path.home() / ".video_analyzer"
_user_config_dir.mkdir(parents=True, exist_ok=True)

# ── FFmpeg ────────────────────────────────────────
FFMPEG_PATH = os.getenv(
    "FFMPEG_PATH",
    r"D:\Tecplot\Tecplot 360 EX 2022 R1\bin\ffmpeg.exe",
)
FFPROBE_PATH = os.getenv(
    "FFPROBE_PATH",
    r"D:\Tecplot\Tecplot 360 EX 2022 R1\bin\ffprobe.exe",
)

# ── 场景检测 ──────────────────────────────────────
SCENE_DETECTION_FPS = 1.0
SCENE_THRESHOLD_SSIM = float(os.getenv("SCENE_THRESHOLD_SSIM", "0.5"))
KEYFRAME_MAX_WIDTH = 1024
KEYFRAME_JPEG_QUALITY = 85
MIN_SCENE_DURATION_SEC = 2.0
PERCEPTUAL_HASH_THRESHOLD = 10

# ── 关键帧限制 ────────────────────────────────────
MAX_KEYFRAMES = int(os.getenv("MAX_KEYFRAMES", "60"))

# ── 音频 / 语音转写 ──────────────────────────────
TRANSCRIPTION_BACKEND = os.getenv("TRANSCRIPTION_BACKEND", "local")
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "medium")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "zh")
AUDIO_CHUNK_SECONDS = 60

# ── VLM API (画面分析) ────────────────────────────
VLM_API_KEY = os.getenv("VLM_API_KEY", "")
VLM_BASE_URL = os.getenv(
    "VLM_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)
VLM_MODEL = os.getenv("VLM_MODEL", "qwen-vl-max")

# ── LLM API (文本总结) ────────────────────────────
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# ── ASR API (备选语音转写) ────────────────────────
ASR_API_KEY = os.getenv("ASR_API_KEY", "")

# ── API 调用控制 ──────────────────────────────────
MAX_CONCURRENT_API_CALLS = int(os.getenv("MAX_CONCURRENT_API_CALLS", "3"))
API_RETRY_ATTEMPTS = 3
API_RETRY_BACKOFF_SEC = 2.0
MAX_TRANSCRIPT_TOKENS = 32000
