"""
collections.py — Routes API pour la gestion des Document Collections
Chaque collection est un groupe nommé de PDFs.
"""
import uuid
import json
import time
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Body

from app.config import settings
from app.models.response_models import (
    CollectionInfo,
    CollectionListResponse,
    CollectionCreateResponse,
    CollectionDocumentInfo,
    DocumentUploadResponse,
    DeleteResponse,
)
from app.core.ingestion.gpt4o_extractor import GPT4oExtractor
from app.core.ingestion.pymupdf_text_extractor import PyMuPDFTextExtractor
from app.core.ingestion.extractor import PDFExtractor
from app.core.ingestion.arabic_normalizer import ArabicNormalizer
from app.core.ingestion.chunker import ArabicChunker
from app.core.retrieval.vector_store import vector_store

router = APIRouter(prefix="/api/collections", tags=["Collections"])
logger = logging.getLogger(__name__)

# Chemin du fichier de persistance des collections
COLLECTIONS_FILE = Path("collections.json")

# Composants pipeline
pdf_extractor_instance = PDFExtractor()
gpt4o_extractor = GPT4oExtractor()
pymupdf_text_extractor = PyMuPDFTextExtractor()
normalizer = ArabicNormalizer()
chunker = ArabicChunker()


# ─────────────────────────────────────────────
# Persistance JSON
# ─────────────────────────────────────────────

