"""
Retrieval Service - FAQ Search and Matching
Provides API for hybrid FAQ retrieval using BM25 + Vector search
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.config_loader import config
from shared.models import RetrievalRequest, RetrievalResponse, HealthResponse
from services.retrieval_service.retrieval import retrieval
from services.retrieval_service.bm25_search import bm25_search
from services.retrieval_service.vector_search import vector_search

# Initialize FastAPI app
app = FastAPI(
    title="SpeakSense Retrieval Service",
    description="FAQ retrieval service using hybrid BM25 + Vector search",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize indices on startup
@app.on_event("startup")
async def startup_event():
    """Initialize search indices on startup"""
    print("Initializing retrieval service...")
    try:
        bm25_search.initialize()
        print(f"Vector database has {vector_search.count_documents()} documents")
        print("Retrieval service initialized successfully!")
    except Exception as e:
        print(f"Warning: Failed to initialize some components: {e}")


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="healthy",
        service="Retrieval Service",
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="Retrieval Service",
        version="1.0.0"
    )


@app.post("/retrieval/search", response_model=List[RetrievalResponse])
async def search_faq(request: RetrievalRequest):
    """
    Search for matching FAQ

    Args:
        request: RetrievalRequest with query and parameters

    Returns:
        List of matching FAQs with answers and audio paths
    """
    import time
    from shared.database import db

    start_time = time.time()

    try:
        results = retrieval.search(
            query=request.query,
            top_k=request.top_k or 1,
            language=request.language
        )

        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Log query
        if results:
            first_result = results[0]
            matched_type = first_result.get('type', 'faq')
            matched_id = first_result.get('intent_id' if matched_type == 'intent' else 'answer_id')
            matched_question = first_result.get('intent_name' if matched_type == 'intent' else 'question')
            confidence = first_result.get('confidence', first_result.get('score', 0.0))

            db.create_query_log(
                query_text=request.query,
                matched_type=matched_type,
                matched_id=matched_id,
                matched_question=matched_question,
                confidence=confidence,
                response_time=response_time
            )
        else:
            # No match found
            db.create_query_log(
                query_text=request.query,
                matched_type='none',
                response_time=response_time
            )

        if not results:
            return []

        return [
            RetrievalResponse(
                answer_id=r['answer_id'],
                question=r['question'],
                answer=r['answer'],
                audio_path=r['audio_path'],
                confidence=r.get('confidence', r.get('score', 0.0)),
                matched_by=r.get('matched_by', 'hybrid')
            )
            for r in results
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/retrieval/best_answer")
async def get_best_answer(request: RetrievalRequest):
    """
    Get the best matching answer for a query
    Returns either an Intent or FAQ result based on what matches

    Args:
        request: RetrievalRequest with query

    Returns:
        Best matching result (Intent or FAQ) with metadata
    """
    import time
    from shared.database import db

    start_time = time.time()

    try:
        result = retrieval.get_best_answer(
            query=request.query,
            language=request.language
        )

        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        if not result:
            # No match found
            db.create_query_log(
                query_text=request.query,
                matched_type='none',
                response_time=response_time
            )
            raise HTTPException(status_code=404, detail="No matching result found")

        # Log query
        matched_type = result.get('type', 'faq')
        matched_id = result.get('intent_id' if matched_type == 'intent' else 'answer_id')
        matched_question = result.get('intent_name' if matched_type == 'intent' else 'question')
        confidence = result.get('confidence', result.get('score', 0.0))

        db.create_query_log(
            query_text=request.query,
            matched_type=matched_type,
            matched_id=matched_id,
            matched_question=matched_question,
            confidence=confidence,
            response_time=response_time
        )

        # Return result as-is (works for both intents and FAQs)
        # Intent results have: type='intent', intent_id, intent_name, action_type, action_config, etc.
        # FAQ results have: type='faq', answer_id, question, answer, audio_path, matched_by, etc.
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/retrieval/rebuild_indices")
async def rebuild_indices():
    """
    Rebuild BM25 and vector search indices
    Call this after adding/updating FAQs
    """
    try:
        retrieval.rebuild_indices()
        return {
            "status": "success",
            "message": "Search indices rebuilt successfully",
            "bm25_documents": len(bm25_search.corpus) if bm25_search.corpus else 0,
            "vector_documents": vector_search.count_documents()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index rebuild failed: {str(e)}")


@app.get("/retrieval/stats")
async def get_stats():
    """Get retrieval service statistics"""
    return {
        "bm25_documents": len(bm25_search.corpus) if bm25_search.corpus else 0,
        "vector_documents": vector_search.count_documents(),
        "bm25_weight": retrieval.bm25_weight,
        "vector_weight": retrieval.vector_weight
    }


@app.post("/retrieval/search_bm25")
async def search_bm25_only(request: RetrievalRequest):
    """Search using BM25 only (for testing/debugging)"""
    try:
        results = retrieval.search(
            query=request.query,
            top_k=request.top_k or 1,
            language=request.language,
            method="bm25"
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BM25 search failed: {str(e)}")


@app.post("/retrieval/search_vector")
async def search_vector_only(request: RetrievalRequest):
    """Search using vector search only (for testing/debugging)"""
    try:
        results = retrieval.search(
            query=request.query,
            top_k=request.top_k or 1,
            language=request.language,
            method="vector"
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    retrieval_config = config.get_section('retrieval')
    port = retrieval_config.get('port', 8002)
    uvicorn.run(app, host="0.0.0.0", port=port)
