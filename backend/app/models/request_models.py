"""
request_models.py — Schémas Pydantic pour les requêtes entrantes
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="La question posée par l'utilisateur (arabe ou français)",
        example="ما هي شروط إبرام العقد في القانون المغربي؟"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Identifiant de session pour l'historique du chat"
    )
    top_k: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Nombre de chunks à retourner par collection"
    )
    collection_ids: Optional[List[str]] = Field(
        default=None,
        description="IDs des Document Collections cibles (None = toute la base)"
    )


class DeleteDocumentRequest(BaseModel):
    document_id: str = Field(
        ...,
        description="Identifiant unique du document à supprimer"
    )
