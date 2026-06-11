"""API 结果磁盘缓存 — 按 (图片hash + prompt) 缓存，避免重复花钱."""
import hashlib
import json
from pathlib import Path

from video_analyzer.config import CACHE_DIR


def _cache_key(*parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return h[:32]


def get(namespace: str, *key_parts: str) -> dict | None:
    """读取缓存，命中返回 dict，未命中返回 None."""
    key = _cache_key(namespace, *key_parts)
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
    return None


def set_cache(namespace: str, data: dict, *key_parts: str) -> None:
    """写入缓存."""
    key = _cache_key(namespace, *key_parts)
    cache_file = CACHE_DIR / f"{key}.json"
    cache_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def image_key(image_bytes: bytes) -> str:
    """计算图片字节的 SHA256 摘要."""
    return hashlib.sha256(image_bytes).hexdigest()[:16]
