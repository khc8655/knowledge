"""
Unified search entry point with intent classification.
Fuses FTS5, BM25, and Vector search results with weighted scoring.
"""
import os
import re
from typing import List, Dict, Any, Optional

from .fts5 import FTS5Index
from .bm25 import BM25Index
from .vector import VectorIndex


# Intent classification keywords (from wiki/query_unified.py)
PRICE_KWS = ['价格', '报价', '多少钱', '费用', '成本']
TENDER_KWS = ['招标', '投标', '可研']
SPEC_KWS = ['规格', '接口', '编解码', '输入', '输出', '分辨率', '像素', '参数', '介绍', '详情', '功能']
COMPARE_KWS = ['对比', '比较', '区别', '差异', 'vs']
ACCESSORY_KWS = ['配件', '附件', '可用配件']
EOL_KWS = ['停产', '替代', '退市', 'EOL']
PPT_KWS = ['PPT', '幻灯片', '页面', 'ppt']
PROPOSAL_KWS = ['方案', '可研']
UPDATE_KWS = ['迭代', '新功能', '版本更新', '发版', '更新说明']

# Model number pattern
MODEL_RE = re.compile(
    r'(AE\d{3}[A-Z]?|XE\d{3}[A-Z]?|GE\d{3}[A-Z]?|PE\d{4}|TP\d{3}(?:-[A-Z])?|'
    r'MX\d{2}|AC\d{2}|NC\d{2}|NP\d{2}(?:V?\d+)?|ME\d{3,4}|XM\d{4})',
    re.I
)

# Source type routing weights
INTENT_WEIGHTS = {
    'price': {'fts5': 0.5, 'bm25': 0.3, 'vector': 0.2},      # Excel精确匹配
    'tender': {'fts5': 0.4, 'bm25': 0.35, 'vector': 0.25},    # 招标参数
    'compare': {'fts5': 0.35, 'bm25': 0.35, 'vector': 0.3},   # 对比需要多源
    'eol': {'fts5': 0.5, 'bm25': 0.3, 'vector': 0.2},         # 停产信息精确
    'accessory': {'fts5': 0.45, 'bm25': 0.3, 'vector': 0.25}, # 配件精确
    'proposal': {'fts5': 0.2, 'bm25': 0.4, 'vector': 0.4},    # 方案语义检索
    'ppt': {'fts5': 0.3, 'bm25': 0.35, 'vector': 0.35},       # PPT检索
    'default': {'fts5': 0.3, 'bm25': 0.35, 'vector': 0.35},   # 默认混合
}

# Source type boost for specific intents
SOURCE_TYPE_BOOST = {
    'price': {'excel': 2.0, 'word': 0.8, 'ppt': 0.5},
    'tender': {'excel': 1.5, 'word': 1.2, 'ppt': 0.8},
    'eol': {'excel': 2.0, 'word': 0.8},
    'accessory': {'excel': 1.5, 'word': 1.0},
    'ppt': {'ppt': 2.0, 'word': 0.8, 'excel': 0.5},
    'default': {},
}


def classify_intent(query: str) -> str:
    """Classify query intent for routing."""
    q_lower = query.lower()

    if any(kw in q_lower for kw in PRICE_KWS):
        return 'price'
    if any(kw in q_lower for kw in EOL_KWS):
        return 'eol'
    if any(kw in q_lower for kw in ACCESSORY_KWS):
        return 'accessory'
    if any(kw in q_lower for kw in COMPARE_KWS):
        return 'compare'
    if any(kw in q_lower for kw in TENDER_KWS):
        return 'tender'
    if any(kw in q_lower for kw in PPT_KWS):
        return 'ppt'
    if any(kw in q_lower for kw in PROPOSAL_KWS):
        return 'proposal'

    return 'default'


