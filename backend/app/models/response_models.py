"""
response_models.py — Schémas Pydantic pour les réponses API
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SourceReference(BaseModel):
    document_name: str = Field(..., description="Nom du fichier PDF source")
    page_number: int = Field(..., description="Numéro de la page source")
    chunk_text: str = Field(..., description="Extrait du texte source")
    relevance_score: float = Field(..., description="Score de pertinence (0-1)")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Réponse générée par le LLM")
    sources: List[SourceReference] = Field(
        default_factory=list,
        description="Sources utilisées pour générer la réponse"
    )
    session_id: str = Field(..., description="Identifiant de session")
    processing_time_ms: int = Field(..., description="Temps de traitement en ms")


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    uploaded_at: datetime
    status: str  # "indexed", "processing", "error"


class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    filename: str
    pages_processed: int
    chunks_created: int


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int


class DeleteResponse(BaseModel):
    success: bool
    message: str


class HealthResponse(BaseModel):
    status: str
    groq_connected: bool
    chroma_connected: bool
    embedding_model_loaded: bool
    version: str = "1.0.0"


# --- Document Collections ---

class CollectionDocumentInfo(BaseModel):
    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    uploaded_at: datetime
    status: str  # "indexed", "processing", "error"


class CollectionInfo(BaseModel):
    collection_id: str
    name: str
    document_count: int
    created_at: datetime
    documents: List[CollectionDocumentInfo] = Field(default_factory=list)


class CollectionCreateResponse(BaseModel):
    success: bool
    message: str
    collection_id: str
    name: str


class CollectionListResponse(BaseModel):
    collections: List[CollectionInfo]
    total: int
