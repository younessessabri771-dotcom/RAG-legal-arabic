# Plan du Projet — Bot RAG Juridique Arabe

## Architecture globale

```
PDF Juridique → Extraction → Embedding → ChromaDB → Retrieval → LLM → Réponse
```

---

## 🛠️ Technologies utilisées

### Backend (FastAPI)
| Rôle | Technologie |
|---|---|
| **API REST** | FastAPI + Python 3.11 |
| **Extraction PDF** (born-digital) | PyMuPDF |
| **Extraction PDF** (scanné) | GPT-4o Vision (OpenAI) |
| **Normalisation arabe** | CAMeL Tools + PyArabic |
| **Embeddings** | BGE-M3 (local, BAAI) |
| **Base vectorielle** | ChromaDB (local) |
| **Reranker** | BGE-Reranker-v2-M3 (local) |
| **LLM génération** | llama3.2 via Ollama (local, gratuit) |

### Frontend (React)
| Rôle | Technologie |
|---|---|
| **Framework** | React + Vite |
| **Design** | RTL (arabe), thème sombre/doré |
| **Upload** | Drag & Drop avec polling statut |

---

## 🔄 Pipeline RAG (étape par étape)

1. **Upload PDF** → détection auto (textuel ou scanné)
2. **Extraction** → PyMuPDF (gratuit) ou GPT-4o (payant)
3. **Normalisation** → nettoyage texte arabe
4. **Chunking** → découpage adapté à l'arabe
5. **Embedding** → BGE-M3 encode les chunks
6. **Stockage** → ChromaDB enregistre les vecteurs
7. **Question** → l'utilisateur pose une question en arabe
8. **Retrieval** → BGE-M3 trouve les chunks pertinents
9. **Reranking** → BGE-Reranker trie les meilleurs résultats
10. **Génération** → llama3.2 génère la réponse finale

---

## ⚠️ État actuel
- ✅ Backend + Frontend : opérationnels
- ✅ Modèles BGE-M3 + Reranker : chargés
- ✅ llama3.2 : installé, optimisé pour CPU
- ⏳ Clé OpenAI : à configurer (pour PDFs scannés uniquement)

---

## 🚀 Démarrer et Arrêter le Système

### 1. Ollama (Moteur IA local — Gratuit)
- **Démarrer** : Ouvrez un terminal et tapez `ollama serve`
- **Arrêter** : Fermez le terminal ou tapez `Ctrl+C`

### 2. Backend (FastAPI — Package Python — Gratuit)
- **Démarrer** :
  ```bash
  cd backend
  .\venv311\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
  ```
- **Arrêter** : Cliquez dans le terminal et appuyez sur `Ctrl+C`

### 3. Frontend (React/Vite — Package Node.js — Gratuit)
- **Démarrer** :
  ```bash
  cd frontend
  npm run dev
  ```
- **Arrêter** : Cliquez dans le terminal et appuyez sur `Ctrl+C`