def _load_registry() -> dict:
    """Charge le registre des collections depuis le fichier JSON."""
    if COLLECTIONS_FILE.exists():
        try:
            with open(COLLECTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Impossible de lire {COLLECTIONS_FILE}: {e}")
    return {}


def _save_registry(registry: dict):
    """Sauvegarde le registre des collections dans le fichier JSON."""
    try:
        with open(COLLECTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Impossible de sauvegarder {COLLECTIONS_FILE}: {e}")


# Registre en mémoire (chargé au démarrage)
_collections_registry: dict = _load_registry()


# ─────────────────────────────────────────────
# Pipeline d'ingestion
# ─────────────────────────────────────────────

async def _process_pdf(
    pdf_path: str,
    document_id: str,
    filename: str,
    collection_id: str,
):
    """
    Pipeline complet d'ingestion d'un PDF dans une collection :
    PDF → Extraction → Normalisation → Chunking → ChromaDB (avec collection_id)
    """
    try:
        _collections_registry[collection_id]["documents"][document_id]["status"] = "processing"
        _save_registry(_collections_registry)

        # Étape 1 : Choix de la méthode d'extraction
        is_scanned = pdf_extractor_instance.is_scanned(pdf_path)
        use_gpt4o = not settings.AUTO_DETECT_EXTRACTION or is_scanned

        if use_gpt4o:
            logger.info(f"[{document_id}] PDF {'scanné' if is_scanned else 'forcé GPT-4o'} → GPT-4o Vision 💰")
            pages = gpt4o_extractor.extract_all_pages(pdf_path)
        else:
            logger.info(f"[{document_id}] PDF textuel → PyMuPDF ✅ Gratuit")
            pages = pymupdf_text_extractor.extract_all_pages(pdf_path)

        _collections_registry[collection_id]["documents"][document_id]["extraction_method"] = (
            "gpt4o" if use_gpt4o else "pymupdf"
        )

        if not pages:
            raise ValueError("Aucun contenu extractible trouvé dans le PDF")

        # Étape 2 : Normalisation
        logger.info(f"[{document_id}] Normalisation arabe...")
        normalized_pages = [
            (page_num, normalizer.normalize(text))
            for page_num, text in pages
        ]

        # Étape 3 : Chunking
        logger.info(f"[{document_id}] Chunking...")
        chunks = chunker.chunk_document(normalized_pages, filename)

        # Étape 4 : Indexation dans ChromaDB avec collection_id
        logger.info(f"[{document_id}] Indexation ChromaDB (collection: {collection_id})...")
        chunks_count = vector_store.add_chunks(chunks, document_id, collection_id=collection_id)

        # Mise à jour du registre
        _collections_registry[collection_id]["documents"][document_id].update({
            "status": "indexed",
            "page_count": len(pages),
            "chunk_count": chunks_count,
        })
        _collections_registry[collection_id]["document_count"] = len(
            _collections_registry[collection_id]["documents"]
        )
        _save_registry(_collections_registry)
        logger.info(f"[{document_id}] ✅ Ingestion terminée: {len(pages)} pages, {chunks_count} chunks")

    except Exception as e:
        logger.error(f"[{document_id}] Erreur ingestion: {e}")
        _collections_registry[collection_id]["documents"][document_id]["status"] = "error"
        _collections_registry[collection_id]["documents"][document_id]["error"] = str(e)
        _save_registry(_collections_registry)


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@router.post("", response_model=CollectionCreateResponse)
async def create_collection(name: str = Body(..., embed=True)):
    """Crée une nouvelle Document Collection."""
    # Vérifier que le nom n'existe pas déjà
    for col in _collections_registry.values():
        if col["name"].strip().lower() == name.strip().lower():
            raise HTTPException(status_code=400, detail=f"Une collection nommée '{name}' existe déjà")

    collection_id = str(uuid.uuid4())
    _collections_registry[collection_id] = {
        "collection_id": collection_id,
        "name": name.strip(),
        "document_count": 0,
        "created_at": datetime.utcnow().isoformat(),
        "documents": {},
    }
    _save_registry(_collections_registry)
    logger.info(f"Collection créée: '{name}' (ID: {collection_id})")

    return CollectionCreateResponse(
        success=True,
        message=f"Collection '{name}' créée avec succès",
        collection_id=collection_id,
        name=name.strip(),
    )


@router.get("", response_model=CollectionListResponse)
async def list_collections():
    """Liste toutes les Document Collections."""
    collections = []
    for col_data in _collections_registry.values():
        docs = [
            CollectionDocumentInfo(
                document_id=doc_id,
                filename=doc_info.get("filename", ""),
                page_count=doc_info.get("page_count", 0),
                chunk_count=doc_info.get("chunk_count", 0),
                uploaded_at=datetime.fromisoformat(doc_info.get("uploaded_at", datetime.utcnow().isoformat())),
                status=doc_info.get("status", "unknown"),
            )
            for doc_id, doc_info in col_data.get("documents", {}).items()
        ]
        collections.append(CollectionInfo(
            collection_id=col_data["collection_id"],
            name=col_data["name"],
            document_count=len(docs),
            created_at=datetime.fromisoformat(col_data["created_at"]),
            documents=docs,
        ))

    return CollectionListResponse(collections=collections, total=len(collections))


@router.delete("/{collection_id}", response_model=DeleteResponse)
async def delete_collection(collection_id: str):
    """Supprime une collection et tous ses documents."""
    if collection_id not in _collections_registry:
        raise HTTPException(status_code=404, detail="Collection non trouvée")

    col_data = _collections_registry[collection_id]

    # Supprimer les chunks ChromaDB de la collection
    deleted_chunks = vector_store.delete_collection(collection_id)

    # Supprimer les fichiers PDF physiques
    for doc_id, doc_info in col_data.get("documents", {}).items():
        pdf_path = Path(doc_info.get("pdf_path", ""))
        if pdf_path.exists():
            pdf_path.unlink()

    # Supprimer du registre
    del _collections_registry[collection_id]
    _save_registry(_collections_registry)

    return DeleteResponse(
        success=True,
        message=f"Collection '{col_data['name']}' supprimée ({deleted_chunks} chunks supprimés)"
    )


@router.post("/{collection_id}/upload", response_model=DocumentUploadResponse)
async def upload_to_collection(
    collection_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload et indexe un PDF dans une collection spécifique."""
    if collection_id not in _collections_registry:
        raise HTTPException(status_code=404, detail="Collection non trouvée")

    # Validation
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés")

    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop grand. Maximum: {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Dossier d'upload de la collection
    upload_dir = Path(settings.UPLOAD_DIR) / collection_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    document_id = str(uuid.uuid4())
    safe_filename = file.filename.replace(" ", "_")
    pdf_path = upload_dir / f"{document_id}.pdf"

    with open(pdf_path, "wb") as f:
        f.write(content)

    # Enregistrement dans le registre
    _collections_registry[collection_id]["documents"][document_id] = {
        "document_id": document_id,
        "filename": safe_filename,
        "status": "queued",
        "page_count": 0,
        "chunk_count": 0,
        "uploaded_at": datetime.utcnow().isoformat(),
        "pdf_path": str(pdf_path),
    }
    _save_registry(_collections_registry)

    # Ingestion en arrière-plan
    background_tasks.add_task(
        _process_pdf, str(pdf_path), document_id, safe_filename, collection_id
    )

    logger.info(f"Upload dans collection '{_collections_registry[collection_id]['name']}': {safe_filename}")

    return DocumentUploadResponse(
        success=True,
        message="Document reçu. L'indexation est en cours...",
        document_id=document_id,
        filename=safe_filename,
        pages_processed=0,
        chunks_created=0,
    )


@router.get("/{collection_id}/documents/{document_id}/status")
async def get_document_status(collection_id: str, document_id: str):
    """Retourne le statut d'indexation d'un document dans une collection."""
    if collection_id not in _collections_registry:
        raise HTTPException(status_code=404, detail="Collection non trouvée")
    docs = _collections_registry[collection_id].get("documents", {})
    if document_id not in docs:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return docs[document_id]


@router.delete("/{collection_id}/documents/{document_id}", response_model=DeleteResponse)
async def delete_document_from_collection(collection_id: str, document_id: str):
    """Supprime un document d'une collection."""
    if collection_id not in _collections_registry:
        raise HTTPException(status_code=404, detail="Collection non trouvée")
    docs = _collections_registry[collection_id].get("documents", {})
    if document_id not in docs:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    # Supprimer chunks ChromaDB
    deleted_chunks = vector_store.delete_document(document_id)

    # Supprimer le fichier PDF
    pdf_path = Path(docs[document_id].get("pdf_path", ""))
    if pdf_path.exists():
        pdf_path.unlink()

    # Supprimer du registre
    del _collections_registry[collection_id]["documents"][document_id]
    _collections_registry[collection_id]["document_count"] = len(
        _collections_registry[collection_id]["documents"]
    )
    _save_registry(_collections_registry)

    return DeleteResponse(
        success=True,
        message=f"Document supprimé ({deleted_chunks} chunks supprimés)"
    )
