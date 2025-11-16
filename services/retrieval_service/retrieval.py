"""
Hybrid Retrieval System for SpeakSense
Combines BM25 keyword search and vector semantic search
"""
from typing import List, Dict, Tuple
import sys
from pathlib import Path
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.config_loader import config
from shared.database import db
from services.retrieval_service.bm25_search import bm25_search
from services.retrieval_service.vector_search import vector_search
from services.retrieval_service.preprocessing import preprocessor


class HybridRetrieval:
    """Hybrid retrieval system combining BM25 and vector search"""

    def __init__(self):
        self.config = config.get_section('retrieval')
        self.bm25_weight = self.config.get('bm25_weight', 0.3)
        self.vector_weight = self.config.get('vector_weight', 0.7)
        self.top_k_bm25 = self.config.get('top_k_bm25', 10)
        self.top_k_vector = self.config.get('top_k_vector', 10)

    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to [0, 1] range"""
        if not scores:
            return []

        min_score = min(scores)
        max_score = max(scores)

        if max_score == min_score:
            return [1.0] * len(scores)

        return [(s - min_score) / (max_score - min_score) for s in scores]

    def _fuse_scores(
        self,
        bm25_candidates: List[Tuple[str, float]],
        vector_candidates: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        """
        Fuse BM25 and vector search scores

        Args:
            bm25_candidates: List of (answer_id, bm25_score) tuples
            vector_candidates: List of (answer_id, vector_score) tuples

        Returns:
            List of (answer_id, fused_score) tuples, sorted by score
        """
        # Extract scores for normalization
        bm25_scores = [score for _, score in bm25_candidates]
        vector_scores = [score for _, score in vector_candidates]

        # Normalize scores
        norm_bm25 = self._normalize_scores(bm25_scores)
        norm_vector = self._normalize_scores(vector_scores)

        # Create score dictionaries
        bm25_dict = {answer_id: norm_score for (answer_id, _), norm_score in zip(bm25_candidates, norm_bm25)}
        vector_dict = {answer_id: norm_score for (answer_id, _), norm_score in zip(vector_candidates, norm_vector)}

        # Get all unique answer_ids
        all_answer_ids = set(bm25_dict.keys()) | set(vector_dict.keys())

        # Fuse scores
        fused_scores = []
        for answer_id in all_answer_ids:
            bm25_score = bm25_dict.get(answer_id, 0.0)
            vector_score = vector_dict.get(answer_id, 0.0)

            # Weighted combination
            fused_score = (
                self.bm25_weight * bm25_score +
                self.vector_weight * vector_score
            )

            fused_scores.append((answer_id, fused_score))

        # Sort by fused score
        fused_scores.sort(key=lambda x: x[1], reverse=True)

        return fused_scores

    def search(
        self,
        query: str,
        top_k: int = 1,
        language: str = None,
        method: str = "hybrid"
    ) -> List[Dict]:
        """
        Search FAQs using hybrid retrieval

        Args:
            query: Query text
            top_k: Number of results to return
            language: Language code for preprocessing
            method: Search method - "hybrid", "bm25", or "vector"

        Returns:
            List of search results with answers and audio paths
        """
        if not query.strip():
            return []

        # Preprocess query
        if language is None or language == "auto":
            language = preprocessor.detect_language(query)

        if method == "bm25":
            # BM25 only
            results = bm25_search.search(query, top_k, language)
            for r in results:
                r['matched_by'] = 'bm25'
                r['confidence'] = r['score']
            return results[:top_k]

        elif method == "vector":
            # Vector search only
            results = vector_search.search(query, top_k)
            for r in results:
                r['matched_by'] = 'vector'
                r['confidence'] = r['score']
            return results[:top_k]

        else:  # hybrid
            # Get candidates from both methods
            bm25_candidates = bm25_search.get_candidates(query, self.top_k_bm25, language)
            vector_candidates = vector_search.get_candidates(query, self.top_k_vector)

            if not bm25_candidates and not vector_candidates:
                return []

            # Fuse scores
            fused_scores = self._fuse_scores(bm25_candidates, vector_candidates)

            # Get top-k results
            top_results = fused_scores[:top_k]

            # Retrieve full FAQ information
            results = []
            for answer_id, score in top_results:
                faq = db.get_faq_by_id(answer_id)
                if faq:
                    results.append({
                        'answer_id': faq.answer_id,
                        'question': faq.question,
                        'answer': faq.answer,
                        'audio_path': faq.audio_path,
                        'language': faq.language,
                        'score': float(score),
                        'confidence': float(score),
                        'matched_by': 'hybrid'
                    })

            return results

    def get_best_answer(self, query: str, language: str = None, method: str = "hybrid") -> Dict:
        """
        Get the best matching answer for a query

        Args:
            query: Query text
            language: Language code
            method: Search method

        Returns:
            Best matching FAQ result or None
        """
        results = self.search(query, top_k=1, language=language, method=method)

        if results:
            return results[0]
        else:
            return None

    def rebuild_indices(self):
        """Rebuild both BM25 and vector search indices"""
        print("Rebuilding search indices...")
        bm25_search.rebuild_index()
        vector_search.rebuild_index()
        print("Search indices rebuilt successfully!")


# Global retrieval instance
retrieval = HybridRetrieval()
