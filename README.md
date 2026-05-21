# Bot RAG — Documents Juridiques Arabes 🇲🇦⚖️

> Système de **Retrieval-Augmented Generation (RAG)** pour interroger des documents juridiques en arabe (droit marocain).
> Dernière mise à jour de l'état : **23 avril 2026**

---

## 📊 État d'Avancement Global

```
█████████████████████░░░  85% — Fonctionnel, quelques correctifs à appliquer
```

---

## ✅ Composants Terminés (Opérationnels)

### Backend — FastAPI
- [x] `main.py` — Point d'entrée, cycle de vie, CORS
- [x] `config.py` — Configuration centralisée via `.env` (pydantic-settings)
- [x] `api/routes/documents.py` — Upload, liste, statut, suppression de PDFs
- [x] `api/routes/chat.py` — Pipeline RAG complet (question → réponse + sources)
- [x] `api/routes/health.py` — Endpoint de santé système (`/api/health`)
- [x] `models/request_models.py` — Schémas Pydantic (ChatRequest, DeleteDocumentRequest)
- [x] `models/response_models.py` — Schémas Pydantic (ChatResponse, SourceReference, etc.)

### Core — Pipeline RAG
- [x] `core/ingestion/extractor.py` — Métadonnées PDF + détection scan (seuil 50 chars/page)
- [x] `core/ingestion/pymupdf_text_extractor.py` — Extraction gratuite PDFs born-digital
- [x] `core/ingestion/gpt4o_extractor.py` — OCR via GPT-4o Vision (PDFs scannés, ~$0.01/page)
- [x] `core/ingestion/arabic_normalizer.py` — Normalisation arabe (diacritiques, alef, unicode)
- [x] `core/ingestion/chunker.py` — Chunking avec séparateurs arabes (`،` `؛` `؟`)
- [x] `core/embedding/embedder.py` — BGE-M3 Singleton, préfixes `query:` / `passage:`
- [x] `core/retrieval/vector_store.py` — ChromaDB persistant, similarité cosine
- [x] `core/retrieval/reranker.py` — BGE-Reranker-v2-M3, fallback sur score ChromaDB
- [x] `core/generation/llm.py` — Llama 3.3-70B via Groq, prompt système en arabe

### Frontend — React/Vite
- [x] `App.jsx` — Layout sidebar + zone chat
- [x] `components/Chat/ChatWindow.jsx` — Interface chat avec suggestions arabes
- [x] `components/Chat/InputBar.jsx` — Barre de saisie
- [x] `components/Chat/MessageBubble.jsx` — Bulles avec détection RTL + support Markdown
- [x] `components/Documents/UploadZone.jsx` — Drag & drop PDF
- [x] `components/Documents/DocumentList.jsx` — Liste avec polling statut (4s)
- [x] `components/Layout/Header.jsx` — En-tête + bouton clear chat
- [x] `components/Sources/SourceCard.jsx` — Affichage source (doc + page + score %)
- [x] `hooks/useChat.js` — State management messages + session UUID
- [x] `services/api.js` — Appels axios (timeout 120s pour GPT-4o)

---

## ⚠️ Bugs Identifiés & Correctifs Nécessaires

### 🔴 Critique — À corriger avant démo

| # | Problème | Fichier | Correctif |
|---|---------|---------|-----------|
| 1 | `AUTO_DETECT_EXTRACTION=false` dans `.env` mais `OPENAI_API_KEY` est un placeholder (`sk-VOTRE_CLE_ICI`) → **tous les uploads plantent** | `backend/.env` ligne 7 et 36 | Mettre `AUTO_DETECT_EXTRACTION=true` **OU** renseigner une vraie clé OpenAI |
| 2 | **Poppler** requis par `pdf2image` mais non installé par défaut sur Windows → plantage à l'upload de PDF scanné | Système | Installer Poppler et l'ajouter au PATH |
| 3 | **Clé API Groq** doit être configurée dans `.env` sinon les requêtes chat échouent | `backend/.env` | Renseigner `GROQ_API_KEY` |

### 🟡 Moyen — Impact fonctionnel partiel

