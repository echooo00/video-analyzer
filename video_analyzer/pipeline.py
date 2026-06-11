"""主编排器 — 串联视频处理、AI分析、格式化输出."""
import json
import time
from pathlib import Path
from typing import Optional

from video_analyzer.video.ingest import ingest, VideoMeta
from video_analyzer.video.scene_detector import detect_scenes
from video_analyzer.video.frame_extractor import extract_keyframes, Keyframe
from video_analyzer.video.audio_extractor import extract_audio
from video_analyzer.ai.frame_analyzer import analyze_frames, FrameAnalysis
from video_analyzer.ai.transcriber import transcribe, TranscriptSegment
from video_analyzer.ai.summarizer import summarize, VideoSummary
from video_analyzer.output.formatter import to_markdown, to_json, to_txt


class Pipeline:
    """视频分析流水线."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        video_path: str,
        output_format: str = "all",
        skip_transcription: bool = False,
        skip_frame_analysis: bool = False,
        dry_run: bool = False,
    ) -> dict[str, str]:
        """
        执行完整的视频分析流水线。

        Args:
            video_path: 视频文件路径
            output_format: 输出格式 ("md", "json", "txt", "all")
            skip_transcription: 跳过语音转写
            skip_frame_analysis: 跳过画面分析（dry-run 时自动跳过）
            dry_run: 仅运行本地处理（场景检测+帧提取+音频提取），不调用 API

        Returns:
            dict with paths of generated output files
        """
        video_stem = Path(video_path).stem
        work_dir = self.output_dir / video_stem
        work_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"视频分析: {video_path}")
        print(f"输出目录: {work_dir}")
        print(f"{'='*60}\n")

        # ── Stage 1: 元数据 ─────────────────────────
        print("[1/5] 提取元数据...")
        t0 = time.time()
        meta = ingest(video_path)
        print(f"  时长: {meta.duration:.0f}s | 分辨率: {meta.width}x{meta.height} "
              f"| FPS: {meta.fps:.1f} | 音频: {'有' if meta.has_audio else '无'}")
        self._save_json(work_dir / "metadata.json", {
            "file_path": meta.file_path,
            "duration": meta.duration,
            "fps": meta.fps,
            "width": meta.width,
            "height": meta.height,
            "codec": meta.codec,
            "has_audio": meta.has_audio,
            "file_size_mb": meta.file_size_mb,
        })

        # ── Stage 2: 场景检测 ────────────────────────
        print("[2/5] 场景检测...")
        scenes = detect_scenes(video_path, meta.duration)
        print(f"  检测到 {len(scenes)} 个场景")
        self._save_json(work_dir / "scenes.json", [
            {"scene_id": s.scene_id, "start_sec": s.start_sec,
             "end_sec": s.end_sec, "keyframe_sec": s.keyframe_sec}
            for s in scenes
        ])

        # ── Stage 3: 帧提取 + 音频提取（可并行） ────
        print("[3/5] 提取关键帧...")
        keyframe_dir = work_dir / "keyframes"
        keyframes = extract_keyframes(video_path, scenes, str(keyframe_dir))
        print(f"  提取了 {len(keyframes)} 个关键帧（去重后）")

        print("  提取音频...")
        audio_path = None
        if meta.has_audio:
            audio_path = extract_audio(video_path, str(work_dir))
            if audio_path:
                size_mb = Path(audio_path).stat().st_size / (1024 * 1024)
                print(f"  音频: {audio_path} ({size_mb:.1f} MB)")

        # ── Stage 4: AI 分析 ─────────────────────────
        frame_analyses: list[FrameAnalysis] = []
        transcript: list[TranscriptSegment] = []

        if dry_run:
            print("[4/5] AI 分析 (dry-run 模式，跳过 API 调用)")
        else:
            print("[4/5] AI 分析...")

            if not skip_frame_analysis and keyframes:
                kf_data = [(kf.scene_id, kf.timestamp, kf.path) for kf in keyframes]
                frame_analyses = analyze_frames(kf_data)
                self._save_json(work_dir / "frame_analysis.json", [
                    {
                        "scene_id": fa.scene_id,
                        "timestamp": fa.timestamp,
                        "scene_type": fa.scene_type,
                        "objects": fa.objects,
                        "text_on_screen": fa.text_on_screen,
                        "action": fa.action,
                        "is_key_moment": fa.is_key_moment,
                        "description_cn": fa.description_cn,
                    }
                    for fa in frame_analyses
                ])

            if not skip_transcription and audio_path:
                transcript = transcribe(audio_path)
                self._save_json(work_dir / "transcript.json", [
                    {"start": s.start, "end": s.end, "text": s.text,
                     "confidence": s.confidence}
                    for s in transcript
                ])

        # ── Stage 5: 总结生成 ────────────────────────
        summary: Optional[VideoSummary] = None
        if not dry_run and (frame_analyses or transcript):
            print("[5/5] 生成总结...")
            summary = summarize(
                frame_analyses=frame_analyses,
                transcript=transcript,
                duration=meta.duration,
                width=meta.width,
                height=meta.height,
            )
        else:
            print("[5/5] 生成总结 (跳过 — 无 AI 分析结果)")

        # ── 输出 ─────────────────────────────────────
        outputs = {}
        if summary:
            if output_format in ("md", "all"):
                md_path = work_dir / f"{video_stem}_summary.md"
                md_path.write_text(
                    to_markdown(summary, frame_analyses, transcript),
                    encoding="utf-8",
                )
                outputs["markdown"] = str(md_path)
                print(f"  Markdown: {md_path}")

            if output_format in ("json", "all"):
                json_path = work_dir / f"{video_stem}_summary.json"
                json_path.write_text(
                    to_json(summary, frame_analyses, transcript),
                    encoding="utf-8",
                )
                outputs["json"] = str(json_path)
                print(f"  JSON: {json_path}")

            if output_format in ("txt", "all"):
                txt_path = work_dir / f"{video_stem}_summary.txt"
                txt_path.write_text(to_txt(summary), encoding="utf-8")
                outputs["txt"] = str(txt_path)
                print(f"  TXT: {txt_path}")

        if transcript:
            txt_path = work_dir / f"{video_stem}_transcript.txt"
            txt_path.write_text(
                "\n\n".join(f"[{s.start:.0f}s-{s.end:.0f}s] {s.text}" for s in transcript),
                encoding="utf-8",
            )
            outputs["transcript"] = str(txt_path)

        elapsed = time.time() - t0
        print(f"\n✓ 完成，耗时 {elapsed:.1f}s")

        return outputs

    def _save_json(self, path: Path, data) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
