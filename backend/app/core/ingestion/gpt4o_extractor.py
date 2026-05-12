"""
gpt4o_extractor.py — Extraction du texte arabe depuis les images PDF via GPT-4o Vision
PAYANT : ~$0.01 par page (mode high detail)
"""
import base64
import logging
from typing import List, Tuple
from PIL import Image
from openai import OpenAI

from app.config import settings
from app.core.ingestion.extractor import PDFExtractor
from app.core.ingestion.ocr_cache import get_cached_pages, save_to_cache

logger = logging.getLogger(__name__)

# Prompt système spécialisé pour les documents juridiques arabes
SYSTEM_PROMPT = """أنت محلل متخصص في استخراج النصوص من الوثائق القانونية المغربية والعربية.
مهمتك هي:
1. استخراج النص العربي كاملاً من الصورة المقدمة لك
2. الحفاظ على بنية النص (الفقرات، العناوين، المواد القانونية)
3. لا تترجم النص - أعده كما هو بالعربية
4. أجهز النص للبحث والاسترجاع الآلي
5. إذا كان هناك نص بالفرنسية، أبقه كما هو أيضاً
6. تجاهل الرؤوس والتذييلات المتكررة (أرقام الصفحات، اسم الوثيقة)
أعد النص المستخرج فقط، بدون تعليقات أو مقدمات."""

USER_PROMPT = "استخرج كل النص الموجود في هذه الوثيقة القانونية."


class GPT4oExtractor:
    """
    Extrait le texte arabe des pages PDF en utilisant GPT-4o Vision.
    Chaque page est envoyée comme image encodée en base64.
    """

    def __init__(self):
        self._client = None  # Initialisé à la demande (lazy)
        self.pdf_extractor = PDFExtractor()

    @property
    def client(self):
        """Crée le client OpenAI seulement quand nécessaire."""
        if self._client is None:
            if not settings.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY non configurée. Ajoutez votre clé dans backend/.env "
                    "pour traiter les PDFs scannés. Les PDFs textuels fonctionnent sans clé."
                )
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def _encode_image_base64(self, img: Image.Image) -> str:
        """Encode une image PIL en base64 string pour l'API OpenAI."""
        import io
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def extract_text_from_image(
        self, img: Image.Image, page_number: int
    ) -> str:
        """
        Envoie une image de page PDF à GPT-4o Vision et retourne le texte extrait.

        Args:
            img: Image PIL de la page
            page_number: Numéro de la page (pour les logs)

        Returns:
            Texte arabe extrait de la page
        """
        logger.info(f"GPT-4o Vision: traitement page {page_number}")
        try:
            image_b64 = self._encode_image_base64(img)

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}",
                                    "detail": "high",  # high detail pour les documents juridiques
                                },
                            },
                            {"type": "text", "text": USER_PROMPT},
                        ],
                    },
                ],
                max_tokens=4096,
                temperature=0,  # 0 = déterministe, important pour l'extraction
            )

            extracted = response.choices[0].message.content or ""
            logger.info(
                f"Page {page_number}: {len(extracted)} caractères extraits"
            )
            return extracted.strip()

        except Exception as e:
            logger.error(f"Erreur GPT-4o Vision page {page_number}: {e}")
            raise

    def extract_all_pages(
        self, pdf_path: str
    ) -> List[Tuple[int, str]]:
        """
        Extrait le texte de toutes les pages d'un PDF.
        Vérifie d'abord le cache local avant d'appeler GPT-4o (payant).

        Args:
            pdf_path: Chemin vers le fichier PDF

        Returns:
            Liste de tuples (numéro_page, texte_extrait)
        """
        # ----------------------------------------------------------------
        # Vérification du cache — évite de payer GPT-4o pour un doublon
        # ----------------------------------------------------------------
        cached = get_cached_pages(pdf_path)
        if cached is not None:
            return cached

        logger.info(f"Début extraction GPT-4o: {pdf_path}")

        # Conversion PDF → images
        page_images = self.pdf_extractor.convert_to_images(pdf_path)

        results: List[Tuple[int, str]] = []
        for page_num, img in page_images:
            try:
                text = self.extract_text_from_image(img, page_num)
                if text:  # On garde seulement les pages avec du contenu
                    results.append((page_num, text))
            except Exception as e:
                logger.warning(f"Page {page_num} ignorée suite à erreur: {e}")
                continue

        logger.info(
            f"Extraction terminée: {len(results)}/{len(page_images)} pages traitées"
        )

        # ----------------------------------------------------------------
        # Sauvegarde dans le cache pour les prochaines insertions
        # ----------------------------------------------------------------
        if results:
            save_to_cache(pdf_path, results)

        return results