| # | Problème | Fichier | Correctif |
|---|---------|---------|-----------|
| 4 | `_documents_registry` en mémoire → **perdu au redémarrage** du backend (chunks ChromaDB intacts mais UI vide) | `backend/app/api/routes/documents.py` ligne 40 | Persister dans `registry.json` ou SQLite |
| 5 | Pas de vérification du **MIME type réel** du fichier uploadé (seulement l'extension `.pdf`) | `documents.py` ligne 123 | Utiliser `python-magic` ou `fitz.open()` pour vérifier |
| 6 | `camel-tools` données morphologiques non installées → fallback regex (qualité de normalisation réduite) | Système | `camel_data -i morphology-db-msa-r13` |

### 🟢 Mineur — Améliorations futures

| # | Amélioration | Priorité |
|---|-------------|---------|
| 7 | Streaming des réponses LLM (éviter attente blanche) | Basse |
| 8 | Affichage de l'endpoint `/api/health` dans l'UI (indicateur de statut) | Basse |
| 9 | Mise à jour des dépendances (ChromaDB 0.5→0.6, torch 2.3→2.5) | Basse |
| 10 | `docker-compose.yml` pour déploiement simplifié | Basse |
| 11 | Pagination de la liste des documents | Basse |

---

## 🚀 Démarrage Rapide (État Actuel)

### ⚡ Correction `.env` préalable obligatoire
```bash
# Dans backend/.env — vérifier :
AUTO_DETECT_EXTRACTION=true   # évite GPT-4o sans clé valide
GROQ_API_KEY=gsk_...           # clé API Groq (gratuit sur console.groq.com)
```

### Étape 1 — Backend
```bash
cd "RAG project/backend"

# Créer l'environnement virtuel
python -m venv venv311
venv311\Scripts\activate          # Windows

# Installer les dépendances
pip install -r requirements.txt
camel_data -i morphology-db-msa-r13   # Données morphologiques arabes

# Lancer l'API
uvicorn app.main:app --reload --port 8000
```

### Étape 3 — Frontend
```bash
cd "RAG project/frontend"
npm install
npm run dev
# → http://localhost:5173
```

### Étape 4 — Vérification
```bash
# Santé du système
curl http://localhost:8000/api/health

# Documentation Swagger
http://localhost:8000/docs
```

---

## 🗺️ Pipeline RAG — Vue d'Ensemble

```
PDF Upload
    │
    ├─ PDF textuel ? ──→ PyMuPDF (gratuit)
    └─ PDF scanné ?  ──→ GPT-4o Vision (~$0.01/page)
                              │
                    ArabicNormalizer
                    (diacritiques, alef, unicode)
                              │
                    ArabicChunker
                    (512 tokens, overlap 64)
                              │
                    BGE-M3 Embedder
                    (BAAI/bge-m3, ~570MB)
                              │
                         ChromaDB ◄─────────────────────────┐
                                                             │
Question Utilisateur                                         │
    │                                                        │
ArabicNormalizer ──→ BGE-M3 embed_query ──→ ChromaDB (Top-20)
                                                    │
                                         BGE-Reranker-v2-M3 (Top-5)
                                                    │
                                         Llama 3.3-70B via Groq
                                                    │
                                    Réponse + Sources (doc + page + score)
```

---

## Stack Technologique

| Composant | Technologie | Statut |
|---|---|---|
| **Extraction PDFs textuels** | PyMuPDF (gratuit) | ✅ Opérationnel |
| **Extraction PDFs scannés** | GPT-4o Vision | ⚠️ Clé API requise |
| **Normalisation Arabe** | CAMeL Tools + PyArabic | ✅ Avec fallback regex |
| **Embeddings** | BGE-M3 (BAAI, gratuit) | ✅ Opérationnel |
| **Base Vectorielle** | ChromaDB (persistant) | ✅ Opérationnel |
| **Reranker** | BGE-Reranker-v2-M3 (gratuit) | ✅ Avec fallback |
| **LLM** | Llama 3.3-70B via Groq (API cloud) | ✅ Clé API gratuite |
| **Backend** | FastAPI + Uvicorn | ✅ Opérationnel |
| **Frontend** | React 19 + Vite 8 | ✅ Opérationnel |

---

## Structure du Projet

```
RAG project/
├── backend/
│   ├── app/
│   │   ├── main.py                      ✅
│   │   ├── config.py                    ✅
│   │   ├── api/routes/
│   │   │   ├── documents.py             ✅ (registry non persisté ⚠️)
│   │   │   ├── chat.py                  ✅
│   │   │   └── health.py                ✅
│   │   ├── core/
│   │   │   ├── ingestion/               ✅
│   │   │   ├── embedding/               ✅
│   │   │   ├── retrieval/               ✅
│   │   │   └── generation/              ✅
│   │   └── models/                      ✅
│   ├── chroma_db/                       (généré au runtime)
│   ├── uploads/                         (généré au runtime)
│   ├── .env                             ⚠️ Corriger AUTO_DETECT_EXTRACTION
│   └── requirements.txt                 ✅
└── frontend/
    ├── src/
    │   ├── components/                  ✅ (Chat, Documents, Layout, Sources)
    │   ├── hooks/useChat.js             ✅
    │   └── services/api.js              ✅
    └── package.json                     ✅
```

---

## Auteurs

**ESSABIRI YOUNESS & ABCHIR WAIL** — INPT 2025-2026
