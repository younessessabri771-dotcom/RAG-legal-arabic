"""
vector_store.py — Gestion de la base vectorielle ChromaDB
Stocke et recherche les chunks de documents juridiques arabes
"""
import uuid
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.core.embedding.embedder import embedder

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Interface ChromaDB pour stocker et rechercher les chunks de documents.
    La collection est persistante sur disque (chroma_db/).
    """

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # Similarité cosine pour BGE-M3
        )
        logger.info(
            f"ChromaDB initialisé: {self.collection.count()} chunks existants"
        )

    def add_chunks(
        self,
        chunks: List[dict],
        document_id: str,
        collection_id: Optional[str] = None,
    ) -> int:
        """
        Ajoute des chunks dans ChromaDB.

        Args:
            chunks: Liste de {text, metadata} produits par ArabicChunker
            document_id: ID unique du document parent

        Returns:
            Nombre de chunks ajoutés
        """
        if not chunks:
            return 0

        ids = []
        documents = []
        embeddings = []
        metadatas = []

        # Génération des embeddings en batch
        texts = [c["text"] for c in chunks]
        batch_embeddings = embedder.embed_texts(texts)

        for i, (chunk, embedding) in enumerate(zip(chunks, batch_embeddings)):
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            documents.append(chunk["text"])
            embeddings.append(embedding)
            meta = {
                **chunk["metadata"],
                "document_id": document_id,
                "indexed_at": datetime.utcnow().isoformat(),
            }
            if collection_id:
                meta["collection_id"] = collection_id
            metadatas.append(meta)

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info(f"Ajout de {len(ids)} chunks pour document {document_id}")
        return len(ids)

    def search(
        self,
        query: str,
        top_k: int = None,
        document_id: Optional[str] = None,
        collection_id: Optional[str] = None,
    ) -> List[Dict]:
        """
        Recherche les chunks les plus similaires à une question.

        Args:
            query: Question de l'utilisateur
            top_k: Nombre de résultats à retourner
            document_id: Filtrer par document spécifique (optionnel)
            collection_id: Filtrer par collection (optionnel)

        Returns:
            Liste de chunks avec scores de similarité
        """
        top_k = top_k or settings.TOP_K_RETRIEVAL
        query_embedding = embedder.embed_query(query)

        if document_id:
            where_filter = {"document_id": document_id}
        elif collection_id:
            where_filter = {"collection_id": collection_id}
        else:
            where_filter = None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count() or 1),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                # Conversion distance cosine → score similarité (0-1)
                score = 1 - dist
                chunks.append({
                    "text": doc,
                    "metadata": meta,
                    "score": round(score, 4),
                })

        return chunks

    def delete_document(self, document_id: str) -> int:
        """
        Supprime tous les chunks d'un document.

        Returns:
            Nombre de chunks supprimés
        """
        results = self.collection.get(
            where={"document_id": document_id},
            include=["documents"],
        )
        ids_to_delete = results["ids"]
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
            logger.info(
                f"Suppression de {len(ids_to_delete)} chunks pour document {document_id}"
            )
        return len(ids_to_delete)

    def delete_collection(self, collection_id: str) -> int:
        """
        Supprime tous les chunks appartenant à une collection.

        Returns:
            Nombre de chunks supprimés
        """
        results = self.collection.get(
            where={"collection_id": collection_id},
            include=["documents"],
        )
        ids_to_delete = results["ids"]
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
            logger.info(
                f"Suppression de {len(ids_to_delete)} chunks pour collection {collection_id}"
            )
        return len(ids_to_delete)

    def get_all_documents(self) -> List[Dict]:
        """
        Retourne la liste des documents uniques indexés.
        """
        results = self.collection.get(include=["metadatas"])
        seen_ids = set()
        documents = []

        for meta in results["metadatas"]:
            doc_id = meta.get("document_id")
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                documents.append({
                    "document_id": doc_id,
                    "filename": meta.get("document_name", ""),
                    "indexed_at": meta.get("indexed_at", ""),
                })

        return documents

    def count_chunks_for_document(self, document_id: str) -> int:
        """Compte le nombre de chunks pour un document donné."""
        results = self.collection.get(where={"document_id": document_id})
        return len(results["ids"])

    @property
    def total_chunks(self) -> int:
        return self.collection.count()


# Instance globale
vector_store = VectorStore()