def unified_search(
    query: str,
    limit: int = 10,
    data_dir: str = None,
) -> Dict[str, Any]:
    """
    Unified search: classify intent → route to weighted fusion → return results.
    """
    if not query.strip():
        return {"results": [], "total": 0, "intent": "empty"}

    intent = classify_intent(query)
    weights = INTENT_WEIGHTS.get(intent, INTENT_WEIGHTS['default'])
    source_boost = SOURCE_TYPE_BOOST.get(intent, SOURCE_TYPE_BOOST['default'])

    if data_dir is None:
        data_dir = os.environ.get("KB_DATA_DIR", "./data")

    cards_dir = os.path.join(data_dir, "cards", "sections")
    index_dir = os.path.join(data_dir, "indexes")

    # Run all three searchers
    fts5_results = []
    bm25_results = []
    vector_results = []

    # FTS5 search
    try:
        fts5 = FTS5Index()
        fts5_results = fts5.search(query, limit=limit * 3)
    except Exception as e:
        print(f"[Search] FTS5 error: {e}")

    # BM25 search
    try:
        bm25 = BM25Index()
        bm25_persist = os.path.join(index_dir, "bm25.pkl")
        if bm25.load(bm25_persist):
            bm25_results = bm25.search(query, top_k=limit * 3)
        else:
            # Build on the fly if no persisted index
            bm25.build(cards_dir, persist_path=bm25_persist)
            bm25_results = bm25.search(query, top_k=limit * 3)
    except Exception as e:
        print(f"[Search] BM25 error: {e}")

    # Vector search
    try:
        vector = VectorIndex()
        vector_persist = os.path.join(index_dir, "vector")
        if vector.load(vector_persist):
            from config import AppConfig
            cfg = AppConfig()
            api_key = cfg.get("llm_api_key")
            model = cfg.get("embedding_model", "Pro/BAAI/bge-m3")
            vector_results = vector.search(query, top_k=limit * 3, api_key=api_key, model=model)
        # Skip vector if no persisted index (too slow to build on the fly per query)
    except Exception as e:
        print(f"[Search] Vector error: {e}")

    # Fuse results
    combined = _fuse_results(
        fts5_results, bm25_results, vector_results,
        weights, source_boost, limit
    )

    return {
        "results": combined,
        "total": len(combined),
        "intent": intent,
        "sources": {
            "fts5": len(fts5_results),
            "bm25": len(bm25_results),
            "vector": len(vector_results),
        },
    }


def _fuse_results(
    fts5_results: List[Dict],
    bm25_results: List[Dict],
    vector_results: List[Dict],
    weights: Dict[str, float],
    source_boost: Dict[str, float],
    limit: int,
) -> List[Dict]:
    """Fuse results from three searchers with weighted scoring."""
    # Normalize scores within each source
    fts5_scores = _normalize_scores(fts5_results)
    bm25_scores = _normalize_scores(bm25_results)
    vector_scores = _normalize_scores(vector_results)

    # Collect all unique card_ids
    all_cards = {}
    for results, key in [(fts5_results, 'fts5'), (bm25_results, 'bm25'), (vector_results, 'vector')]:
        score_map = {'fts5': fts5_scores, 'bm25': bm25_scores, 'vector': vector_scores}[key]
        for r in results:
            cid = r.get("card_id", "")
            if not cid:
                continue
            if cid not in all_cards:
                all_cards[cid] = {
                    "card_id": cid,
                    "title": r.get("title", ""),
                    "body": r.get("body", ""),
                    "doc_file": r.get("doc_file", ""),
                    "source_type": r.get("source_type", ""),
                    "path": r.get("path", ""),
                    "brand": r.get("brand", ""),
                    "scores": {},
                }
            all_cards[cid]["scores"][key] = score_map.get(cid, 0.0)

    # Compute weighted fusion score
    for cid, card in all_cards.items():
        scores = card["scores"]
        fused = 0.0
        for source, weight in weights.items():
            fused += weight * scores.get(source, 0.0)

        # Apply source type boost
        st = card.get("source_type", "")
        if st in source_boost:
            fused *= source_boost[st]

        card["hit_rate"] = round(fused, 4)
        del card["scores"]

    # Sort and limit
    results = sorted(all_cards.values(), key=lambda x: -x["hit_rate"])
    return results[:limit]


def _normalize_scores(results: List[Dict]) -> Dict[str, float]:
    """Normalize scores to [0, 1] range."""
    if not results:
        return {}

    scores = {r.get("card_id", ""): r.get("score", 0) for r in results}
    if not scores:
        return {}

    max_score = max(scores.values())
    min_score = min(scores.values())
    score_range = max_score - min_score if max_score > min_score else 1.0

    return {cid: (s - min_score) / score_range for cid, s in scores.items()}
