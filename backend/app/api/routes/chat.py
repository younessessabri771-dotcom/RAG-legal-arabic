"""
chat.py — Routes API pour les questions/réponses RAG
Pipeline: Question → Normalisation → Embedding → ChromaDB → Reranking → Qwen2.5
"""
import time
import uuid
import logging
from typing import Dict, List

from fastapi import APIRouter, HTTPException

from app.models.request_models import ChatRequest
from app.models.response_models import ChatResponse, SourceReference
from app.core.ingestion.arabic_normalizer import ArabicNormalizer
from app.core.retrieval.vector_store import vector_store
from app.core.retrieval.reranker import reranker
from app.core.generation.llm import llm_generator

router = APIRouter(prefix="/api/chat", tags=["Chat"])
logger = logging.getLogger(__name__)

normalizer = ArabicNormalizer()

# Historique des sessions en mémoire (simple, peut être remplacé par Redis)
_chat_history: Dict[str, List[dict]] = {}


@router.post("/query", response_model=ChatResponse)
async def query(request: ChatRequest):
    """
    Pipeline RAG complet :
    Question → Normalisation → BGE-M3 → ChromaDB (top-20)
    → BGE-Reranker (top-5) → Qwen2.5 → Réponse avec sources
    """
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())

    if vector_store.total_chunks == 0:
        raise HTTPException(
            status_code=400,
            detail="Aucun document indexé. Veuillez d'abord uploader des PDFs."
        )

    # Étape 1 : Normalisation de la question
    normalized_question = normalizer.normalize_query(request.question)
    logger.info(f"[{session_id}] Question: {request.question[:80]}...")

    # Étape 2 : Recherche vectorielle (top-K dans ChromaDB)
    candidates = vector_store.search(
        query=normalized_question,
        top_k=settings_top_k(request.top_k),
    )

    if not candidates:
        return ChatResponse(
            answer="لم أجد نتائج ذات صلة. يرجى التحقق من الوثائق المفهرسة.",
            sources=[],
            session_id=session_id,
            processing_time_ms=int((time.time() - start_time) * 1000),
        )

    # Étape 3 : Reranking (BGE-Reranker)
    reranked = reranker.rerank(
        query=normalized_question,
        chunks=candidates,
        top_k=request.top_k or 5,
    )

    # Étape 4 : Génération de la réponse (Qwen2.5)
    try:
        answer = llm_generator.generate(
            question=request.question,
            chunks=reranked,
        )
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Construction des sources
    sources = [
        SourceReference(
            document_name=chunk["metadata"].get("document_name", ""),
            page_number=chunk["metadata"].get("page_number", 0),
            chunk_text=chunk["text"][:300] + "..." if len(chunk["text"]) > 300 else chunk["text"],
            relevance_score=chunk.get("rerank_score", chunk.get("score", 0.0)),
        )
        for chunk in reranked
    ]

    # Ajout à l'historique de session
    _chat_history.setdefault(session_id, []).append({
        "question": request.question,
        "answer": answer,
        "sources_count": len(sources),
    })

    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info(f"[{session_id}] Réponse générée en {elapsed_ms}ms")

    return ChatResponse(
        answer=answer,
        sources=sources,
        session_id=session_id,
        processing_time_ms=elapsed_ms,
    )


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """
    Retourne l'historique de chat d'une session.
    """
    history = _chat_history.get(session_id, [])
    return {"session_id": session_id, "messages": history, "count": len(history)}


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """
    Efface l'historique d'une session.
    """
    _chat_history.pop(session_id, None)
    return {"success": True, "message": "Historique effacé"}


def settings_top_k(requested: int = None) -> int:
    """Retourne le top_k validé."""
    from app.config import settings
    return min(requested or settings.TOP_K_RETRIEVAL, 20)
