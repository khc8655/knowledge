"""Customer Reply Service — generates customer-facing replies from evidence."""
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from db.models import get_db

# Patterns for internal notes that must be stripped from customer replies
_INTERNAL_NOTE_PATTERNS = [
    re.compile(r'\[内部备注:[^\]]*\]'),
    re.compile(r'\[内部:[^\]]*\]'),
    re.compile(r'\[confidential:[^\]]*\]'),
]


def _sanitize_internal_notes(text: str) -> str:
    """Remove internal/confidential note tags from text."""
    for pat in _INTERNAL_NOTE_PATTERNS:
        text = pat.sub("", text)
    return text.strip()


def _build_uncertain_reply(tone: str) -> str:
    """Return a standard reply when no evidence is available."""
    if tone == "formal":
        return "关于您的问题，目前暂无相关资料可供参考，我们将尽快确认后回复您。"
    return "关于您的问题，目前暂无相关资料，待确认后回复。"


class ReplyService:
    """Generates customer-facing replies backed by evidence packs."""

    def __init__(self, conn=None):
        self.conn = conn

    def generate(
        self,
        customer_question: str,
        evidences: List[Dict[str, Any]],
        project_id: str = None,
        tone: str = "neutral",
        max_chars: int = 2000,
        allowed_evidence_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate a customer reply from evidence.

        Args:
            customer_question: The customer's question text.
            evidences: List of evidence dicts (from EvidencePackBuilder).
            project_id: Target presales project ID.
            tone: Reply tone — 'neutral', 'formal', 'friendly'.
            max_chars: Maximum character length for the reply.
            allowed_evidence_ids: If provided, only use these evidence IDs.

        Returns:
            Dict with: output_id, reply_text, internal_evidence, risk_summary.
        """
        # Filter evidences to allowed IDs if specified
        if allowed_evidence_ids is not None:
            allowed = set(allowed_evidence_ids)
            evidences = [e for e in evidences if e.get("id") in allowed]

        # No evidence -> uncertain reply
        if not evidences:
            reply_text = _build_uncertain_reply(tone)
            output_id = self._persist_output(
                project_id, customer_question, reply_text, [], {}
            )
            return {
                "output_id": output_id,
                "reply_text": reply_text,
                "internal_evidence": [],
                "risk_summary": {},
            }

        # Compute average confidence
        confidences = [e.get("confidence", 0) for e in evidences]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Build reply body from evidence claims
        reply_parts: List[str] = []
        internal_evidence: List[Dict[str, Any]] = []
        risk_flag_counts: Dict[str, int] = {}

        for ev in evidences:
            claim = ev.get("claim", "")
            body = ev.get("body", "")

            # Sanitize internal notes from body
            clean_body = _sanitize_internal_notes(body)
            clean_claim = _sanitize_internal_notes(claim)

            # Track what was removed for internal evidence
            original_body = body
            if clean_body != body.strip():
                internal_evidence.append({
                    "evidence_id": ev.get("id", ""),
                    "original_snippet": body[:200],
                    "sanitized_snippet": clean_body[:200],
                })

            # Collect risk flags
            raw_flags = ev.get("risk_flags", "[]")
            flags = json.loads(raw_flags) if isinstance(raw_flags, str) else raw_flags
            for f in flags:
                risk_flag_counts[f] = risk_flag_counts.get(f, 0) + 1

            if clean_claim:
                reply_parts.append(clean_claim)

        # Assemble reply
        if reply_parts:
            reply_text = "\n".join(f"- {p}" for p in reply_parts)
        else:
            reply_text = _build_uncertain_reply(tone)

        # Low confidence disclaimer
        if avg_confidence < 0.7:
            disclaimer = "\n\n注：以上信息供参考，具体以最新官方资料为准。"
            reply_text += disclaimer

        # Truncate if needed
        if len(reply_text) > max_chars:
            reply_text = reply_text[:max_chars - 3] + "..."

        risk_summary = {
            "total_evidence": len(evidences),
            "avg_confidence": round(avg_confidence, 2),
            "flag_counts": risk_flag_counts,
        }

        output_id = self._persist_output(
            project_id, customer_question, reply_text, evidences, risk_summary
        )

        return {
            "output_id": output_id,
            "reply_text": reply_text,
            "internal_evidence": internal_evidence,
            "risk_summary": risk_summary,
        }

    def _persist_output(
        self,
        project_id: str,
        question: str,
        reply_text: str,
        evidences: List[Dict[str, Any]],
        risk_summary: Dict[str, Any],
    ) -> str:
        """Save reply as a project_output record. Returns output_id."""
        output_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        content_json = json.dumps({
            "question": question,
            "evidence_count": len(evidences),
            "risk_summary": risk_summary,
        }, ensure_ascii=False)

        conn = self.conn or get_db()
        should_close = self.conn is None
        try:
            conn.execute(
                """
                INSERT INTO project_outputs
                    (id, project_id, output_type, title, status,
                     content_md, content_json, version, created_at, updated_at)
                VALUES (?, ?, 'reply', ?, 'draft', ?, ?, 1, ?, ?)
                """,
                (output_id, project_id or 'standalone', question[:200], reply_text, content_json, now, now),
            )
            conn.commit()
        finally:
            if should_close:
                conn.close()

        return output_id
