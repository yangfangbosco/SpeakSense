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
from services.retrieval_service.parameter_extraction import parameter_extractor


class BM25Search:
    """BM25-based keyword search for FAQ retrieval"""

    def __init__(self):
        self.corpus = []  # List of FAQ entries
        self.tokenized_corpus = []  # Tokenized questions
        self.bm25 = None
        self.initialized = False

    def initialize(self):
        """Initialize BM25 index with FAQ and Intent data"""
        # Get all FAQs from database
        faqs = db.get_all_faqs()

        # Get all Intents from database
        intents = db.get_all_intents()

        if not faqs and not intents:
            print("Warning: No FAQs or Intents found in database. BM25 search will not work.")
            return

        self.corpus = []
        self.tokenized_corpus = []

        # Add FAQs to corpus
        for faq in faqs:
            # Add main question
            self.corpus.append({
                'type': 'faq',
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
                    'type': 'faq',
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

        # Add Intents to corpus (treat trigger phrases as questions)
        for intent in intents:
            for trigger_phrase in intent.trigger_phrases:
                self.corpus.append({
                    'type': 'intent',
                    'intent_id': intent.intent_id,
                    'intent_name': intent.intent_name,
                    'description': intent.description,
                    'trigger_phrase': trigger_phrase,
                    'action_type': intent.action_type,
                    'action_config': intent.action_config,
                    'language': intent.language,
                    'category': intent.category
                })

                # Preprocess and tokenize trigger phrase
                tokens = preprocessor.preprocess_for_bm25(trigger_phrase, intent.language)
                self.tokenized_corpus.append(tokens)

        # Build BM25 index
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            self.initialized = True
            print(f"BM25 index initialized with {len(self.corpus)} documents ({len(faqs)} FAQs, {len(intents)} Intents)")
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
        seen_ids = set()  # Track both answer_ids (FAQ) and intent_ids (Intent)

        for idx in top_indices:
            if scores[idx] <= 0:
                continue

            doc = self.corpus[idx]
            doc_type = doc['type']

            if doc_type == 'faq':
                # FAQ result
                answer_id = doc['answer_id']

                # Deduplicate by answer_id (keep highest score)
                if answer_id not in seen_ids:
                    seen_ids.add(answer_id)
                    results.append({
                        'type': 'faq',
                        'answer_id': answer_id,
                        'question': doc['question'],
                        'answer': doc['answer'],
                        'audio_path': doc['audio_path'],
                        'language': doc['language'],
                        'score': float(scores[idx]),
                        'matched_question': doc['question'],
                        'is_alternative': doc['is_alternative']
                    })

            elif doc_type == 'intent':
                # Intent result
                intent_id = doc['intent_id']

                # Deduplicate by intent_id (keep highest score)
                if intent_id not in seen_ids:
                    seen_ids.add(intent_id)

                    # Get full intent from database to access all trigger phrases
                    intent = db.get_intent_by_id(intent_id)
                    parameters = {}
                    matched_phrase = doc['trigger_phrase']

                    if intent:
                        # Extract parameters from query using all trigger phrases
                        matched, phrase, parameters = parameter_extractor.match_and_extract(
                            query, intent.trigger_phrases
                        )
                        if matched:
                            matched_phrase = phrase

                    results.append({
                        'type': 'intent',
                        'intent_id': intent_id,
                        'intent_name': doc['intent_name'],
                        'description': doc['description'],
                        'matched_phrase': matched_phrase,
                        'action_type': doc['action_type'],
                        'action_config': doc['action_config'],
                        'language': doc['language'],
                        'category': doc['category'],
                        'score': float(scores[idx]),
                        'parameters': parameters  # Extracted parameters
                    })

        return results

    def get_candidates(self, query: str, top_k: int = 10, language: str = None) -> List[Tuple[str, float]]:
        """
        Get candidate IDs with BM25 scores
        Returns (document_id, score) tuples where document_id is answer_id for FAQs or intent_id for Intents

        Args:
            query: Query text
            top_k: Number of candidates
            language: Language code

        Returns:
            List of (document_id, score) tuples
        """
        results = self.search(query, top_k, language)
        candidates = []
        for r in results:
            if r['type'] == 'faq':
                candidates.append((r['answer_id'], r['score']))
            elif r['type'] == 'intent':
                candidates.append((r['intent_id'], r['score']))
        return candidates


# Global BM25 search instance
bm25_search = BM25Search()
