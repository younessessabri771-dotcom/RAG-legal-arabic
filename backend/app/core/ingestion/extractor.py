"""
extractor.py — Extraction des métadonnées PDF et conversion en images
Utilise PyMuPDF (fitz) pour les métadonnées et pdf2image pour les images
"""
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
from typing import List, Tuple
import io
import logging

logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extrait les métadonnées d'un PDF et convertit ses pages en images
    pour envoi à GPT-4o Vision.
    """

    def __init__(self, dpi: int = 200, max_image_size: Tuple[int, int] = (2048, 2048)):
        """
        Args:
            dpi: Résolution pour la conversion (200 dpi = bon compromis qualité/coût)
            max_image_size: Taille max de l'image pour éviter des coûts élevés
        """
        self.dpi = dpi
        self.max_image_size = max_image_size

    def get_metadata(self, pdf_path: str) -> dict:
        """
        Extrait les métadonnées du PDF (titre, nb pages, auteur...).
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "page_count": doc.page_count,
                "filename": Path(pdf_path).name,
                "is_encrypted": doc.is_encrypted,
            }
            doc.close()
            return metadata
        except Exception as e:
            logger.error(f"Erreur extraction métadonnées: {e}")
            raise

    def is_scanned(self, pdf_path: str, sample_pages: int = 3) -> bool:
        """
        Détecte si le PDF est scanné (peu de texte extractible directement).
        On vérifie si les premières pages ont du texte ou non.
        """
        try:
            doc = fitz.open(pdf_path)
            pages_to_check = min(sample_pages, doc.page_count)
            total_chars = 0
            for i in range(pages_to_check):
                page = doc.load_page(i)
                text = page.get_text("text")
                total_chars += len(text.strip())
            doc.close()
            # Moins de 50 caractères par page en moyenne → probablement scanné
            avg_chars = total_chars / pages_to_check
            return avg_chars < 50
        except Exception:
            return True  # Si erreur, on traite comme scanné (envoyer à GPT-4o)

    def convert_to_images(self, pdf_path: str) -> List[Tuple[int, Image.Image]]:
        """
        Convertit chaque page du PDF en image PIL.

        Returns:
            Liste de tuples (numéro_page_1indexed, image_PIL)
        """
        logger.info(f"Conversion PDF → images: {pdf_path}")
        try:
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                fmt="PNG",
                thread_count=2,
            )
            result = []
            for i, img in enumerate(images):
                # Redimensionner si trop grande pour économiser les coûts GPT-4o
                resized = self._resize_image(img)
                result.append((i + 1, resized))  # page numérotée à partir de 1

            logger.info(f"Conversion terminée: {len(result)} pages")
            return result

        except Exception as e:
            logger.error(f"Erreur conversion PDF→images: {e}")
            raise

    def _resize_image(self, img: Image.Image) -> Image.Image:
        """Redimensionne l'image si elle dépasse max_image_size."""
        if img.width > self.max_image_size[0] or img.height > self.max_image_size[1]:
            img.thumbnail(self.max_image_size, Image.LANCZOS)
        return img

    def image_to_bytes(self, img: Image.Image) -> bytes:
        """Convertit une image PIL en bytes PNG."""
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
