"""
BM25 Keyword Search for SpeakSense
Classic information retrieval using BM25 algorithm
"""
from rank_bm25 import BM25Okapi
from typing import List, Dict, Tuple
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.database import db
from services.retrieval_service.preprocessing import preprocessor


class BM25Search:
    """BM25-based keyword search for FAQ retrieval"""

    def __init__(self):
        self.corpus = []  # List of FAQ entries
        self.tokenized_corpus = []  # Tokenized questions
        self.bm25 = None
        self.initialized = False

    def initialize(self):
        """Initialize BM25 index with FAQ data"""
        # Get all FAQs from database
        faqs = db.get_all_faqs()

        if not faqs:
            print("Warning: No FAQs found in database. BM25 search will not work.")
            return

        self.corpus = []
        self.tokenized_corpus = []

        for faq in faqs:
            # Add main question
            self.corpus.append({
                'answer_id': faq.answer_id,
                'question': faq.question,
                'answer': faq.answer,
                'audio_path': faq.audio_path,
                'language': faq.language,
                'is_alternative': False
            })

            # Preprocess and tokenize
            tokens = preprocessor.preprocess_for_bm25(faq.question, faq.language)
            self.tokenized_corpus.append(tokens)

            # Add alternative questions
            for alt_question in faq.alternative_questions:
                self.corpus.append({
                    'answer_id': faq.answer_id,
                    'question': alt_question,
                    'answer': faq.answer,
                    'audio_path': faq.audio_path,
                    'language': faq.language,
                    'is_alternative': True
                })

                # Preprocess and tokenize alternative
                alt_tokens = preprocessor.preprocess_for_bm25(alt_question, faq.language)
                self.tokenized_corpus.append(alt_tokens)

        # Build BM25 index
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            self.initialized = True
            print(f"BM25 index initialized with {len(self.corpus)} questions")
        else:
            print("Warning: Empty corpus, BM25 search unavailable")

    def rebuild_index(self):
        """Rebuild BM25 index (call after adding/updating FAQs)"""
        self.initialize()

    def search(self, query: str, top_k: int = 10, language: str = None) -> List[Dict]:
        """
        Search FAQs using BM25

        Args:
            query: Query text
            top_k: Number of top results to return
            language: Language code for preprocessing

        Returns:
            List of search results with scores
        """
        if not self.initialized or self.bm25 is None:
            self.initialize()

        if not self.initialized:
            return []

        # Preprocess query
        query_tokens = preprocessor.preprocess_for_bm25(query, language)

        if not query_tokens:
            return []

        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)

        # Get top-k results
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        seen_answer_ids = set()

        for idx in top_indices:
            if scores[idx] <= 0:
                continue

            doc = self.corpus[idx]
            answer_id = doc['answer_id']

            # Deduplicate by answer_id (keep highest score)
            if answer_id not in seen_answer_ids:
                seen_answer_ids.add(answer_id)
                results.append({
                    'answer_id': answer_id,
                    'question': doc['question'],
                    'answer': doc['answer'],
                    'audio_path': doc['audio_path'],
                    'language': doc['language'],
                    'score': float(scores[idx]),
                    'matched_question': doc['question'],
                    'is_alternative': doc['is_alternative']
                })

        return results

    def get_candidates(self, query: str, top_k: int = 10, language: str = None) -> List[Tuple[str, float]]:
        """
        Get candidate answer_ids with BM25 scores

        Args:
            query: Query text
            top_k: Number of candidates
            language: Language code

        Returns:
            List of (answer_id, score) tuples
        """
        results = self.search(query, top_k, language)
        return [(r['answer_id'], r['score']) for r in results]


# Global BM25 search instance
bm25_search = BM25Search()
