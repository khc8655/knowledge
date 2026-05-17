"""
FTS5 full-text index for knowledge cards.
Uses SQLite FTS5 virtual table for fast keyword matching.
"""
import sqlite3
import json
import os
from typing import List, Dict, Any, Optional

from db.models import DB_PATH


FTS_TABLE = "cards_fts5"


class FTS5Index:
    def __init__(self):
        self.db_path = str(DB_PATH)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def build(self, cards_dir: str):
        """Build FTS5 index from all card JSON files in cards_dir."""
        conn = self._get_conn()
        try:
            conn.execute(f"DROP TABLE IF EXISTS {FTS_TABLE}")
            conn.execute(f"""
                CREATE VIRTUAL TABLE {FTS_TABLE} USING fts5(
                    card_id,
                    title,
                    body,
                    doc_file,
                    source_type,
                    path,
                    brand,
                    content_rowid='rowid',
                    tokenize='trigram'
                )
            """)

            cards = self._load_cards(cards_dir)
            for card in cards:
                semantic = card.get("semantic") or {}
                brand = card.get("brand", "") or semantic.get("brand", "")
                conn.execute(
                    f"INSERT INTO {FTS_TABLE} (card_id, title, body, doc_file, source_type, path, brand) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        card.get("id", ""),
                        card.get("title", ""),
                        card.get("body", ""),
                        card.get("doc_file", ""),
                        card.get("source_type", ""),
                        card.get("path", ""),
                        brand,
                    ),
                )
            conn.commit()
            return len(cards)
        finally:
            conn.close()

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search FTS5 index with the given query."""
        if not query.strip():
            return []

        conn = self._get_conn()
        try:
            # Check if table exists
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (FTS_TABLE,)
            ).fetchone()
            if not row:
                return []

            # FTS5 match query - trigram tokenizer handles CJK natively
            safe_query = query.replace('"', '""')
            # For multi-word queries (space-separated), use OR
            words = safe_query.split()
            if len(words) > 1:
                # Filter out words shorter than 3 chars (trigram minimum)
                valid_words = [w for w in words if len(w) >= 3]
                if not valid_words:
                    # Fall back to LIKE search for short queries
                    return self._like_search(conn, query, limit)
                fts_query = " OR ".join(f'"{w}"' for w in valid_words)
            else:
                if len(safe_query) < 3:
                    # Trigram needs 3+ chars, fall back to LIKE
                    return self._like_search(conn, query, limit)
                fts_query = f'"{safe_query}"'

            rows = conn.execute(
                f"""SELECT card_id, title, body, doc_file, source_type, path, brand,
                           rank
                    FROM {FTS_TABLE}
                    WHERE {FTS_TABLE} MATCH ?
                    ORDER BY rank
                    LIMIT ?""",
                (fts_query, limit),
            ).fetchall()

            results = []
            for row in rows:
                results.append({
                    "card_id": row["card_id"],
                    "title": row["title"],
                    "body": row["body"],
                    "doc_file": row["doc_file"],
                    "source_type": row["source_type"],
                    "path": row["path"],
                    "brand": row["brand"] or "",
                    "score": abs(row["rank"]),  # FTS5 rank is negative, lower = better
                })
            return results
        except Exception as e:
            print(f"[FTS5] Search error: {e}")
            return []
        finally:
            conn.close()

    def _like_search(self, conn, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback LIKE search for short Chinese queries."""
        rows = conn.execute(
            f"""SELECT card_id, title, body, doc_file, source_type, path, brand
                FROM {FTS_TABLE}
                WHERE title LIKE ? OR body LIKE ?
                LIMIT ?""",
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()

        results = []
        for row in rows:
            results.append({
                "card_id": row["card_id"],
                "title": row["title"],
                "body": row["body"],
                "doc_file": row["doc_file"],
                "source_type": row["source_type"],
                "path": row["path"],
                "brand": row["brand"] or "",
                "score": 0.5,  # Fixed score for LIKE matches
            })
        return results

    def _load_cards(self, cards_dir: str) -> List[Dict]:
        """Load all card JSON files from directory."""
        cards = []
        if not os.path.isdir(cards_dir):
            return cards
        for fname in os.listdir(cards_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(cards_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    card = json.load(f)
                cards.append(card)
            except (json.JSONDecodeError, IOError):
                continue
        return cards
