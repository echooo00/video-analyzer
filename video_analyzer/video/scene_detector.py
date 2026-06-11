"""基于 OpenCV 直方图比较的场景分割（纯 OpenCV，无需 scikit-image）."""
from dataclasses import dataclass

import cv2
import numpy as np

from video_analyzer.config import (
    SCENE_DETECTION_FPS,
    SCENE_THRESHOLD_SSIM,
    MIN_SCENE_DURATION_SEC,
)


@dataclass
class Scene:
    scene_id: int
    start_sec: float
    end_sec: float
    keyframe_sec: float   # 该场景中间时刻，用于提取关键帧


def _compute_hist_similarity(prev_gray, curr_gray) -> float:
    """计算两帧之间的直方图相似度（HSV Hue + 梯度直方图）."""
    # 方法1: HSV 色调直方图，对光照变化不敏感
    h, w = prev_gray.shape[:2]
    # 缩小到 256x256 以加速
    small_prev = cv2.resize(prev_gray, (256, 256))
    small_curr = cv2.resize(curr_gray, (256, 256))

    hist_prev = cv2.calcHist([small_prev], [0], None, [64], [0, 256])
    hist_curr = cv2.calcHist([small_curr], [0], None, [64], [0, 256])
    cv2.normalize(hist_prev, hist_prev, 0, 1, cv2.NORM_MINMAX)
    cv2.normalize(hist_curr, hist_curr, 0, 1, cv2.NORM_MINMAX)

    hist_corr = cv2.compareHist(hist_prev, hist_curr, cv2.HISTCMP_CORREL)

    # 方法2: 像素差值均值（检测大幅变化）
    diff = cv2.absdiff(small_prev, small_curr)
    diff_ratio = np.mean(diff) / 255.0

    # 组合评分：直方图相关性高 + 像素差小 → 相似度高
    similarity = hist_corr * (1.0 - diff_ratio)
    return similarity


def detect_scenes(video_path: str, duration: float) -> list[Scene]:
    """检测视频中的场景切换，返回场景列表."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频: {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    sample_interval = max(1, int(video_fps / SCENE_DETECTION_FPS))

    prev_gray = None
    scene_boundaries = [0.0]
    current_sec = 0.0
    frame_idx = 0

    # 动态阈值：前 N 帧的相似度统计用于校准
    recent_similarities: list[float] = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current_sec = frame_idx / video_fps

        if frame_idx % sample_interval == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_gray is not None:
                sim = _compute_hist_similarity(prev_gray, gray)
                recent_similarities.append(sim)
                if len(recent_similarities) > 30:
                    recent_similarities.pop(0)

                # 使用动态阈值：历史均值的 1.5 个标准差以下视为切换
                if len(recent_similarities) >= 5:
                    mean_sim = np.mean(recent_similarities)
                    std_sim = np.std(recent_similarities)
                    threshold = max(0.3, mean_sim - 1.5 * std_sim)
                else:
                    threshold = SCENE_THRESHOLD_SSIM

                if sim < threshold:
                    scene_boundaries.append(current_sec)

            prev_gray = gray

        frame_idx += 1

    cap.release()

    if len(scene_boundaries) == 0:
        scene_boundaries = [0.0]

    scene_boundaries.append(duration)

    # 合并过短的场景
    merged = _merge_short_scenes(scene_boundaries, MIN_SCENE_DURATION_SEC)

    # 生成 Scene 对象
    scenes = []
    for i in range(len(merged) - 1):
        start = merged[i]
        end = merged[i + 1]
        mid = (start + end) / 2
        scenes.append(Scene(
            scene_id=i,
            start_sec=round(start, 2),
            end_sec=round(end, 2),
            keyframe_sec=round(mid, 2),
        ))

    return scenes


def _merge_short_scenes(boundaries: list[float], min_duration: float) -> list[float]:
    """合并时长过短的场景."""
    if len(boundaries) <= 2:
        return boundaries

    merged = [boundaries[0]]
    i = 1
    while i < len(boundaries) - 1:
        dur = boundaries[i] - merged[-1]
        if dur < min_duration:
            pass  # 跳过此边界，与下一段合并
        else:
            merged.append(boundaries[i])
        i += 1
    merged.append(boundaries[-1])
    return merged
