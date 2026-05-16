import hashlib
import json
import os
import time
from typing import Dict, Any, Optional, List

from card.store import CardStore


ANNOTATION_PROMPT_SYSTEM = "你是小鱼易连产品知识库的标注助手。你的任务是分析技术文档片段，输出结构化的语义标签。仅输出 JSON，不要输出任何其他文本。"

ANNOTATION_PROMPT_USER = """请分析以下文档片段，输出 JSON 格式的语义标注。

文档上下文: {doc_file} > {path}
标题: {title}
正文: {body}

输出格式:
{{
  "intent_tags": [从标签库中选择 0-3 个],
  "concept_tags": [提取 0-5 个核心技术概念],
  "scenario_tags": [提取 0-5 个应用场景],
  "card_type": "capability/parameter/price/scenario/architecture/update",
  "summary": "一句话描述本节内容（50字以内）",
  "models": [提取产品型号如 AE800/PE8000],
  "keywords": [提取 0-5 个检索关键词],
  "negative_concepts": [与本节无关但易混淆的概念],
  "quality_tier": "high/medium/low/placeholder",
  "content_hash": "{content_hash}"
}}

标签库 (intent_tags 只能从中选择):
- 安全保障: 加密/认证/权限/审计/合规
- 功能更新: 新功能/版本迭代/发版说明
- 架构设计: 系统拓扑/模块设计/技术选型
- 部署运维: 安装/配置/监控/升级
- 场景方案: 行业方案/客户案例/应用场景
- 报价价格: 产品价格/配件价格/报价体系
- 性能参数: 硬件规格/性能指标/技术参数
- 集成对接: API/SDK/接口/第三方集成"""

VALID_INTENT_TAGS = {
    "安全保障", "功能更新", "架构设计", "部署运维",
    "场景方案", "报价价格", "性能参数", "集成对接",
}

VALID_CARD_TYPES = {"capability", "parameter", "price", "scenario", "architecture", "update"}
VALID_QUALITY_TIERS = {"high", "medium", "low", "placeholder"}


def annotate_card(card: Dict[str, Any], llm_call=None) -> Dict[str, Any]:
    body = card.get("body", "")
    content_hash = hashlib.sha256(body.encode()).hexdigest()[:16]

    if llm_call is None:
        llm_call = _default_llm_call

    prompt = ANNOTATION_PROMPT_USER.format(
        doc_file=card.get("doc_file", ""),
        path=card.get("path", ""),
        title=card.get("title", ""),
        body=body[:1200],
        content_hash=content_hash,
    )

    try:
        result = llm_call(ANNOTATION_PROMPT_SYSTEM, prompt)
        annotation = json.loads(result)
    except (json.JSONDecodeError, Exception):
        annotation = _fallback_annotation(card, content_hash)

    annotation = _validate_annotation(annotation, content_hash)

    from datetime import datetime, timezone
    annotation["annotated_at"] = datetime.now(timezone.utc).isoformat()
    annotation["annotation_version"] = (card.get("semantic") or {}).get("annotation_version", 0) + 1

    return annotation


def _fallback_annotation(card: Dict, content_hash: str) -> Dict:
    return {
        "intent_tags": [],
        "concept_tags": [],
        "scenario_tags": [],
        "card_type": "capability",
        "summary": card.get("title", ""),
        "models": [],
        "keywords": [],
        "negative_concepts": [],
        "quality_tier": "placeholder",
        "content_hash": content_hash,
    }


def _validate_annotation(annotation: Dict, content_hash: str) -> Dict:
    result = {}
    result["intent_tags"] = [t for t in annotation.get("intent_tags", []) if t in VALID_INTENT_TAGS][:3]
    result["concept_tags"] = annotation.get("concept_tags", [])[:5]
    result["scenario_tags"] = annotation.get("scenario_tags", [])[:5]
    result["card_type"] = annotation.get("card_type", "capability")
    if result["card_type"] not in VALID_CARD_TYPES:
        result["card_type"] = "capability"
    result["summary"] = str(annotation.get("summary", ""))[:50]
    result["models"] = annotation.get("models", [])
    result["keywords"] = annotation.get("keywords", [])[:5]
    result["negative_concepts"] = annotation.get("negative_concepts", [])
    result["quality_tier"] = annotation.get("quality_tier", "placeholder")
    if result["quality_tier"] not in VALID_QUALITY_TIERS:
        result["quality_tier"] = "placeholder"
    result["content_hash"] = content_hash
    return result


def _default_llm_call(system: str, user: str) -> str:
    import requests
    cfg_path = os.path.join(os.environ.get("KB_DATA_DIR", "./data"), "config.yaml")
    api_key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    model = os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

    if os.path.exists(cfg_path):
        import yaml
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f) or {}
        api_key = cfg.get("llm_api_key", api_key)
        base_url = cfg.get("llm_base_url", base_url)
        model = cfg.get("llm_model", model)

    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
            "max_tokens": 500,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def annotate_batch(store: CardStore, card_ids: List[str] = None, llm_call=None) -> int:
    annotated = 0
    if card_ids is None:
        result = store.list_cards(page_size=10000)
        cards = result["items"]
    else:
        cards = [store.get(cid) for cid in card_ids if store.get(cid)]

    for card in cards:
        semantic = annotate_card(card, llm_call=llm_call)
        semantic["annotator_model"] = os.environ.get("LLM_MODEL", "unknown")
        store.update(card["id"], {"semantic": semantic})
        annotated += 1

    return annotated
