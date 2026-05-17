"""
BM25 index for knowledge cards.
Pure Python implementation with Chinese bigram tokenization.
Based on wiki/lib/retrieval_bm25.py algorithm.
"""
import json
import math
import os
import pickle
import re
from typing import List, Dict, Any, Tuple, Optional


class BM25Index:
    """BM25 retrieval for knowledge base cards."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._corpus_tokens: List[List[str]] = []
        self._card_ids: List[str] = []
        self._cards: List[Dict] = []
        self._doc_freqs: Dict[str, int] = {}
        self._avg_dl: float = 0.0
        self._doc_lengths: List[int] = []
        self._idf: Dict[str, float] = {}
        self._built = False

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize Chinese text using character-based + bigram approach."""
        if not text:
            return []
        # Protect special terms: H.264, H.265, H.323 etc.
        text = re.sub(r'([A-Za-z])\.(\d)', r'\1DOT\2', text)
        # Insert space at Chinese/English/digit boundaries
        text = re.sub(r'([a-zA-Z0-9])([一-鿿])', r'\1 \2', text)
        text = re.sub(r'([一-鿿])([a-zA-Z0-9])', r'\1 \2', text)
        # Clean special chars (keep DOT placeholder)
        text = re.sub(r'[^一-龥a-zA-Z0-9DOT]', ' ', text)
        # Restore dots
        text = text.replace('DOT', '.')

        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都',
                     '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会',
                     '着', '没有', '看', '好', '自己', '这', '为', '与', '及', '等', '或'}

        tokens = []
        words = text.split()

        for word in words:
            word = word.strip()
            if len(word) == 0:
                continue
            elif len(word) == 1:
                if word not in stopwords:
                    tokens.append(word.lower())
            elif len(word) == 2:
                tokens.append(word.lower())
            else:
                # Chinese: extract bigrams for better recall
                chinese_chars = re.findall(r'[一-龥]', word)
                if len(chinese_chars) >= 2:
                    for i in range(len(chinese_chars) - 1):
                        bigram = chinese_chars[i] + chinese_chars[i + 1]
                        if bigram not in stopwords:
                            tokens.append(bigram)
                    # Also add individual chars for short-word matching
                    for ch in chinese_chars:
                        if ch not in stopwords:
                            tokens.append(ch)
                # English/digit tokens
                eng_parts = re.findall(r'[a-zA-Z0-9.]+', word)
                for part in eng_parts:
                    tokens.append(part.lower())
                    # Add sub-tokens for model numbers like AE800
                    sub = re.findall(r'[a-zA-Z]+|\d+', part)
                    for s in sub:
                        if len(s) >= 2:
                            tokens.append(s.lower())

        return tokens

    def build(self, cards_dir: str, persist_path: str = None):
        """Build BM25 index from card JSON files."""
        cards = self._load_cards(cards_dir)
        self._build_from_cards(cards)

        if persist_path:
            self._persist(persist_path)

        return len(cards)

    def _build_from_cards(self, cards: List[Dict]):
        """Build index from a list of card dicts."""
        self._cards = cards
        self._card_ids = [c.get("id", str(i)) for i, c in enumerate(cards)]

        # Build corpus tokens
        self._corpus_tokens = []
        for card in cards:
            text = f"{card.get('title', '')} {card.get('body', '')}"
            self._corpus_tokens.append(self._tokenize(text))

        # Compute document lengths
        self._doc_lengths = [len(tokens) for tokens in self._corpus_tokens]
        self._avg_dl = sum(self._doc_lengths) / max(1, len(self._doc_lengths))

        # Compute document frequencies
        self._doc_freqs = {}
        for tokens in self._corpus_tokens:
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self._doc_freqs[t] = self._doc_freqs.get(t, 0) + 1

        # Compute IDF
        n = len(self._corpus_tokens)
        self._idf = {}
        for term, freq in self._doc_freqs.items():
            self._idf[term] = math.log((n - freq + 0.5) / (freq + 0.5) + 1)

        self._built = True

    def search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Search with BM25 scoring."""
        if not self._built or not query.strip():
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = []
        for i, doc_tokens in enumerate(self._corpus_tokens):
            score = self._score(query_tokens, doc_tokens, i)
            if score > 0:
                scores.append((i, score))

        scores.sort(key=lambda x: -x[1])
        results = []
        for idx, score in scores[:top_k]:
            card = self._cards[idx]
            semantic = card.get("semantic") or {}
            results.append({
                "card_id": card.get("id", ""),
                "title": card.get("title", ""),
                "body": card.get("body", ""),
                "doc_file": card.get("doc_file", ""),
                "source_type": card.get("source_type", ""),
                "path": card.get("path", ""),
                "brand": card.get("brand", "") or semantic.get("brand", ""),
                "score": round(score, 4),
            })

        return results

    def _score(self, query_tokens: List[str], doc_tokens: List[str], doc_idx: int) -> float:
        """Compute BM25 score for a document."""
        dl = self._doc_lengths[doc_idx]
        doc_term_freq = {}
        for t in doc_tokens:
            doc_term_freq[t] = doc_term_freq.get(t, 0) + 1

        score = 0.0
        for qt in query_tokens:
            if qt not in doc_term_freq:
                continue
            tf = doc_term_freq[qt]
            idf = self._idf.get(qt, 0)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * dl / max(1, self._avg_dl))
            score += idf * numerator / denominator

        return score

    def _persist(self, path: str):
        """Save index to disk."""
        data = {
            "corpus_tokens": self._corpus_tokens,
            "card_ids": self._card_ids,
            "cards": self._cards,
            "doc_freqs": self._doc_freqs,
            "avg_dl": self._avg_dl,
            "doc_lengths": self._doc_lengths,
            "idf": self._idf,
        }
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load(self, path: str) -> bool:
        """Load index from disk."""
        if not os.path.exists(path):
            return False
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            self._corpus_tokens = data["corpus_tokens"]
            self._card_ids = data["card_ids"]
            self._cards = data["cards"]
            self._doc_freqs = data["doc_freqs"]
            self._avg_dl = data["avg_dl"]
            self._doc_lengths = data["doc_lengths"]
            self._idf = data["idf"]
            self._built = True
            return True
        except Exception as e:
            print(f"[BM25] Failed to load index: {e}")
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
