"""语音转文字 — whisper / faster-whisper / DashScope API."""
import os
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from video_analyzer.config import (
    TRANSCRIPTION_BACKEND,
    WHISPER_MODEL_SIZE,
    WHISPER_LANGUAGE,
    MODEL_CACHE_DIR,
    ASR_API_KEY,
)


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    confidence: float


def transcribe(audio_path: str) -> list[TranscriptSegment]:
    """转写音频，返回带时间戳的文本段列表."""
    if TRANSCRIPTION_BACKEND in ("local", "whisper"):
        return _transcribe_whisper(audio_path)
    elif TRANSCRIPTION_BACKEND == "faster":
        return _transcribe_faster(audio_path)
    elif TRANSCRIPTION_BACKEND == "dashscope":
        return _transcribe_dashscope(audio_path)
    else:
        raise ValueError(f"不支持的转写后端: {TRANSCRIPTION_BACKEND}")


def _transcribe_whisper(audio_path: str) -> list[TranscriptSegment]:
    """使用 openai-whisper 本地转写 (PyTorch 后端, 兼容性好)."""
    import whisper

    print(f"  [语音转写] 加载 whisper 模型 ({WHISPER_MODEL_SIZE})...")
    model = whisper.load_model(WHISPER_MODEL_SIZE)
    print(f"    ↳ 开始转写...")

    result = model.transcribe(
        audio_path,
        language=WHISPER_LANGUAGE,
        verbose=False,
        fp16=False,  # CPU 上用 FP32
    )

    results = []
    for seg in result.get("segments", []):
        results.append(TranscriptSegment(
            start=round(seg["start"], 2),
            end=round(seg["end"], 2),
            text=seg["text"].strip(),
            confidence=round(seg.get("confidence", seg.get("avg_logprob", 0)), 3),
        ))

    print(f"    ↳ 完成，共 {len(results)} 个文本段")
    return results


def _transcribe_faster(audio_path: str) -> list[TranscriptSegment]:
    """使用 faster-whisper 本地转写 (CTranslate2 后端, 速度快但兼容性差)."""
    print(f"  [语音转写] 加载 faster-whisper 模型 ({WHISPER_MODEL_SIZE})...")

    from faster_whisper import WhisperModel

    model_dir = str(Path(MODEL_CACHE_DIR) / "faster_whisper")
    Path(model_dir).mkdir(parents=True, exist_ok=True)

    model = WhisperModel(
        WHISPER_MODEL_SIZE,
        device="cpu",
        compute_type="int8",
        download_root=model_dir,
    )

    segments, info = model.transcribe(
        audio_path,
        language=WHISPER_LANGUAGE,
        beam_size=3,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )
    print(f"    ↳ 检测语言: {info.language} (概率 {info.language_probability:.2f})")

    results = []
    for seg in segments:
        results.append(TranscriptSegment(
            start=round(seg.start, 2),
            end=round(seg.end, 2),
            text=seg.text.strip(),
            confidence=round(seg.avg_logprob, 3),
        ))

    print(f"    ↳ 完成，共 {len(results)} 个文本段")
    return results


def _transcribe_dashscope(audio_path: str) -> list[TranscriptSegment]:
    """使用阿里百炼 DashScope ASR API 转写."""
    import json
    import requests

    if not ASR_API_KEY:
        raise RuntimeError("使用 DashScope ASR 需要设置 ASR_API_KEY")

    print(f"  [语音转写] 使用 DashScope ASR API...")

    from video_analyzer.utils.cache import image_key

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    audio_hash = image_key(audio_data)

    from video_analyzer.utils.cache import get as cache_get, set_cache as cache_set
    cached = cache_get("asr", audio_hash)
    if cached:
        print(f"    ↳ 缓存命中")
        return [TranscriptSegment(**s) for s in cached]

    url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
    headers = {"Authorization": f"Bearer {ASR_API_KEY}"}

    files = {"audio": (Path(audio_path).name, audio_data, "audio/wav")}
    data = {
        "model": "paraformer-v2",
        "parameters": json.dumps({"language_hints": ["zh", "en"]}),
    }
    response = requests.post(url, headers=headers, files=files, data=data, timeout=300)

    if response.status_code != 200:
        raise RuntimeError(f"DashScope ASR 失败: {response.status_code} {response.text}")

    result = response.json()
    segments = []
    for item in result.get("results", []):
        for sentence in item.get("sentences", []):
            segments.append({
                "start": sentence.get("begin_time", 0) / 1000,
                "end": sentence.get("end_time", 0) / 1000,
                "text": sentence.get("text", ""),
                "confidence": 1.0,
            })

    cache_set("asr", segments, audio_hash)
    print(f"    ↳ 完成，共 {len(segments)} 个文本段")
    return [TranscriptSegment(**s) for s in segments]
