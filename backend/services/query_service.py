import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from db.models import get_db


def normalize_query(query: str) -> str:
    q = query.strip()
    q = q.replace("　", " ")
    while "  " in q:
        q = q.replace("  ", " ")
    return q


def query_hash(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def search(query: str, limit: int = 10) -> Dict[str, Any]:
    q = normalize_query(query)
    if not q:
        return {"error": "INVALID_QUERY", "results": []}
    if len(q) > 500:
        return {"error": "INVALID_QUERY", "results": []}

    qhash = query_hash(q)
    conn = get_db()

    try:
        cache = conn.execute(
            "SELECT source_type, models FROM route_cache WHERE query_hash = ?",
            (qhash,)
        ).fetchone()

        route_source = "cache" if cache else "rule"

        mapping = conn.execute(
            "SELECT expected_route, confidence FROM route_mappings WHERE query_hash = ? AND is_active = 1",
            (qhash,)
        ).fetchone()

        if mapping and mapping["confidence"] >= 0.7:
            route_source = "feedback_learned"

    finally:
        conn.close()

    wiki_dir = os.environ.get("WIKI_DIR", "/home/jjb/wiki")
    script = os.path.join(wiki_dir, "query_unified.py")

    try:
        result = subprocess.run(
            ["python3", script, q, "--json", "--limit", str(limit)],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=wiki_dir,
        )

        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
        else:
            data = {"results": [], "total": 0}

    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        data = {"results": [], "total": 0}

    data["route_source"] = route_source
    data["query_hash"] = qhash

    if data.get("total", 0) > 0 and route_source in ("rule", "feedback_learned"):
        _update_cache(qhash, q, data)

    return data


def _update_cache(qhash: str, query: str, data: Dict):
    conn = get_db()
    try:
        source_type = data.get("results", [{}])[0].get("source_type", "knowledge") if data.get("results") else "knowledge"
        models = json.dumps(data.get("models", []))
        conn.execute(
            """INSERT OR REPLACE INTO route_cache (query_hash, query_text, source_type, models, hit_count, last_hit_at)
               VALUES (?, ?, ?, ?,
                       COALESCE((SELECT hit_count FROM route_cache WHERE query_hash = ?), 0) + 1,
                       datetime('now'))""",
            (qhash, query, source_type, models, qhash)
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def submit_feedback(query_text: str, card_id: str, feedback: str, route_used: str):
    qhash = query_hash(normalize_query(query_text))
    conn = get_db()
    try:
        import uuid
        query_id = str(uuid.uuid4())[:8]
        conn.execute(
            """INSERT INTO query_feedback (query_id, query_text, card_id, feedback, route_used, route_source)
               VALUES (?, ?, ?, ?, ?, 'user')""",
            (query_id, query_text, card_id, feedback, route_used)
        )

        mapping = conn.execute(
            "SELECT * FROM route_mappings WHERE query_hash = ?", (qhash,)
        ).fetchone()

        if not mapping:
            conn.execute(
                """INSERT INTO route_mappings (query_pattern, query_hash, expected_route, confidence,
                   positive_count, negative_count, total_count, source)
                   VALUES (?, ?, ?, 0.5, 0, 0, 0, 'rule')""",
                (query_text, qhash, route_used)
            )
            mapping = conn.execute(
                "SELECT * FROM route_mappings WHERE query_hash = ?", (qhash,)
            ).fetchone()

        pos = mapping["positive_count"]
        neg = mapping["negative_count"]
        if feedback == "positive":
            pos += 1
        else:
            neg += 1

        total = pos + neg
        confidence = pos / total if total > 0 else 0.5

        is_active = 0
        source = mapping["source"]
        if confidence >= 0.7 and total >= 5:
            is_active = 1
            source = "feedback_learned"
        elif confidence < 0.3 and total >= 5:
            is_active = 0
        elif confidence < 0.5 and total >= 10:
            is_active = 0

        conn.execute(
            """UPDATE route_mappings SET
               positive_count=?, negative_count=?, total_count=?,
               confidence=?, is_active=?, source=?, updated_at=datetime('now')
               WHERE query_hash=?""",
            (pos, neg, total, confidence, is_active, source, qhash)
        )
        conn.commit()
    finally:
        conn.close()
