"""
documents.py — Routes API pour l'upload et la gestion des documents PDF
"""
import uuid
import time
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.response_models import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentInfo,
    DeleteResponse,
)
from app.core.ingestion.gpt4o_extractor import GPT4oExtractor
from app.core.ingestion.pymupdf_text_extractor import PyMuPDFTextExtractor
from app.core.ingestion.extractor import PDFExtractor
from app.core.ingestion.arabic_normalizer import ArabicNormalizer
from app.core.ingestion.chunker import ArabicChunker
from app.core.retrieval.vector_store import vector_store

router = APIRouter(prefix="/api/documents", tags=["Documents"])
logger = logging.getLogger(__name__)

# Instanciation des composants du pipeline
pdf_extractor_instance = PDFExtractor()   # Détection scan + conversion images
gpt4o_extractor = GPT4oExtractor()        # Extraction GPT-4o (PDFs scannés)
pymupdf_text_extractor = PyMuPDFTextExtractor()  # Extraction PyMuPDF (PDFs textuels)
normalizer = ArabicNormalizer()
chunker = ArabicChunker()

# Stockage en mémoire des métadonnées des documents (peut être remplacé par une DB)
_documents_registry: dict = {}


def _ensure_upload_dir():
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


async def _process_pdf(pdf_path: str, document_id: str, filename: str):
    """
    Pipeline complet d'ingestion d'un PDF :
    PDF → GPT-4o Vision → Normalisation → Chunking → ChromaDB
    """
    try:
        _documents_registry[document_id]["status"] = "processing"

        # ----------------------------------------------------------------
        # Étape 1 : Choix de la méthode d'extraction (Smart Routing)
        # ----------------------------------------------------------------
        is_scanned = pdf_extractor_instance.is_scanned(pdf_path)
        use_gpt4o = not settings.AUTO_DETECT_EXTRACTION or is_scanned

        if use_gpt4o:
            logger.info(
                f"[{document_id}] PDF {'scanné' if is_scanned else 'forcé GPT-4o'} "
                f"→ GPT-4o Vision 💰"
            )
            pages = gpt4o_extractor.extract_all_pages(pdf_path)
        else:
            logger.info(f"[{document_id}] PDF textuel → PyMuPDF ✅ Gratuit")
            pages = pymupdf_text_extractor.extract_all_pages(pdf_path)

        # Enregistrer la méthode utilisée dans le registre
        _documents_registry[document_id]["extraction_method"] = (
            "gpt4o" if use_gpt4o else "pymupdf"
        )

        if not pages:
            raise ValueError("Aucun contenu extractible trouvé dans le PDF")

        # Étape 2 : Normalisation du texte arabe
        logger.info(f"[{document_id}] Normalisation arabe...")
        normalized_pages = [
            (page_num, normalizer.normalize(text))
            for page_num, text in pages
        ]

        # Étape 3 : Chunking
        logger.info(f"[{document_id}] Chunking...")
        chunks = chunker.chunk_document(normalized_pages, filename)

        # Étape 4 : Indexation dans ChromaDB
        logger.info(f"[{document_id}] Indexation ChromaDB...")
        chunks_count = vector_store.add_chunks(chunks, document_id)

        # Mise à jour du registre
        _documents_registry[document_id].update({
            "status": "indexed",
            "page_count": len(pages),
            "chunk_count": chunks_count,
        })
        logger.info(
            f"[{document_id}] ✅ Ingestion terminée: {len(pages)} pages, "
            f"{chunks_count} chunks"
        )

    except Exception as e:
        logger.error(f"[{document_id}] Erreur ingestion: {e}")
        _documents_registry[document_id]["status"] = "error"
        _documents_registry[document_id]["error"] = str(e)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload et indexation d'un document PDF.
    L'ingestion se fait en arrière-plan (GPT-4o Vision peut prendre du temps).
    """
    _ensure_upload_dir()

    # Validation du fichier
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés")

    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop grand. Maximum: {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Sauvegarde du fichier
    # IMPORTANT: On utilise uniquement l'UUID comme nom de fichier sur disque
    # pour éviter les problèmes d'encodage avec les noms arabes sur Windows.
    document_id = str(uuid.uuid4())
    original_filename = file.filename  # Nom original gardé pour l'affichage
    safe_filename = file.filename.replace(" ", "_")  # Pour affichage uniquement
    pdf_path = Path(settings.UPLOAD_DIR) / f"{document_id}.pdf"  # UUID uniquement

    with open(pdf_path, "wb") as f:
        f.write(content)

    # Enregistrement dans le registre
    _documents_registry[document_id] = {
        "document_id": document_id,
        "filename": safe_filename,          # Nom original pour l'affichage
        "status": "queued",
        "page_count": 0,
        "chunk_count": 0,
        "uploaded_at": datetime.utcnow().isoformat(),
        "pdf_path": str(pdf_path),          # Chemin avec UUID uniquement
    }

    # Lancement de l'ingestion en arrière-plan
    background_tasks.add_task(
        _process_pdf, str(pdf_path), document_id, safe_filename
    )

    logger.info(f"Upload reçu: {safe_filename} (ID: {document_id})")

    return DocumentUploadResponse(
        success=True,
        message="Document reçu. L'indexation est en cours (détection auto du type de PDF)...",
        document_id=document_id,
        filename=safe_filename,
        pages_processed=0,
        chunks_created=0,
    )


@router.get("/list", response_model=DocumentListResponse)
async def list_documents():
    """
    Liste tous les documents indexés avec leur statut.
    """
    docs = []
    for doc_id, info in _documents_registry.items():
        docs.append(DocumentInfo(
            document_id=doc_id,
            filename=info.get("filename", ""),
            page_count=info.get("page_count", 0),
            chunk_count=info.get("chunk_count", 0),
            uploaded_at=datetime.fromisoformat(
                info.get("uploaded_at", datetime.utcnow().isoformat())
            ),
            status=info.get("status", "unknown"),
        ))

    return DocumentListResponse(documents=docs, total=len(docs))


@router.get("/{document_id}/status")
async def get_document_status(document_id: str):
    """
    Retourne le statut d'indexation d'un document.
    """
    if document_id not in _documents_registry:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return _documents_registry[document_id]


@router.delete("/{document_id}", response_model=DeleteResponse)
async def delete_document(document_id: str):
    """
    Supprime un document et tous ses chunks de ChromaDB.
    """
    if document_id not in _documents_registry:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    # Suppression des chunks dans ChromaDB
    deleted_chunks = vector_store.delete_document(document_id)

    # Suppression du fichier PDF
    doc_info = _documents_registry[document_id]
    pdf_path = Path(doc_info.get("pdf_path", ""))
    if pdf_path.exists():
        pdf_path.unlink()

    # Suppression du registre
    del _documents_registry[document_id]

    return DeleteResponse(
        success=True,
        message=f"Document supprimé ({deleted_chunks} chunks supprimés)"
    )
