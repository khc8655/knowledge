import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


class CardStore:
    def __init__(self, data_dir: str):
        self._sections_dir = os.path.join(data_dir, "cards", "sections")
        os.makedirs(self._sections_dir, exist_ok=True)

    def _card_path(self, card_id: str) -> str:
        return os.path.join(self._sections_dir, f"{card_id}.json")

    def get(self, card_id: str) -> Optional[Dict]:
        path = self._card_path(card_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, card: Dict[str, Any]):
        path = self._card_path(card["id"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(card, f, ensure_ascii=False, indent=2)

    def update(self, card_id: str, updates: Dict[str, Any]) -> bool:
        card = self.get(card_id)
        if not card:
            return False
        card.update(updates)
        card["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save(card)
        return True

    def delete(self, card_id: str) -> bool:
        path = self._card_path(card_id)
        if not os.path.exists(path):
            return False
        os.remove(path)
        return True

    def list_cards(
        self,
        source_type: str = None,
        intent_tag: str = None,
        quality_tier: str = None,
        search: str = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 50,
    ) -> Dict:
        cards = []
        for fname in os.listdir(self._sections_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._sections_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    card = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

            if source_type and card.get("source_type") != source_type:
                continue
            if intent_tag:
                semantic = card.get("semantic") or {}
                tags = semantic.get("intent_tags", [])
                if intent_tag not in tags:
                    continue
            if quality_tier:
                semantic = card.get("semantic") or {}
                if semantic.get("quality_tier") != quality_tier:
                    continue
            if search:
                search_lower = search.lower()
                body = card.get("body", "").lower()
                title = card.get("title", "").lower()
                if search_lower not in body and search_lower not in title:
                    continue

            cards.append(card)

        reverse = sort_order == "desc"
        cards.sort(key=lambda c: c.get(sort_by, ""), reverse=reverse)

        total = len(cards)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": cards[start:end],
        }

    def stats(self) -> Dict:
        by_source = {}
        by_tier = {}
        total = 0
        for fname in os.listdir(self._sections_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._sections_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    card = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue
            total += 1
            st = card.get("source_type", "unknown")
            by_source[st] = by_source.get(st, 0) + 1
            semantic = card.get("semantic") or {}
            tier = semantic.get("quality_tier", "unknown")
            by_tier[tier] = by_tier.get(tier, 0) + 1

        return {
            "total": total,
            "by_source_type": by_source,
            "by_quality_tier": by_tier,
        }

    def save_batch(self, cards: List[Dict[str, Any]]):
        for card in cards:
            self.save(card)
