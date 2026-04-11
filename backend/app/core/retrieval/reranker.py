"""
reranker.py — Re-classement des résultats avec BGE-Reranker-v2-M3 (Gratuit)
Améliore significativement la précision de la recherche juridique arabe
"""
import logging
from typing import List, Dict

from app.config import settings

logger = logging.getLogger(__name__)

try:
    from FlagEmbedding import FlagReranker
    RERANKER_AVAILABLE = True
except ImportError:
    logger.warning("FlagEmbedding non disponible. pip install FlagEmbedding")
    RERANKER_AVAILABLE = False


class BGEReranker:
    """
    Re-classe les chunks récupérés par ChromaDB selon leur pertinence réelle
    par rapport à la question posée.

    Modèle: BAAI/bge-reranker-v2-m3 (multilingue, excellent en arabe)
    """

    _instance = None
    _reranker = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_model(self):
        """Charge le reranker (appelé une fois au démarrage)."""
        if self._reranker is not None or not RERANKER_AVAILABLE:
            return
        logger.info("Chargement du BGE-Reranker-v2-M3...")
        self._reranker = FlagReranker(
            "BAAI/bge-reranker-v2-m3",
            use_fp16=True,  # Utilise FP16 pour réduire la RAM
        )
        logger.info("BGE-Reranker chargé")

    def rerank(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = None,
    ) -> List[Dict]:
        """
        Re-classe les chunks selon leur pertinence avec la question.

        Args:
            query: Question de l'utilisateur
            chunks: Chunks récupérés par ChromaDB (avec 'text' et 'metadata')
            top_k: Nombre de chunks à retourner après re-classement

        Returns:
            Chunks re-classés du plus pertinent au moins pertinent
        """
        top_k = top_k or settings.TOP_K_RERANK

        if not chunks:
            return []

        if not RERANKER_AVAILABLE or self._reranker is None:
            # Fallback : retourner les résultats triés par score ChromaDB
            logger.warning("Reranker non disponible, fallback sur score ChromaDB")
            sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)
            return sorted_chunks[:top_k]

        # Préparation des paires (question, chunk) pour le reranker
        pairs = [(query, chunk["text"]) for chunk in chunks]

        try:
            scores = self._reranker.compute_score(pairs, normalize=True)

            # Ajout du score de reranking
            for chunk, score in zip(chunks, scores):
                chunk["rerank_score"] = round(float(score), 4)

            # Tri par score de reranking décroissant
            reranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)

            logger.info(
                f"Reranking: {len(chunks)} → {top_k} chunks (meilleur score: "
                f"{reranked[0]['rerank_score']:.3f})"
            )
            return reranked[:top_k]

        except Exception as e:
            logger.error(f"Erreur reranking: {e}")
            # Fallback sur scores ChromaDB
            return sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)[:top_k]

    @property
    def is_loaded(self) -> bool:
        return self._reranker is not None


# Instance globale
reranker = BGEReranker()
