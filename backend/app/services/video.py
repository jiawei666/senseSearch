"""
视频处理服务 - 抽帧、关键帧提取
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    pass

settings = get_settings()

# 支持的视频格式
SUPPORTED_VIDEO_FORMATS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

# 默认抽帧间隔（秒）
DEFAULT_FRAME_INTERVAL = 2.0

# 最大帧数限制
MAX_FRAMES = 30


def _validate_video_file(file_path: str) -> None:
    """
    验证视频文件

    Args:
        file_path: 视频文件路径

    Raises:
        ValueError: 文件无效
    """
    path = Path(file_path)

    if not path.exists():
        raise ValueError(f"视频文件不存在: {file_path}")

    if not path.is_file():
        raise ValueError(f"路径不是文件: {file_path}")

    if path.suffix.lower() not in SUPPORTED_VIDEO_FORMATS:
        raise ValueError(
            f"不支持的视频格式: {path.suffix}. "
            f"支持的格式: {', '.join(SUPPORTED_VIDEO_FORMATS)}"
        )

    # 检查文件大小（限制 500MB）
    file_size = path.stat().st_size
    max_size = settings.max_file_size
    if file_size > max_size:
        raise ValueError(
            f"视频文件过大: {file_size / 1024 / 1024:.1f}MB. "
            f"最大支持: {max_size / 1024 / 1024:.1f}MB"
        )


def _run_ffmpeg_extract_frames(
    video_path: str, output_dir: str, interval: float
) -> list[str]:
    """
    使用 ffmpeg 抽取视频帧

    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        interval: 抽帧间隔（秒）

    Returns:
        帧文件路径列表
    """
    output_pattern = os.path.join(output_dir, "frame_%04d.jpg")

    # ffmpeg 命令：每 interval 秒抽一帧
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"fps=1/{interval}",
        "-q:v", "2",  # JPEG 质量
        "-y",  # 覆盖已存在文件
        output_pattern,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            # 可能是空视频或很短的视频，不报错
            if "Output file is empty" in result.stderr:
                return []
            raise RuntimeError(f"ffmpeg 抽帧失败: {result.stderr}")

    except subprocess.TimeoutExpired:
        raise RuntimeError("视频处理超时")

    # 获取生成的帧文件
    frame_files = sorted(Path(output_dir).glob("frame_*.jpg"))

    # 限制最大帧数
    if len(frame_files) > MAX_FRAMES:
        frame_files = frame_files[:MAX_FRAMES]

    return [str(f) for f in frame_files]


def _extract_base64_from_images(
    image_paths: list[str], cleanup: bool = True
) -> list[str]:
    """
    从图片路径提取 base64 数据

    Args:
        image_paths: 图片路径列表
        cleanup: 是否清理临时文件

    Returns:
        base64 编码列表
    """
    base64_list = []

    for img_path in image_paths:
        with open(img_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
            base64_list.append(data)

    # 清理临时文件
    if cleanup:
        for img_path in image_paths:
            try:
                os.remove(img_path)
            except OSError:
                pass
        # 清理临时目录（如果为空）
        try:
            output_dir = os.path.dirname(image_paths[0]) if image_paths else ""
            if output_dir and output_dir.startswith(tempfile.gettempdir()):
                os.rmdir(output_dir)
        except OSError:
            pass

    return base64_list


import base64


async def extract_video_frames(
    video_path: str, interval_seconds: float = DEFAULT_FRAME_INTERVAL
) -> list[str]:
    """
    提取视频帧为 base64 列表

    Args:
        video_path: 视频文件路径
        interval_seconds: 抽帧间隔（秒）

    Returns:
        base64 编码的帧列表

    Raises:
        ValueError: 视频文件无效
        RuntimeError: 处理失败
    """
    # 验证文件
    _validate_video_file(video_path)

    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 抽帧
        frame_files = _run_ffmpeg_extract_frames(
            video_path, temp_dir, interval_seconds
        )

        if not frame_files:
            # 空视频或无法抽帧
            return []

        # 提取 base64
        return _extract_base64_from_images(frame_files, cleanup=False)


def get_video_duration(file_path: str) -> float:
    """
    获取视频时长（秒）

    Args:
        file_path: 视频文件路径

    Returns:
        时长（秒）
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise RuntimeError(f"获取视频时长失败: {result.stderr}")
        return float(result.stdout.strip())
    except ValueError:
        raise RuntimeError("无效的视频时长")
    except subprocess.TimeoutExpired:
        raise RuntimeError("获取视频时长超时")
