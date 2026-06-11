"""图片处理工具 — 压缩、resize."""
import io
from typing import Optional

from PIL import Image

from video_analyzer.config import KEYFRAME_MAX_WIDTH, KEYFRAME_JPEG_QUALITY


def compress_image(
    image: Image.Image,
    max_width: int = KEYFRAME_MAX_WIDTH,
    quality: int = KEYFRAME_JPEG_QUALITY,
) -> bytes:
    """压缩图片为 JPEG 字节，限制宽度并控制画质."""
    w, h = image.size
    if w > max_width:
        ratio = max_width / w
        new_size = (max_width, int(h * ratio))
        image = image.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    image = image.convert("RGB")
    image.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def load_and_compress(image_path: str) -> bytes:
    """从文件路径加载图片并压缩后返回字节."""
    img = Image.open(image_path)
    return compress_image(img)


def image_bytes_to_pil(data: bytes) -> Image.Image:
    """将 JPEG 字节转为 PIL Image."""
    return Image.open(io.BytesIO(data))
