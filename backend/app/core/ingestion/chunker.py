"""
chunker.py — Découpage intelligent du texte arabe en chunks pour indexation
Utilise LangChain RecursiveCharacterTextSplitter avec séparateurs arabes
"""
import logging
from typing import List, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.config import settings

logger = logging.getLogger(__name__)

# Séparateurs arabes pour un découpage naturel du texte juridique
ARABIC_SEPARATORS = [
    "\n\n",       # Double saut de ligne (entre paragraphes)
    "\n",         # Saut de ligne simple
    ".",          # Point (fin de phrase française)
    "。",         # Point CJK (sécurité)
    "،",          # Virgule arabe (pause dans la phrase)
    "؛",          # Point-virgule arabe
    "؟",          # Point d'interrogation arabe
    "!",          # Point d'exclamation
    " ",          # Espace (dernier recours)
    "",           # Caractère vide (fallback absolu)
]


class ArabicChunker:
    """
    Découpe le texte arabe en chunks optimisés pour la recherche vectorielle.
    Respecte les séparateurs naturels du texte arabe juridique.
    """

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=ARABIC_SEPARATORS,
            length_function=len,
            is_separator_regex=False,
            keep_separator=True,
        )

    def chunk_page(
        self, page_text: str, page_number: int, document_name: str
    ) -> List[dict]:
        """
        Découpe le texte d'une page en chunks avec leurs métadonnées.

        Args:
            page_text: Texte extrait de la page
            page_number: Numéro de la page (1-indexed)
            document_name: Nom du fichier PDF

        Returns:
            Liste de dicts {text, metadata}
        """
        if not page_text or not page_text.strip():
            return []

        chunks = self.splitter.split_text(page_text)

        result = []
        for i, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if len(chunk) < 20:  # Ignorer les chunks trop courts (bruit)
                continue

            result.append({
                "text": chunk,
                "metadata": {
                    "document_name": document_name,
                    "page_number": page_number,
                    "chunk_index": i,
                    "chunk_length": len(chunk),
                },
            })

        return result

    def chunk_document(
        self, pages: List[Tuple[int, str]], document_name: str
    ) -> List[dict]:
        """
        Découpe toutes les pages d'un document en chunks.

        Args:
            pages: Liste de (numéro_page, texte)
            document_name: Nom du fichier PDF

        Returns:
            Liste complète de chunks avec métadonnées
        """
        all_chunks = []
        for page_number, page_text in pages:
            page_chunks = self.chunk_page(page_text, page_number, document_name)
            all_chunks.extend(page_chunks)

        logger.info(
            f"Document '{document_name}': {len(pages)} pages → {len(all_chunks)} chunks"
        )
        return all_chunks
