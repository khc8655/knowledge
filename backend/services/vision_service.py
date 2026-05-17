"""
视觉理解服务 — 图片描述 + PPT 页面摘要
"""
import base64
import json
import requests
from typing import List, Dict, Optional, Tuple


def describe_image(
    image_bytes: bytes,
    content_type: str = "image/png",
    profile_name: str = "vision",
) -> str:
    """调用视觉模型描述图片内容。"""
    from config import AppConfig
    profile = AppConfig().get_llm_profile(profile_name)

    b64 = base64.b64encode(image_bytes).decode("utf-8")

    resp = requests.post(
        f"{profile['base_url']}/chat/completions",
        headers={
            "Authorization": f"Bearer {profile['api_key']}",
            "Content-Type": "application/json",
        },
        json={
            "model": profile["model"],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{content_type};base64,{b64}"},
                        },
                        {
                            "type": "text",
                            "text": (
                                "请详细描述这张图片的内容。包括：\n"
                                "1. 图片中的文字、标题、标签\n"
                                "2. 图表类型和关键数据（如有）\n"
                                "3. 产品型号、界面元素、架构组件（如有）\n"
                                "4. 图片要表达的核心信息\n"
                                "用简洁的中文描述，不要遗漏关键信息。"
                            ),
                        },
                    ],
                }
            ],
            "temperature": 0.1,
            "max_tokens": 500,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def summarize_slide(
    title: str,
    text_content: str,
    image_descriptions: List[str],
    doc_file: str = "",
) -> str:
    """用 LLM 将文本 + 图片描述合并为结构化摘要。"""
    from config import AppConfig
    profile = AppConfig().get_llm_profile("annotation")

    parts = []
    if text_content.strip():
        parts.append(f"【页面文本】\n{text_content.strip()}")
    for i, desc in enumerate(image_descriptions):
        parts.append(f"【图片{i + 1}描述】\n{desc.strip()}")

    combined = "\n\n".join(parts)

    prompt = f"""请将以下 PPT 页面内容（文本 + 图片描述）合并为一段精炼的摘要。

来源文档: {doc_file}
页面标题: {title}

{combined}

要求：
1. 摘要 50-150 字，保留关键信息（产品型号、参数、功能、场景等）
2. 如果有图片描述，将图片中的关键信息融入摘要
3. 不要遗漏产品型号、数字、技术参数等检索关键信息
4. 直接输出摘要文本，不要加前缀或格式"""

    resp = requests.post(
        f"{profile['base_url']}/chat/completions",
        headers={
            "Authorization": f"Bearer {profile['api_key']}",
            "Content-Type": "application/json",
        },
        json={
            "model": profile["model"],
            "messages": [
                {
                    "role": "system",
                    "content": "你是小鱼易连产品知识库的内容摘要助手。将 PPT 页面的文本和图片描述合并为精炼摘要。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 300,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
