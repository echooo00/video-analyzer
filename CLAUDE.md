# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 A/B 测试数据分析项目，使用 Jupyter Notebook 进行实验效果评估、假设检验和置信区间计算。

## 环境

- **主开发环境**：conda base (`E:\anaconda`), Python 3.10.9
- **备用环境**：conda `pytorch` (`E:\anaconda\envs\pytorch`), Python 3.10.18 (含 CUDA PyTorch)
- `.venv/` — Python 3.13 虚拟环境（仅用于旧版 A/B 测试 notebook）
- FFmpeg 位于：`D:\Tecplot\Tecplot 360 EX 2022 R1\bin\ffmpeg.exe`（ffprobe 不可用，项目改用 ffmpeg stderr 解析）

## 项目结构

```
数分项目_ABTEST/           # A/B 测试数据分析
  AB TEST.ipynb
  requirements.txt
video_analyzer/            # 视频解析总结工具 (新增)
  config.py                # 全局配置 + API Key
  pipeline.py              # 主编排器
  cli.py                   # 命令行入口
  web_ui.py                # Gradio 网页界面
  video/                   # 视频处理层
    ingest.py              # 元数据提取 (ffmpeg)
    scene_detector.py      # 场景分割 (OpenCV 直方图)
    frame_extractor.py     # 关键帧提取 + 去重
    audio_extractor.py     # 音频轨提取
  ai/                      # AI 分析层
    prompts.py             # Prompt 模板
    frame_analyzer.py      # VLM API 画面分析
    transcriber.py         # faster-whisper 语音转写
    summarizer.py          # LLM 综合总结
  output/                  # 输出层
    formatter.py           # Markdown/JSON/TXT 格式化
  utils/                   # 工具层
    ffmpeg.py              # FFmpeg 查找 + 调用
    cache.py               # API 结果缓存
    image_utils.py         # 图片压缩
data/                      # A/B 测试数据
机器学习项目_股票分析/       # 股票分析 ML 项目
```

## 视频解析工具 使用

```powershell
# 分析单个视频 (先 dry-run 测试本地处理)
python -m video_analyzer.cli analyze my_video.mp4 --dry-run

# 正式分析 (需要 API Key)
python -m video_analyzer.cli analyze my_video.mp4

# 批量分析
python -m video_analyzer.cli batch videos/*.mp4

# 启动网页界面
python -m video_analyzer.web_ui
```

首次使用需在 `video_analyzer/.env` 配置 API Key（参考 `.env.example`）。
