"""
ocr_cache.py — Cache local des résultats OCR (GPT-4o Vision)
Évite de repayer OpenAI si le même PDF est soumis plusieurs fois.
Utilise le hash SHA-256 du fichier comme clé unique.
"""
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Dossier où le cache JSON sera stocké
CACHE_DIR = Path(__file__).parent.parent.parent.parent / "ocr_cache"
CACHE_FILE = CACHE_DIR / "ocr_results.json"


def _compute_sha256(pdf_path: str) -> str:
    """
    Calcule le hash SHA-256 d'un fichier PDF.
    Deux fichiers identiques produiront toujours le même hash.
    """
    sha256 = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        # Lecture par blocs pour ne pas charger tout le PDF en RAM
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


def _load_cache() -> dict:
    """Charge le fichier JSON du cache (ou retourne un dict vide)."""
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Cache illisible, réinitialisation: {e}")
        return {}


def _save_cache(cache: dict) -> None:
    """Sauvegarde le cache dans le fichier JSON."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def get_cached_pages(pdf_path: str) -> Optional[List[Tuple[int, str]]]:
    """
    Vérifie si le PDF a déjà été traité par GPT-4o.

    Args:
        pdf_path: Chemin vers le fichier PDF

    Returns:
        Liste de (numéro_page, texte) si trouvé dans le cache, sinon None.
    """
    file_hash = _compute_sha256(pdf_path)
    cache = _load_cache()

    if file_hash in cache:
        entry = cache[file_hash]
        filename = entry.get("filename", "inconnu")
        cached_at = entry.get("cached_at", "date inconnue")
        logger.info(
            f"✅ Cache HIT — '{filename}' déjà traité le {cached_at}. "
            f"GPT-4o non appelé (économie ~${len(entry['pages']) * 0.01:.2f})"
        )
        # Reconvertir la liste JSON en liste de tuples
        return [(p[0], p[1]) for p in entry["pages"]]

    logger.info(f"Cache MISS — hash {file_hash[:12]}... → appel GPT-4o nécessaire")
    return None


def save_to_cache(
    pdf_path: str, pages: List[Tuple[int, str]]
) -> None:
    """
    Sauvegarde les résultats OCR dans le cache après un appel GPT-4o réussi.

    Args:
        pdf_path: Chemin vers le fichier PDF
        pages: Liste de (numéro_page, texte_extrait) retournée par GPT-4o
    """
    file_hash = _compute_sha256(pdf_path)
    cache = _load_cache()

    cache[file_hash] = {
        "filename": Path(pdf_path).name,
        "cached_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "page_count": len(pages),
        # Sauvegarder les tuples comme listes (JSON ne supporte pas les tuples)
        "pages": [[page_num, text] for page_num, text in pages],
    }

    _save_cache(cache)
    logger.info(
        f"💾 Cache sauvegardé — '{Path(pdf_path).name}' "
        f"({len(pages)} pages) → {CACHE_FILE}"
    )
