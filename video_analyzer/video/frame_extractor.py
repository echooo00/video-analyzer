"""关键帧提取 + 感知哈希去重."""
import hashlib
from dataclasses import dataclass
from pathlib import Path

import cv2
import imagehash
from PIL import Image

from video_analyzer.config import (
    KEYFRAME_MAX_WIDTH,
    KEYFRAME_JPEG_QUALITY,
    PERCEPTUAL_HASH_THRESHOLD,
    MAX_KEYFRAMES,
)
from video_analyzer.video.scene_detector import Scene


@dataclass
class Keyframe:
    path: str              # 图片文件路径
    timestamp: float       # 视频时间秒
    scene_id: int
    phash: str             # 感知哈希 hex


def extract_keyframes(
    video_path: str,
    scenes: list[Scene],
    output_dir: str,
) -> list[Keyframe]:
    """从每个场景提取关键帧，去重后保存到 output_dir."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频: {video_path}")

    keyframes: list[Keyframe] = []
    seen_hashes: set[str] = set()

    # 限制最大帧数
    if len(scenes) > MAX_KEYFRAMES:
        step = len(scenes) / MAX_KEYFRAMES
        sampled = [scenes[int(i * step)] for i in range(MAX_KEYFRAMES)]
    else:
        sampled = scenes

    for scene in sampled:
        cap.set(cv2.CAP_PROP_POS_MSEC, scene.keyframe_sec * 1000)
        ret, frame = cap.read()
        if not ret:
            continue

        # 转为 PIL Image 计算感知哈希
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        phash = str(imagehash.phash(pil_img))

        # 去重
        is_unique = True
        for prev_hash in seen_hashes:
            diff = _hamming_distance_hex(phash, prev_hash)
            if diff < PERCEPTUAL_HASH_THRESHOLD:
                is_unique = False
                break

        if not is_unique:
            continue

        seen_hashes.add(phash)

        # 压缩并保存
        h, w = frame.shape[:2]
        if w > KEYFRAME_MAX_WIDTH:
            ratio = KEYFRAME_MAX_WIDTH / w
            new_size = (KEYFRAME_MAX_WIDTH, int(h * ratio))
            frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)

        filename = f"scene_{scene.scene_id:04d}_{scene.keyframe_sec:.1f}s.jpg"
        save_path = out / filename
        cv2.imwrite(str(save_path), frame, [cv2.IMWRITE_JPEG_QUALITY, KEYFRAME_JPEG_QUALITY])

        keyframes.append(Keyframe(
            path=str(save_path),
            timestamp=scene.keyframe_sec,
            scene_id=scene.scene_id,
            phash=phash,
        ))

    cap.release()
    return keyframes


def _hamming_distance_hex(h1: str, h2: str) -> int:
    """计算两个十六进制字符串表示的哈希的汉明距离."""
    b1 = int(h1, 16)
    b2 = int(h2, 16)
    xor = b1 ^ b2
    return xor.bit_count()
