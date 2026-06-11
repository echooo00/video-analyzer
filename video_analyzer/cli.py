"""命令行入口 — 视频分析工具."""
import argparse
import sys
from pathlib import Path

from video_analyzer.pipeline import Pipeline


def main():
    parser = argparse.ArgumentParser(
        prog="video-analyzer",
        description="本地视频内容识别与要点总结工具",
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # analyze 子命令
    analyze_parser = subparsers.add_parser("analyze", help="分析单个视频")
    analyze_parser.add_argument(
        "video", type=str, help="视频文件路径"
    )
    analyze_parser.add_argument(
        "--output", "-o", type=str, default="output",
        help="输出目录 (默认: output)"
    )
    analyze_parser.add_argument(
        "--format", "-f", type=str, default="all",
        choices=["md", "json", "txt", "all"],
        help="输出格式 (默认: all)"
    )
    analyze_parser.add_argument(
        "--skip-transcription", action="store_true",
        help="跳过语音转写"
    )
    analyze_parser.add_argument(
        "--skip-frame-analysis", action="store_true",
        help="跳过画面分析"
    )
    analyze_parser.add_argument(
        "--dry-run", action="store_true",
        help="仅运行本地处理，不调用 API"
    )
    analyze_parser.add_argument(
        "--resume", action="store_true",
        help="从缓存恢复 API 结果"
    )

    # batch 子命令
    batch_parser = subparsers.add_parser("batch", help="批量分析多个视频")
    batch_parser.add_argument(
        "files", type=str, nargs="+", help="视频文件路径或 glob 模式"
    )
    batch_parser.add_argument(
        "--output", "-o", type=str, default="output",
        help="输出目录 (默认: output)"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "analyze":
        video_path = Path(args.video)
        if not video_path.exists():
            print(f"错误: 文件不存在: {args.video}")
            sys.exit(1)

        pipeline = Pipeline(output_dir=args.output)
        outputs = pipeline.run(
            str(video_path),
            output_format=args.format,
            skip_transcription=args.skip_transcription,
            skip_frame_analysis=args.skip_frame_analysis,
            dry_run=args.dry_run,
        )

        if not outputs:
            print("未生成任何输出文件 (可能因为 dry-run 模式)")
        else:
            print(f"\n生成的文件:")
            for fmt, path in outputs.items():
                print(f"  [{fmt}] {path}")

    elif args.command == "batch":
        import glob
        pipeline = Pipeline(output_dir=args.output)

        all_files = []
        for pattern in args.files:
            matched = glob.glob(pattern)
            if matched:
                all_files.extend(matched)
            else:
                print(f"警告: 未匹配到文件: {pattern}")

        if not all_files:
            print("错误: 没有找到任何视频文件")
            sys.exit(1)

        print(f"共 {len(all_files)} 个视频文件待处理\n")
        for i, f in enumerate(all_files, 1):
            print(f"\n{'='*60}")
            print(f"[{i}/{len(all_files)}]")
            print(f"{'='*60}")
            try:
                pipeline.run(f)
            except Exception as e:
                print(f"✗ 处理失败: {e}")
                continue

        print(f"\n全部完成。")


if __name__ == "__main__":
    main()
