"""
health.py — Endpoint de vérification de l'état du système
"""
from fastapi import APIRouter
from app.models.response_models import HealthResponse
from app.core.embedding.embedder import embedder
from app.core.retrieval.vector_store import vector_store
from app.core.generation.llm import llm_generator

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Vérifie l'état de tous les composants du système RAG.
    """
    ollama_ok = llm_generator.is_ollama_available()
    chroma_ok = True
    try:
        _ = vector_store.total_chunks
    except Exception:
        chroma_ok = False

    return HealthResponse(
        status="ok" if (ollama_ok and chroma_ok and embedder.is_loaded) else "degraded",
        ollama_connected=ollama_ok,
        chroma_connected=chroma_ok,
        embedding_model_loaded=embedder.is_loaded,
    )
