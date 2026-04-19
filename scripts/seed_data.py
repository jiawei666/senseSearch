#!/usr/bin/env python3
"""
SenseSearch 种子数据脚本
向 Milvus 和 PostgreSQL 导入示例内容数据
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.database import async_session_maker
from app.core.milvus import milvus_client
from app.models.content import Content
from app.services.embedding import embed_batch_texts, embed_image


# 示例内容数据
SAMPLE_CONTENTS = [
    {
        "title": "日落时分的海岸线",
        "description": "美丽的海景，夕阳西下，波光粼粼的海面与远处的山峦相映成趣。金色的阳光洒在沙滩上，形成一道温暖的光带。",
        "type": "image",
        "file_path": "sample_sunset.jpg",
        "source": "public",
        "tags": ["自然", "风景", "日落", "海洋", "摄影"],
    },
    {
        "title": "城市夜景 - 霓虹灯光",
        "description": "繁华都市的夜景，霓虹灯闪烁，高楼大厦林立。车水马龙的街道，流动的光线勾勒出现代城市的轮廓。",
        "type": "image",
        "file_path": "sample_city_night.jpg",
        "source": "public",
        "tags": ["城市", "夜景", "霓虹", "建筑", "摄影"],
    },
    {
        "title": "山间云海",
        "description": "清晨的高山，云海翻腾，旭日初升。云雾缭绕间，群山若隐若现，宛如仙境。",
        "type": "image",
        "file_path": "sample_clouds_mountain.jpg",
        "source": "public",
        "tags": ["自然", "风景", "山", "云", "日出"],
    },
    {
        "title": "极光下的北极",
        "description": "绚丽多彩的极光在夜空中舞动，绿色与紫色的光带交织。雪白的冰原在极光下闪耀着神秘的光芒。",
        "type": "image",
        "file_path": "sample_aurora.jpg",
        "source": "public",
        "tags": ["自然", "极光", "夜空", "北极", "奇观"],
    },
    {
        "title": "樱花盛开",
        "description": "春季的樱花公园，粉白色的樱花如云如霞。花瓣飘落，游客漫步其中，享受春日的美好时光。",
        "type": "image",
        "file_path": "sample_cherry_blossom.jpg",
        "source": "public",
        "tags": ["自然", "花卉", "春天", "樱花", "公园"],
    },
    {
        "title": "海洋生物纪录片 - 珊瑚礁",
        "description": "深入探索热带珊瑚礁生态系统。色彩斑斓的鱼群在珊瑚间穿梭，海龟悠闲游弋，展现海底世界的勃勃生机。",
        "type": "video",
        "file_path": "sample_coral_reef.mp4",
        "source": "public",
        "tags": ["海洋", "纪录片", "珊瑚", "生物", "自然"],
    },
    {
        "title": "城市街头摄影 - 车流不息",
        "description": "记录城市街道的日常，行人匆匆，车流不断。通过镜头捕捉都市人的生活百态与城市节奏。",
        "type": "video",
        "file_path": "sample_street_video.mp4",
        "source": "public",
        "tags": ["城市", "街头", "摄影", "人文", "纪录片"],
    },
    {
        "title": "烹饪教程 - 经典意大利面",
        "description": "详细讲解如何制作正宗的意大利面，从制作面团到调配酱汁。每个步骤都有特写镜头，让观众轻松掌握要领。",
        "type": "video",
        "file_path": "sample_pasta_cooking.mp4",
        "source": "public",
        "tags": ["烹饪", "教程", "意大利面", "美食", "教学"],
    },
    {
        "title": "Python 快速入门教程",
        "description": "面向编程新手的 Python 教程，涵盖基础语法、数据结构、函数定义等核心概念。通过大量实例和练习帮助理解。",
        "type": "document",
        "file_path": "python_intro.pdf",
        "source": "public",
        "tags": ["编程", "Python", "教程", "入门", "文档"],
    },
    {
        "title": "摄影构图技巧大全",
        "description": "深入解析各种摄影构图方法，如三分法、引导线、框架式构图等。配以大量示例图片，适合各水平摄影爱好者。",
        "type": "document",
        "file_path": "photography_composition.pdf",
        "source": "public",
        "tags": ["摄影", "教程", "构图", "技巧", "学习"],
    },
    {
        "title": "旅行日记 - 北欧之旅",
        "description": "记录北欧四国之旅的所见所感，包括挪威的峡湾、芬兰的极光、瑞典的设计与丹麦的童话。",
        "type": "text",
        "file_path": "nordic_travel.md",
        "source": "public",
        "tags": ["旅行", "北欧", "日记", "游记", "体验"],
    },
    {
        "title": "机器学习基础概念",
        "description": "介绍机器学习的核心概念，包括监督学习、非监督学习、强化学习等基本范式。适合 AI 初学者。",
        "type": "text",
        "file_path": "ml_basics.md",
        "source": "public",
        "tags": ["AI", "机器学习", "教程", "技术", "概念"],
    },
]


async def seed_postgresql(contents: list[dict[str, Any]]) -> list[str]:
    """将内容数据导入 PostgreSQL"""
    from sqlalchemy.ext.asyncio import AsyncSession

    async with async_session_maker() as session:
        content_ids = []

        for content_data in contents:
            # 创建 Content 记录
            content = Content(
                type=content_data["type"],
                title=content_data["title"],
                description=content_data["description"],
                file_path=content_data["file_path"],
                source=content_data["source"],
                tags=content_data["tags"],
                status="indexed",
                extra_metadata={"seed": True},
            )

            session.add(content)
            await session.flush()
            content_ids.append(str(content.id))

        await session.commit()

        print(f"✓ PostgreSQL: 已导入 {len(content_ids)} 条内容记录")

        return content_ids


async def seed_milvus(content_ids: list[str], contents: list[dict[str, Any]]) -> None:
    """将内容向量导入 Milvus"""
    try:
        # 准备用于嵌入的文本
        texts_for_embedding = []
        for content in contents:
            # 组合标题和描述作为嵌入文本
            combined = f"{content['title']} {content['description']}"
            texts_for_embedding.append(combined)

        # 批量生成向量
        print("正在生成向量嵌入...")
        embeddings = await embed_batch_texts(texts_for_embedding)
        print(f"✓ 向量生成完成，维度: {len(embeddings[0])}")

        # 准备 Milvus 数据
        milvus_data = []
        for idx, (content_id, content) in enumerate(zip(content_ids, contents)):
            milvus_data.append(
                {
                    "id": content_id,
                    "vector": embeddings[idx],
                    "content_type": content["type"],
                    "title": content["title"],
                    "description": content["description"],
                    "source": content["source"],
                    "tags": content.get("tags", []),
                    "created_at": datetime.utcnow().isoformat(),
                }
            )

        # 批量插入 Milvus
        from pymilvus import Collection

        collection = await milvus_client.get_collection()
        if collection:
            await collection.insert(milvus_data)
            await collection.flush()
            print(f"✓ Milvus: 已导入 {len(milvus_data)} 条向量数据")
        else:
            print("⚠ Milvus 集合不存在，请先创建集合")

    except Exception as e:
        print(f"✗ Milvus 导入失败: {e}")
        raise


async def clear_seed_data() -> None:
    """清除种子数据（可选功能）"""
    print("\n正在清除种子数据...")

    # 清除 Milvus 中的种子数据
    try:
        from pymilvus import Collection

        collection = await milvus_client.get_collection()
        if collection:
            # 删除带有 seed 标记的数据
            expr = "extra_metadata['seed'] == True"
            await collection.delete(expr)
            await collection.flush()
            print("✓ Milvus: 种子数据已清除")
    except Exception as e:
        print(f"⚠ 清除 Milvus 种子数据失败: {e}")

    # 清除 PostgreSQL 中的种子数据
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import delete

    async with async_session_maker() as session:
        stmt = delete(Content).where(Content.extra_metadata["seed"].astext == "True")
        await session.execute(stmt)
        await session.commit()
        print("✓ PostgreSQL: 种子数据已清除")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="SenseSearch 种子数据管理脚本")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="清除种子数据",
    )
    args = parser.parse_args()

    if args.clear:
        await clear_seed_data()
        return

    print("=" * 60)
    print("SenseSearch 种子数据导入工具")
    print("=" * 60)

    # 导入 PostgreSQL
    print("\n[1/2] 导入 PostgreSQL...")
    content_ids = await seed_postgresql(SAMPLE_CONTENTS)

    # 导入 Milvus
    print("\n[2/2] 导入 Milvus...")
    await seed_milvus(content_ids, SAMPLE_CONTENTS)

    print("\n" + "=" * 60)
    print("种子数据导入完成！")
    print("=" * 60)
    print(f"\n已导入 {len(SAMPLE_CONTENTS)} 条示例内容：")
    print(f"  - 图片: {sum(1 for c in SAMPLE_CONTENTS if c['type'] == 'image')} 条")
    print(f"  - 视频: {sum(1 for c in SAMPLE_CONTENTS if c['type'] == 'video')} 条")
    print(f"  - 文档: {sum(1 for c in SAMPLE_CONTENTS if c['type'] == 'document')} 条")
    print(f"  - 文本: {sum(1 for c in SAMPLE_CONTENTS if c['type'] == 'text')} 条")


if __name__ == "__main__":
    asyncio.run(main())
