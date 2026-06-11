# 🎬 视频分析工具

本地视频内容识别与要点总结工具 — 上传视频，自动生成结构化分析报告。

## 功能

- **📹 视频处理** — FFmpeg 提取元数据，OpenCV 场景检测与关键帧去重
- **🎙️ 语音转写** — 本地 Whisper 模型（支持 tiny ~ large，默认 medium）
- **🖼️ 画面分析** — 阿里百炼 Qwen-VL 云端视觉模型，识别场景类型、物体、文字、动作
- **📝 智能总结** — DeepSeek LLM 综合帧描述 + 字幕，生成要点、话题、标签
- **🖥️ Web UI** — Gradio 网页界面，上传视频即可分析
- **⌨️ CLI** — 命令行工具，支持单文件 / 批量处理

## 效果展示

### Web 界面

![Web UI](docs/screenshots/web_ui.png)

### 分析结果示例

```markdown
# 阴天城市景观

**一段4秒的阴天城市景观视频，展示树木与雾气中的高楼。**

**话题分类**：`城市景观` | `阴天` | `自然与建筑`

## 关键要点

- ⭐ **[2s]** 阴天城市景观，前景树木，背景雾气笼罩的高楼

## 完整总结

该视频时长4秒，画面为阴天城市景观。前景是茂密的树木，背景是被雾气笼罩的高层建筑群，
整体色调偏冷，氛围宁静。
```

## 技术栈

| 层 | 技术 |
|---|---|
| 视频处理 | FFmpeg, OpenCV, imagehash (感知哈希去重) |
| 语音转写 | openai-whisper (PyTorch), faster-whisper (备选) |
| 画面分析 | Qwen-VL-Max (阿里百炼 DashScope API) |
| 文本总结 | DeepSeek Chat API |
| Web UI | Gradio 6 |
| 缓存 | 本地 JSON 文件缓存 (SHA256 摘要去重) |

## 项目结构

```
video_analyzer/
├── config.py              # 全局配置（API Key、路径、阈值）
├── pipeline.py            # 主编排器（5 阶段流水线）
├── cli.py                 # 命令行入口
├── web_ui.py              # Gradio 网页界面
├── video/
│   ├── ingest.py          # 视频元数据提取
│   ├── scene_detector.py  # 直方图场景分割
│   ├── frame_extractor.py # 关键帧提取 + 感知哈希去重
│   └── audio_extractor.py # 音频轨提取 (16kHz WAV)
├── ai/
│   ├── prompts.py         # Prompt 模板（画面分析 / 总结）
│   ├── frame_analyzer.py  # VLM 画面分析（Qwen-VL）
│   ├── transcriber.py     # 语音转文字（Whisper）
│   └── summarizer.py      # 综合总结（DeepSeek）
├── output/
│   └── formatter.py       # Markdown / JSON / TXT 格式化
└── utils/
    ├── ffmpeg.py           # FFmpeg 查找与调用封装
    ├── cache.py            # API 结果磁盘缓存
    └── image_utils.py      # 图片压缩处理
```

## 快速开始

### 环境要求

- Python ≥ 3.10
- FFmpeg（需在 PATH 中或配置 `FFMPEG_PATH`）
- conda base 环境推荐（含 PyTorch + OpenCV）

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/video-analyzer.git
cd video-analyzer

# 2. 安装
pip install -e .

# 3. 双击运行一键安装（创建桌面快捷方式）
install.bat
```

或者手动安装依赖：

```bash
pip install openai-whisper openai pillow imagehash gradio opencv-python python-dotenv
```

### 配置 API Key

在 `%USERPROFILE%\.video_analyzer\.env` 中配置（参考 `video_analyzer/.env.example`）：

```env
# 画面分析（阿里百炼 Qwen-VL）
VLM_API_KEY=sk-your-key-here
VLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
VLM_MODEL=qwen-vl-max

# 文本总结（DeepSeek）
LLM_API_KEY=sk-your-key-here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 语音转写
TRANSCRIPTION_BACKEND=local
WHISPER_MODEL_SIZE=medium
WHISPER_LANGUAGE=zh
```

### 启动

```bash
# 网页界面（推荐）
python -m video_analyzer.web_ui

# 命令行分析
python -m video_analyzer.cli analyze my_video.mp4

# 命令行批量
python -m video_analyzer.cli batch videos/*.mp4

# 干跑测试（不调用 API）
python -m video_analyzer.cli analyze my_video.mp4 --dry-run
```

## 输出

每个视频分析后生成：

| 文件 | 内容 |
|---|---|
| `{视频名}_summary.md` | Markdown 结构化报告（标题、要点、总结、标签） |
| `{视频名}_summary.json` | 机读 JSON 数据 |
| `{视频名}_summary.txt` | 纯文本总结 |
| `{视频名}_transcript.txt` | 完整语音转文字 |
| `keyframes/` | 关键帧图片 |

## 配置参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `SCENE_THRESHOLD_SSIM` | 0.5 | 场景切换敏感度（越小越敏感） |
| `MAX_KEYFRAMES` | 60 | 最大分析帧数 |
| `WHISPER_MODEL_SIZE` | medium | tiny/base/small/medium/large |
| `API_RETRY_ATTEMPTS` | 3 | API 调用重试次数 |

## License

MIT
