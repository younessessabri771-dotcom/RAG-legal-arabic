"""
config.py — Paramètres globaux du projet (chargés depuis .env)
"""
from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # --- OpenAI (optionnel — requis uniquement pour les PDFs scannés) ---
    OPENAI_API_KEY: str = ""  # Laisser vide pour utiliser uniquement PyMuPDF

    # --- Groq (LLM Rapide) ---
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # --- Ollama (conservé pour fallback / usage local) ---
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    # --- ChromaDB ---
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "legal_docs_arabic"

    # --- Embeddings ---
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DEVICE: str = "cpu"

    # --- Chunking ---
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64

    # --- Retrieval ---
    TOP_K_RETRIEVAL: int = 20
    TOP_K_RERANK: int = 5

    # --- Uploads ---
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50

    # --- Extraction intelligente ---
    # True  = auto-détection (PyMuPDF si textuel, GPT-4o si scanné)
    # False = toujours GPT-4o Vision (plus précis mais payant)
    AUTO_DETECT_EXTRACTION: bool = True
    # Seuil de caractères par page pour détecter un PDF textuel (< seuil = scanné)
    SCAN_DETECTION_THRESHOLD: int = 50

    # --- API ---
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000"]'

    def get_cors_origins(self) -> List[str]:
        try:
            return json.loads(self.CORS_ORIGINS)
        except Exception:
            return ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
