"""
文件服务 - 本地文件存储、缩略图生成
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from PIL import Image as PILImage

from app.core.config import get_settings

if TYPE_CHECKING:
    pass

settings = get_settings()

# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# 支持的视频格式
SUPPORTED_VIDEO_FORMATS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

# 缩略图尺寸
THUMBNAIL_SIZE = (300, 300)


def _ensure_upload_dir() -> None:
    """确保上传目录存在"""
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)


def generate_unique_filename(original_filename: str) -> str:
    """
    生成唯一的文件名（保留扩展名）

    Args:
        original_filename: 原始文件名

    Returns:
        唯一文件名
    """
    ext = Path(original_filename).suffix.lower()
    unique_id = uuid4()
    return f"{unique_id}{ext}"


def validate_file_type(filename: str) -> str:
    """
    验证并返回文件类型

    Args:
        filename: 文件名

    Returns:
        文件类型 (image/video)

    Raises:
        ValueError: 不支持的文件类型
    """
    ext = Path(filename).suffix.lower()
    if ext in SUPPORTED_IMAGE_FORMATS:
        return "image"
    elif ext in SUPPORTED_VIDEO_FORMATS:
        return "video"
    else:
        raise ValueError(
            f"不支持的文件格式: {ext}. "
            f"图片: {', '.join(SUPPORTED_IMAGE_FORMATS)}, "
            f"视频: {', '.join(SUPPORTED_VIDEO_FORMATS)}"
        )


def save_uploaded_file(
    file_data: bytes,
    filename: str,
    subfolder: str = "",
) -> str:
    """
    保存上传的文件

    Args:
        file_data: 文件二进制数据
        filename: 原始文件名
        subfolder: 子文件夹（如 images/, videos/）

    Returns:
        保存后的文件路径

    Raises:
        ValueError: 文件类型不支持
    """
    _ensure_upload_dir()

    # 验证文件类型
    file_type = validate_file_type(filename)

    # 生成唯一文件名
    unique_filename = generate_unique_filename(filename)

    # 构造完整路径
    upload_path = Path(settings.upload_dir)
    if subfolder:
        save_path = upload_path / subfolder / unique_filename
        save_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        save_path = upload_path / unique_filename

    # 写入文件
    save_path.write_bytes(file_data)

    return str(save_path)


def generate_thumbnail(
    image_path: str, size: tuple[int, int] = THUMBNAIL_SIZE
) -> str | None:
    """
    生成图片缩略图

    Args:
        image_path: 图片路径
        size: 缩略图尺寸

    Returns:
        缩略图保存路径，失败返回 None
    """
    try:
        img = PILImage.open(image_path)
        img.thumbnail(size, PILImage.Resampling.LANCZOS)

        # 生成缩略图文件名
        path = Path(image_path)
        thumb_filename = f"{path.stem}_thumb{path.suffix}"
        thumb_path = path.parent / thumb_filename

        img.save(thumb_path, optimize=True, quality=85)
        return str(thumb_path)
    except Exception as e:
        print(f"生成缩略图失败: {e}")
        return None


def delete_file(file_path: str) -> bool:
    """
    删除文件

    Args:
        file_path: 文件路径

    Returns:
        是否成功
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception as e:
        print(f"删除文件失败: {e}")
        return False


def get_file_size(file_path: str) -> int:
    """
    获取文件大小（字节）

    Args:
        file_path: 文件路径

    Returns:
        文件大小
    """
    return Path(file_path).stat().st_size


def generate_video_thumbnail(
    video_path: str, timestamp: float = 1.0
) -> str | None:
    """
    生成视频缩略图（从指定时间戳）

    Args:
        video_path: 视频路径
        timestamp: 截图时间戳（秒）

    Returns:
        缩略图保存路径，失败返回 None
    """
    import subprocess

    path = Path(video_path)
    thumb_filename = f"{path.stem}_thumb.jpg"
    thumb_path = path.parent / thumb_filename

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-ss", str(timestamp),
        "-vframes", "1",
        "-vf", f"scale={THUMBNAIL_SIZE[0]}:{THUMBNAIL_SIZE[1]}",
        "-y",  # 覆盖已存在文件
        str(thumb_path),
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and Path(thumb_path).exists():
            return str(thumb_path)
        return None
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"生成视频缩略图失败: {e}")
        return None
