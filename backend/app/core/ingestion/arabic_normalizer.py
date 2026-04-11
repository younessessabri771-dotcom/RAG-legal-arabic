"""
arabic_normalizer.py — Normalisation du texte arabe extrait des documents juridiques
Utilise camel-tools et pyarabic pour nettoyer et uniformiser le texte
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Importation conditionnelle de camel-tools (nécessite installation séparée des données)
try:
    from camel_tools.utils.normalize import (
        normalize_alef_ar,
        normalize_alef_maksura_ar,
        normalize_teh_marbuta_ar,
        normalize_unicode,
    )
    from camel_tools.utils.dediac import dediac_ar
    CAMEL_AVAILABLE = True
except ImportError:
    logger.warning(
        "camel-tools non disponible. Utilisez: pip install camel-tools "
        "puis: camel_data -i morphology-db-msa-r13"
    )
    CAMEL_AVAILABLE = False

try:
    import pyarabic.araby as araby
    PYARABIC_AVAILABLE = True
except ImportError:
    logger.warning("pyarabic non disponible. pip install pyarabic")
    PYARABIC_AVAILABLE = False


class ArabicNormalizer:
    """
    Normalise le texte arabe extrait des documents juridiques :
    - Suppression des diacritiques (تشكيل)
    - Normalisation des variantes de alef (أ إ آ ا → ا)
    - Normalisation Unicode
    - Nettoyage des espaces et caractères spéciaux
    - Préservation de la ponctuation arabe (، ؟ ؛)
    """

    def normalize(self, text: str) -> str:
        """
        Applique toutes les normalisations au texte arabe.
        """
        if not text or not text.strip():
            return ""

        # 1. Normalisation Unicode
        text = self._normalize_unicode(text)

        # 2. Suppression des diacritiques
        text = self._remove_diacritics(text)

        # 3. Normalisation des variantes de lettres arabes
        text = self._normalize_letters(text)

        # 4. Nettoyage des espaces multiples
        text = self._clean_whitespace(text)

        # 5. Suppression des caractères de contrôle indésirables
        text = self._remove_control_chars(text)

        return text.strip()

    def _normalize_unicode(self, text: str) -> str:
        """Normalise l'Unicode (форма NFC)."""
        import unicodedata
        text = unicodedata.normalize("NFC", text)
        if CAMEL_AVAILABLE:
            try:
                text = normalize_unicode(text)
            except Exception:
                pass
        return text

    def _remove_diacritics(self, text: str) -> str:
        """Supprime les diacritiques arabes (تشكيل)."""
        if CAMEL_AVAILABLE:
            try:
                return dediac_ar(text)
            except Exception:
                pass
        if PYARABIC_AVAILABLE:
            try:
                return araby.strip_diacritics(text)
            except Exception:
                pass
        # Fallback: regex pour supprimer les diacritiques
        diacritics_pattern = re.compile(
            r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]"
        )
        return diacritics_pattern.sub("", text)

    def _normalize_letters(self, text: str) -> str:
        """Normalise les variantes de lettres (alef, teh marbuta, etc.)."""
        if CAMEL_AVAILABLE:
            try:
                text = normalize_alef_ar(text)       # أ إ آ → ا
                text = normalize_alef_maksura_ar(text) # ى → ي
                text = normalize_teh_marbuta_ar(text)  # ة → ه
                return text
            except Exception:
                pass
        # Fallback manuelle
        text = re.sub(r"[أإآٱ]", "ا", text)  # Normalisation alef
        text = re.sub(r"ى", "ي", text)         # Alef maksura → ya
        return text

    def _clean_whitespace(self, text: str) -> str:
        """Nettoie les espaces multiples et les sauts de ligne excessifs."""
        # Remplace les espaces multiples par un seul
        text = re.sub(r"[ \t]+", " ", text)
        # Remplace les sauts de ligne multiples par maximum 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def _remove_control_chars(self, text: str) -> str:
        """Supprime les caractères de contrôle sauf les sauts de ligne."""
        return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

    def normalize_query(self, query: str) -> str:
        """
        Normalise une question utilisateur (même pipeline que les documents).
        """
        return self.normalize(query)
