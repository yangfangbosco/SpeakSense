"""
Vector Search for SpeakSense
Semantic search using embeddings and ChromaDB
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.config_loader import config
from shared.database import db


class EmbeddingModel:
    """Wrapper for embedding models with model switching capability"""

    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load embedding model"""
        print(f"Loading embedding model: {self.model_name} on {self.device}...")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        print(f"Embedding model loaded successfully!")

    def encode(self, texts: List[str], normalize: bool = True) -> List[List[float]]:
        """
        Encode texts to embeddings

        Args:
            texts: List of texts to encode
            normalize: Whether to normalize embeddings

        Returns:
            List of embeddings
        """
        if self.model is None:
            self._load_model()

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )

        return embeddings.tolist()

    def switch_model(self, model_name: str, device: str = None):
        """Switch to a different embedding model"""
        self.model_name = model_name
        if device:
            self.device = device

        # Unload current model
        if self.model is not None:
            del self.model

        # Load new model
        self._load_model()


class VectorSearch:
    """Vector-based semantic search using ChromaDB"""

    def __init__(self):
        # Load config
        vector_config = config.get_section('vector_db')
        embedding_config = config.get_section('embedding')

        # Initialize embedding model
        self.embedding_model = EmbeddingModel(
            model_name=embedding_config.get('model_name', 'BAAI/bge-m3'),
            device=embedding_config.get('device', 'cpu')
        )

        # Initialize ChromaDB
        persist_dir = vector_config.get('persist_directory', './data/chromadb')

        # Ensure directory exists
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        # Create ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Collection name
        self.collection_name = vector_config.get('collection_name', 'faq_embeddings')

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"Loaded existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": vector_config.get('distance_metric', 'cosine')}
            )
            print(f"Created new collection: {self.collection_name}")

    def add_faq(self, answer_id: str, question: str, alternative_questions: List[str], metadata: Dict = None):
        """
        Add FAQ to vector database

        Args:
            answer_id: Unique answer ID
            question: Main question text
            alternative_questions: List of alternative question texts
            metadata: Additional metadata
        """
        # Prepare all questions
        all_questions = [question] + alternative_questions

        # Generate IDs for each question variant
        ids = [f"{answer_id}_main"] + [f"{answer_id}_alt_{i}" for i in range(len(alternative_questions))]

        # Encode questions
        embeddings = self.embedding_model.encode(all_questions)

        # Prepare metadata
        metadatas = []
        for i, q in enumerate(all_questions):
            meta = {
                'answer_id': answer_id,
                'question': q,
                'is_alternative': i > 0
            }
            if metadata:
                meta.update(metadata)
            metadatas.append(meta)

        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=all_questions,
            metadatas=metadatas
        )

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search similar FAQs using vector similarity

        Args:
            query: Query text
            top_k: Number of top results

        Returns:
            List of search results with scores
        """
        # Encode query
        query_embedding = self.embedding_model.encode([query])[0]

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # Process results
        search_results = []
        seen_answer_ids = set()

        if results['ids'] and len(results['ids']) > 0:
            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                answer_id = metadata['answer_id']

                # Convert distance to similarity score (for cosine distance)
                # ChromaDB returns distance, we want similarity (1 - distance)
                similarity = 1 - distance

                # Deduplicate by answer_id (keep highest score)
                if answer_id not in seen_answer_ids:
                    seen_answer_ids.add(answer_id)

                    # Get full FAQ from database
                    faq = db.get_faq_by_id(answer_id)

                    if faq:
                        search_results.append({
                            'answer_id': answer_id,
                            'question': faq.question,
                            'answer': faq.answer,
                            'audio_path': faq.audio_path,
                            'language': faq.language,
                            'score': float(similarity),
                            'matched_question': metadata['question'],
                            'is_alternative': metadata.get('is_alternative', False)
                        })

        return search_results

    def get_candidates(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Get candidate answer_ids with similarity scores

        Args:
            query: Query text
            top_k: Number of candidates

        Returns:
            List of (answer_id, score) tuples
        """
        results = self.search(query, top_k)
        return [(r['answer_id'], r['score']) for r in results]

    def delete_faq(self, answer_id: str):
        """Delete FAQ from vector database"""
        # Get all IDs related to this answer_id
        results = self.collection.get(where={'answer_id': answer_id})

        if results['ids']:
            self.collection.delete(ids=results['ids'])

    def rebuild_index(self):
        """Rebuild entire vector index from database"""
        # Clear existing collection
        self.client.delete_collection(name=self.collection_name)

        # Recreate collection
        vector_config = config.get_section('vector_db')
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": vector_config.get('distance_metric', 'cosine')}
        )

        # Get all FAQs
        faqs = db.get_all_faqs()

        print(f"Rebuilding vector index with {len(faqs)} FAQs...")

        # Add each FAQ
        for faq in faqs:
            self.add_faq(
                answer_id=faq.answer_id,
                question=faq.question,
                alternative_questions=faq.alternative_questions,
                metadata={
                    'language': faq.language,
                    'category': faq.category
                }
            )

        print(f"Vector index rebuilt successfully!")

    def count_documents(self) -> int:
        """Get total number of documents in collection"""
        return self.collection.count()


# Global vector search instance
vector_search = VectorSearch()
