# Bot RAG — Documents Juridiques Arabes 🇲🇦⚖️

Système de **Retrieval-Augmented Generation (RAG)** pour interroger des documents juridiques en arabe.

## Stack Technologique

| Composant | Technologie |
|---|---|
| **Extraction PDFs (textuels)** | PyMuPDF (gratuit) |
| **Extraction PDFs (scannés)** | GPT-4o Vision |
| **Normalisation Arabe** | CAMeL Tools + PyArabic |
| **Embeddings** | BGE-M3 (BAAI, gratuit) |
| **Base Vectorielle** | ChromaDB |
| **Reranker** | BGE-Reranker-v2-M3 (gratuit) |
| **LLM** | Qwen2.5-7B via Ollama (gratuit) |
| **Backend** | FastAPI |
| **Frontend** | React + Vite |

## Structure du Projet

```
RAG project/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/routes/
│   │   └── core/
│   ├── requirements.txt
│   └── .env.example        ← Copier en .env
└── frontend/
    ├── src/
    └── package.json
```

## Installation

### Prérequis
- Python >= 3.10
- Node.js >= 18
- [Ollama](https://ollama.com/download)
- [Poppler](https://github.com/oschwartz10612/poppler-windows/releases) (Windows)
- Clé API OpenAI (pour les PDFs scannés)

### Backend
```bash
cd backend
copy .env.example .env        # Windows
# nano .env                   # Linux/Mac
# → Renseigner OPENAI_API_KEY

pip install -r requirements.txt
camel_data -i morphology-db-msa-r13

ollama pull qwen2.5:7b
ollama serve &

uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Utilisation

1. Ouvrir `http://localhost:5173`
2. Uploader un PDF juridique arabe via la sidebar
3. Poser vos questions en arabe ou en français
4. Le système retourne la réponse avec les sources (document + page)

## Auteurs

ESSABIRI YOUNESS & ABCHIR WAIL — INPT 2025-2026
