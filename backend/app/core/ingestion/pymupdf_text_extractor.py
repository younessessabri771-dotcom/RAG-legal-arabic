"""
pymupdf_text_extractor.py — Extraction directe du texte arabe via PyMuPDF (Gratuit)
Utilisé pour les PDFs born-digital (texte natif, non scanné)
"""
import fitz  # PyMuPDF
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class PyMuPDFTextExtractor:
    """
    Extrait le texte directement depuis les PDFs textuels (born-digital).
    100% gratuit — aucun appel API externe.
    Fonctionne très bien pour les documents juridiques arabes numériques.
    """

    def extract_all_pages(self, pdf_path: str) -> List[Tuple[int, str]]:
        """
        Extrait le texte de toutes les pages d'un PDF textuel.

        Args:
            pdf_path: Chemin vers le fichier PDF

        Returns:
            Liste de tuples (numéro_page_1indexed, texte_extrait)
        """
        logger.info(f"PyMuPDF extraction (gratuit): {pdf_path}")
        results: List[Tuple[int, str]] = []

        try:
            doc = fitz.open(pdf_path)
            for page_index in range(doc.page_count):
                page = doc.load_page(page_index)
                # Extraction avec préservation de l'ordre de lecture (RTL pour l'arabe)
                text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                text = text.strip()
                if text:
                    results.append((page_index + 1, text))
                else:
                    logger.debug(f"Page {page_index + 1}: vide, ignorée")
            doc.close()

        except Exception as e:
            logger.error(f"Erreur extraction PyMuPDF: {e}")
            raise

        logger.info(f"PyMuPDF: {len(results)} pages extraites gratuitement")
        return results
