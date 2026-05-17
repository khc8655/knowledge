"""
Vector index for knowledge cards.
Uses SiliconFlow embedding API (bge-m3) and numpy for cosine similarity.
"""
import json
import os
import time
import requests
import numpy as np
from typing import List, Dict, Any, Optional, Tuple


class VectorIndex:
    """Vector search using SiliconFlow embeddings."""

    def __init__(self):
        self._matrix: Optional[np.ndarray] = None
        self._card_ids: List[str] = []
        self._cards: List[Dict] = []
        self._normalized: Optional[np.ndarray] = None
        self._built = False

    def build(self, cards_dir: str, persist_dir: str = None, api_key: str = None,
              model: str = "Pro/BAAI/bge-m3", batch_size: int = 32) -> int:
        """Build vector index from card JSON files."""
        cards = self._load_cards(cards_dir)
        if not cards:
            return 0

        self._cards = cards
        self._card_ids = [c.get("id", str(i)) for i, c in enumerate(cards)]

        # Build texts to embed
        texts = [self._build_card_text(c) for c in cards]

        # Get embeddings
        vectors = self._embed_batch(texts, api_key=api_key, model=model, batch_size=batch_size)
        if vectors is None or len(vectors) == 0:
            print("[Vector] Embedding generation failed")
            return 0

        self._matrix = np.array(vectors, dtype=np.float32)
        # Normalize for cosine similarity
        norms = np.linalg.norm(self._matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._normalized = self._matrix / norms
        self._built = True

        if persist_dir:
            self._persist(persist_dir)

        return len(cards)

    def search(self, query: str, top_k: int = 20, api_key: str = None,
               model: str = "Pro/BAAI/bge-m3") -> List[Dict[str, Any]]:
        """Search for similar cards using cosine similarity."""
        if not self._built or not query.strip():
            return []

        query_vec = self._get_embedding(query, api_key=api_key, model=model)
        if query_vec is None:
            return []

        q_norm = query_vec / (np.linalg.norm(query_vec) or 1.0)
        scores = self._normalized @ q_norm

        top_k = min(top_k, len(scores))
        if top_k == 0:
            return []

        if len(scores) <= top_k:
            indices = np.argsort(-scores)
        else:
            k_for_partition = min(top_k, len(scores) - 1)
            indices = np.argpartition(-scores, k_for_partition)[:top_k]
            indices = indices[np.argsort(-scores[indices])]

        results = []
        for i in indices:
            if scores[i] <= 0:
                break
            card = self._cards[i]
            results.append({
                "card_id": card.get("id", ""),
                "title": card.get("title", ""),
                "body": card.get("body", ""),
                "doc_file": card.get("doc_file", ""),
                "source_type": card.get("source_type", ""),
                "path": card.get("path", ""),
                "score": round(float(scores[i]), 4),
            })

        return results

    def _get_embedding(self, text: str, api_key: str = None,
                       model: str = "Pro/BAAI/bge-m3") -> Optional[np.ndarray]:
        """Get embedding for a single text."""
        vectors = self._embed_batch([text], api_key=api_key, model=model, batch_size=1)
        if vectors and len(vectors) > 0:
            return np.array(vectors[0], dtype=np.float32)
        return None

    def _embed_batch(self, texts: List[str], api_key: str = None,
                     model: str = "Pro/BAAI/bge-m3",
                     batch_size: int = 32) -> Optional[List[List[float]]]:
        """Embed a batch of texts using SiliconFlow API."""
        if not api_key:
            from config import AppConfig
            cfg = AppConfig()
            api_key = cfg.get("llm_api_key")

        url = "https://api.siliconflow.cn/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        all_vectors = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for attempt in range(3):
                try:
                    r = requests.post(
                        url,
                        headers=headers,
                        json={
                            "model": model,
                            "input": batch,
                            "encoding_format": "float",
                        },
                        timeout=60,
                    )
                    data = r.json()

                    if r.status_code == 429:
                        wait = float(data.get("retry_after", 5))
                        print(f"[Vector] Rate limited, waiting {wait}s")
                        time.sleep(wait)
                        continue

                    if r.status_code != 200:
                        print(f"[Vector] API error {r.status_code}: {data.get('message', data)}")
                        if attempt < 2:
                            time.sleep(2 ** attempt)
                            continue
                        return None

                    results = data.get("data", [])
                    vectors = [item.get("embedding", []) for item in
                               sorted(results, key=lambda x: x.get("index", 0))]
                    all_vectors.extend(vectors)
                    break

                except requests.Timeout:
                    print(f"[Vector] Timeout batch {i}-{i + len(batch)}")
                    if attempt < 2:
                        time.sleep(2)
                        continue
                    return None
                except Exception as e:
                    print(f"[Vector] Error: {e}")
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    return None

        return all_vectors if all_vectors else None

    def _build_card_text(self, card: Dict) -> str:
        """Build text to embed from a card (max ~450 chars for token limit)."""
        semantic = card.get("semantic") or {}
        parts = []

        title = card.get("title", "")
        if title:
            parts.append(title)

        brand = card.get("brand", "") or semantic.get("brand", "")
        if brand:
            parts.append(brand)

        for key in ["intent_tags", "concept_tags", "keywords"]:
            tags = semantic.get(key, [])
            if tags:
                parts.append(";".join(tags[:5]))

        body = card.get("body", "")
        if body:
            parts.append(body[:200])

        text = " ".join(parts)
        return text[:450]

    def _persist(self, persist_dir: str):
        """Save index to disk."""
        os.makedirs(persist_dir, exist_ok=True)
        np.save(os.path.join(persist_dir, "embeddings.npy"), self._matrix)
        with open(os.path.join(persist_dir, "card_ids.json"), "w") as f:
            json.dump(self._card_ids, f)
        with open(os.path.join(persist_dir, "cards.json"), "w", encoding="utf-8") as f:
            json.dump(self._cards, f, ensure_ascii=False)

    def load(self, persist_dir: str) -> bool:
        """Load index from disk."""
        try:
            matrix_path = os.path.join(persist_dir, "embeddings.npy")
            ids_path = os.path.join(persist_dir, "card_ids.json")
            cards_path = os.path.join(persist_dir, "cards.json")

            if not all(os.path.exists(p) for p in [matrix_path, ids_path, cards_path]):
                return False

            self._matrix = np.load(matrix_path)
            with open(ids_path, "r") as f:
                self._card_ids = json.load(f)
            with open(cards_path, "r", encoding="utf-8") as f:
                self._cards = json.load(f)

            norms = np.linalg.norm(self._matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self._normalized = self._matrix / norms
            self._built = True
            return True
        except Exception as e:
            print(f"[Vector] Failed to load index: {e}")
            return False

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
