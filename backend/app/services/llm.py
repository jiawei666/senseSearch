"""LLM 服务 - MVP mock 版本"""
from typing import Any
from enum import Enum


class ConversationAction(str, Enum):
    SEARCH = "search"
    CLARIFY = "clarify"
    SUMMARIZE = "summarize"


async def recognize_intent(
    query: str,
    conversation_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """识别用户意图（MVP 简化 - 关键词匹配）"""
    # MVP: 简化实现 - 关键词匹配规则
    
    # 空查询
    if not query or not query.strip():
        return {
            "action": ConversationAction.SEARCH,
            "query": query,
            "filters": {},
        }
    
    # 图片相关关键词
    image_keywords = ["图片", "photo", "照片", "相片", "图", "jpg", "jpeg", "png"]
    if any(kw in query.lower() for kw in image_keywords):
        return {
            "action": ConversationAction.SEARCH,
            "query": query,
            "filters": {"type": "image"},
        }
    
    # 视频相关关键词
    video_keywords = ["视频", "video", "影片", "movie", "mp4", "avi", "mov"]
    if any(kw in query.lower() for kw in video_keywords):
        return {
            "action": ConversationAction.SEARCH,
            "query": query,
            "filters": {"type": "video"},
        }
    
    # 澄清关键词
    clarify_keywords = ["什么", "哪", "哪个", "如何", "多少", "几种", "找", "搜索"]
    if any(kw in query.lower() for kw in clarify_keywords):
        return {
            "action": ConversationAction.CLARIFY,
            "question": f"您想搜索{query}的什么内容？是图片还是视频？",
            "query": query,
            "filters": {},
            "search": False,
        }
    
    # 总结关键词
    summarize_keywords = ["最近", "总结", "刚才", "刚才"]
    if any(kw in query.lower() for kw in summarize_keywords):
        return {
            "action": ConversationAction.SUMMARIZE,
            "summary": "我找到了一些搜索结果，需要总结吗？",
            "query": query,
            "filters": {},
            "search": False,
        }
    
    # 默认：搜索
    return {
        "action": ConversationAction.SEARCH,
        "query": query,
        "filters": {},
    }


async def generate_conversational_answer(
    query: str,
    search_results: list[dict[str, Any]],
    conversation_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """生成对话式回答（MVP 简化）"""
    if search_results:
        result_count = min(len(search_results), 3)
        answer = f"我为您找到了 {result_count} 个相关结果。"
        ref_ids = [r.get("content_id") for r in search_results[:result_count]]
    else:
        answer = f"抱歉，我无法理解您的查询：'{query}'。请尝试提供更多细节，比如'搜索猫的照片'。"
        ref_ids = []
    
    return {
        "answer": answer,
        "reference_ids": ref_ids,
        "follow_up": "是否需要我帮您调整搜索关键词？" if not search_results else None,
    }


async def summarize_results(
    results: list[dict[str, Any]],
    query: str,
    max_results: int = 5,
) -> dict[str, Any]:
    """总结搜索结果（MVP 简化）"""
    result_count = min(len(results), max_results)
    summary = f"根据您最近的搜索，我找到了 {result_count} 个相关结果。"
    
    return {
        "summary": summary,
        "suggestions": ["尝试调整搜索关键词", "添加更多描述"],
        "action": "search",
    }


async def clarify_intent(
    query: str,
    conversation_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """澄清用户意图（MVP 简化）"""
    question = f"您想搜索'{query}'的什么内容？是图片、视频还是其他？"
    
    return {
        "question": question,
        "suggestion": "您可以包含图片类型、场景描述等。",
        "query": query,
        "action": "clarify",
        "filters": {},
        "search": False,
    }
