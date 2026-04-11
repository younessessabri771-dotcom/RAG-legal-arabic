"""
main.py — Point d'entrée de l'application FastAPI
Bot RAG — Documents Juridiques Arabes
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import documents, chat, health
from app.core.embedding.embedder import embedder
from app.core.retrieval.reranker import reranker

# ---- Logging ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application :
    - Démarrage : chargement des modèles (BGE-M3, Reranker)
    - Arrêt : libération des ressources
    """
    # -- Démarrage --
    logger.info("🚀 Démarrage du Bot RAG — Documents Juridiques Arabes")

    # Créer les dossiers nécessaires
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)

    # Chargement du modèle d'embedding BGE-M3
    logger.info("⏳ Chargement BGE-M3 (peut prendre ~30s au premier lancement)...")
    embedder.load_model()
    logger.info("✅ BGE-M3 chargé")

    # Chargement du reranker BGE-Reranker-v2-M3
    logger.info("⏳ Chargement BGE-Reranker-v2-M3...")
    reranker.load_model()
    logger.info("✅ BGE-Reranker chargé")

    logger.info("✅ Système prêt ! API disponible sur http://localhost:8000")
    logger.info("📖 Documentation Swagger : http://localhost:8000/docs")

    yield  # L'application tourne ici

    # -- Arrêt --
    logger.info("👋 Arrêt du serveur...")


# ---- Application FastAPI ----
app = FastAPI(
    title="Bot RAG — Documents Juridiques Arabes",
    description=(
        "API de recherche et génération augmentée (RAG) pour documents juridiques "
        "en arabe. Utilise GPT-4o Vision pour l'extraction, BGE-M3 pour les "
        "embeddings, et Qwen2.5 pour la génération de réponses."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---- CORS (autorise le frontend React) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routes ----
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(health.router)


@app.get("/")
async def root():
    return {
        "message": "Bot RAG — Documents Juridiques Arabes",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
