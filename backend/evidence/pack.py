"""Evidence Pack Builder — converts knowledge cards into evidence items for presales projects."""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from db.models import get_db

# Card type -> evidence type mapping
_CARD_TYPE_MAP = {
    "price": "price",
    "parameter": "parameter",
    "capability": "parameter",
    "scenario": "scenario",
    "architecture": "architecture",
    "update": "update",
}

# Quality tier -> confidence score
_CONFIDENCE_MAP = {
    "high": 0.95,
    "medium": 0.75,
    "low": 0.4,
    "placeholder": 0.1,
}


class EvidencePackBuilder:
    """Builds, persists, and manages evidence packs from knowledge cards."""

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def build(
        self,
        cards: List[Dict[str, Any]],
        task_type: str,
        project_id: str,
    ) -> List[Dict[str, Any]]:
        """Convert card dicts into evidence item dicts ready for persistence.

        Args:
            cards: List of card dictionaries (from CardStore).
            task_type: The task context (e.g. 'proposal', 'tender', 'reply').
            project_id: Target presales project ID.

        Returns:
            List of evidence dicts (not yet persisted).
        """
        evidences: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc).isoformat()

        for card in cards:
            evidence_type = self._resolve_evidence_type(card)
            confidence = self._compute_confidence(card)
            freshness = self._compute_freshness(card)
            risk_flags = self._compute_risk_flags(card)

            evidence = {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "source_card_id": card.get("id", ""),
                "source_type": card.get("source_type", "txt"),
                "evidence_type": evidence_type,
                "claim": self._extract_claim(card),
                "body": card.get("body", ""),
                "source": self._extract_source(card),
                "confidence": confidence,
                "freshness": freshness,
                "risk_flags": json.dumps(risk_flags),
                "created_by_task_id": None,
                "created_at": now,
                "archived_at": None,
            }
            evidences.append(evidence)

        return evidences

    # ------------------------------------------------------------------
    # Persist
    # ------------------------------------------------------------------
    def persist(
        self,
        evidences: List[Dict[str, Any]],
        project_id: str,
        created_by_task_id: Optional[str] = None,
    ) -> str:
        """Save evidence items to the evidence_packs table.

        Args:
            evidences: Evidence dicts (output of build()).
            project_id: Target project ID.
            created_by_task_id: Optional task ID that created these evidences.

        Returns:
            The pack_id (ID of the first inserted evidence, for grouping).
        """
        conn = get_db()
        try:
            cur = conn.cursor()
            pack_id: Optional[str] = None
            now = datetime.now(timezone.utc).isoformat()

            for ev in evidences:
                eid = ev.get("id") or str(uuid.uuid4())
                if pack_id is None:
                    pack_id = eid

                cur.execute(
                    """
                    INSERT INTO evidence_packs
                        (id, project_id, source_card_id, source_type, evidence_type,
                         claim, body, source, confidence, freshness, risk_flags,
                         created_by_task_id, created_at, archived_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        eid,
                        ev.get("project_id", project_id),
                        ev["source_card_id"],
                        ev["source_type"],
                        ev["evidence_type"],
                        ev["claim"],
                        ev["body"],
                        ev["source"],
                        ev["confidence"],
                        ev["freshness"],
                        ev["risk_flags"],
                        created_by_task_id,
                        ev.get("created_at", now),
                        ev.get("archived_at"),
                    ),
                )

            conn.commit()
            return pack_id
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Get
    # ------------------------------------------------------------------
    def get(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single evidence item by ID.

        Args:
            evidence_id: The evidence pack ID.

        Returns:
            Evidence dict or None if not found.
        """
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM evidence_packs WHERE id = ?", (evidence_id,))
            row = cur.fetchone()
            if row is None:
                return None
            return dict(row)
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # List by project
    # ------------------------------------------------------------------
    def list_by_project(
        self,
        project_id: str,
        include_archived: bool = False,
    ) -> List[Dict[str, Any]]:
        """List evidence for a project.

        Args:
            project_id: Target project ID.
            include_archived: If True, include soft-deleted evidence.

        Returns:
            List of evidence dicts.
        """
        conn = get_db()
        try:
            cur = conn.cursor()
            if include_archived:
                cur.execute(
                    "SELECT * FROM evidence_packs WHERE project_id = ? ORDER BY created_at DESC",
                    (project_id,),
                )
            else:
                cur.execute(
                    "SELECT * FROM evidence_packs WHERE project_id = ? AND archived_at IS NULL ORDER BY created_at DESC",
                    (project_id,),
                )
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Archive
    # ------------------------------------------------------------------
    def archive(self, evidence_id: str) -> bool:
        """Soft-delete an evidence item by setting archived_at.

        Args:
            evidence_id: The evidence pack ID.

        Returns:
            True if the item was found and archived, False otherwise.
        """
        conn = get_db()
        try:
            cur = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cur.execute(
                "UPDATE evidence_packs SET archived_at = ? WHERE id = ? AND archived_at IS NULL",
                (now, evidence_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    # ==================================================================
    # Private helpers
    # ==================================================================
    @staticmethod
    def _resolve_evidence_type(card: Dict[str, Any]) -> str:
        """Map card type to evidence type."""
        if card.get("report_meta"):
            return "report"
        card_type = card.get("card_type", card.get("type", ""))
        return _CARD_TYPE_MAP.get(card_type, "parameter")

    @staticmethod
    def _compute_confidence(card: Dict[str, Any]) -> float:
        """Derive confidence from quality_tier."""
        semantic = card.get("semantic") or {}
        tier = semantic.get("quality_tier", "low")
        return _CONFIDENCE_MAP.get(tier, 0.4)

    @staticmethod
    def _compute_freshness(card: Dict[str, Any]) -> str:
        """Determine freshness: current / expired / history / unknown."""
        report_meta = card.get("report_meta")
        if report_meta and isinstance(report_meta, dict):
            valid_to = report_meta.get("valid_to")
            if valid_to:
                try:
                    if datetime.fromisoformat(valid_to.replace("Z", "+00:00")) < datetime.now(timezone.utc):
                        return "expired"
                except (ValueError, TypeError):
                    pass

        # Check is_current flag (e.g. on uploaded_files linked cards)
        if card.get("is_current") is False or card.get("is_current") == 0:
            return "history"

        if card.get("is_current") is True or card.get("is_current") == 1:
            return "current"

        return "unknown"

    @staticmethod
    def _compute_risk_flags(card: Dict[str, Any]) -> List[str]:
        """Infer risk flags from card metadata."""
        flags: List[str] = []

        # Expired certificate check
        report_meta = card.get("report_meta")
        if report_meta and isinstance(report_meta, dict):
            valid_to = report_meta.get("valid_to")
            if valid_to:
                try:
                    if datetime.fromisoformat(valid_to.replace("Z", "+00:00")) < datetime.now(timezone.utc):
                        flags.append("expired_certificate")
                except (ValueError, TypeError):
                    pass

        # Scan unavailable
        if card.get("scan_available") is False:
            flags.append("scan_unavailable")

        # Unannotated — no semantic analysis or empty tags
        semantic = card.get("semantic")
        if not semantic or not isinstance(semantic, dict):
            flags.append("unannotated")
        elif not semantic.get("intent_tags") and not semantic.get("quality_tier"):
            flags.append("unannotated")

        return flags

    @staticmethod
    def _extract_claim(card: Dict[str, Any]) -> str:
        """Build a short claim from the card title."""
        return card.get("title", card.get("body", "")[:200])

    @staticmethod
    def _extract_source(card: Dict[str, Any]) -> str:
        """Derive a human-readable source reference."""
        parts = []
        if card.get("doc_file"):
            parts.append(card["doc_file"])
        if card.get("path"):
            parts.append(card["path"])
        return " > ".join(parts) if parts else card.get("source_type", "unknown")
