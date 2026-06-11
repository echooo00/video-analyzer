"""Gradio 网页界面 — 上传视频 → 分析 → 展示结果."""
import tempfile
from pathlib import Path

import gradio as gr

from video_analyzer.pipeline import Pipeline


def analyze_video(video_file, skip_transcription, skip_frame_analysis, progress=gr.Progress()):
    """处理上传的视频文件并返回结果."""
    if video_file is None:
        return "请上传一个视频文件", "", "", ""

    video_path = video_file.name if hasattr(video_file, 'name') else str(video_file)

    with tempfile.TemporaryDirectory() as tmpdir:
        progress(0.1, desc="正在初始化...")
        pipeline = Pipeline(output_dir=tmpdir)

        progress(0.2, desc="正在分析视频...")
        outputs = pipeline.run(
            video_path,
            output_format="all",
            skip_transcription=skip_transcription,
            skip_frame_analysis=skip_frame_analysis,
        )

        markdown_content = ""
        json_content = ""
        transcript_content = ""

        if "markdown" in outputs:
            markdown_content = Path(outputs["markdown"]).read_text(encoding="utf-8")
        if "json" in outputs:
            json_content = Path(outputs["json"]).read_text(encoding="utf-8")
        if "transcript" in outputs:
            transcript_content = Path(outputs["transcript"]).read_text(encoding="utf-8")

        progress(1.0, desc="完成!")
        return markdown_content, json_content, transcript_content, "分析完成!"


def create_ui():
    """创建 Gradio 界面."""
    with gr.Blocks(title="视频分析工具", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎬 视频内容分析工具

        上传本地视频文件，自动识别视频内容并生成结构化要点总结。
        - **画面分析**：AI 视觉模型识别每一帧内容
        - **语音转写**：自动将语音转为文字
        - **智能总结**：生成要点、话题分类、行动项
        """)

        with gr.Row():
            with gr.Column(scale=1):
                video_input = gr.Video(
                    label="上传视频",
                    sources=["upload"],
                )
                skip_trans = gr.Checkbox(label="跳过语音转写", value=False)
                skip_frame = gr.Checkbox(label="跳过画面分析", value=False)
                analyze_btn = gr.Button("开始分析", variant="primary", size="lg")

                status = gr.Textbox(label="状态", interactive=False)

            with gr.Column(scale=2):
                with gr.Tabs():
                    with gr.TabItem("总结 (Markdown)"):
                        output_md = gr.Markdown(
                            value="等待上传视频...",
                            label="分析结果",
                        )
                    with gr.TabItem("JSON"):
                        output_json = gr.Code(
                            language="json",
                            label="结构化数据",
                        )
                    with gr.TabItem("语音转文字"):
                        output_transcript = gr.Textbox(
                            label="语音转文字内容",
                            lines=15,
                            max_lines=30,
                        )

        analyze_btn.click(
            fn=analyze_video,
            inputs=[video_input, skip_trans, skip_frame],
            outputs=[output_md, output_json, output_transcript, status],
        )

    return demo


def main():
    demo = create_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True,
    )


if __name__ == "__main__":
    main()
