# Bot RAG — Assistant Juridique Marocain 🇲🇦⚖️

Système de **Retrieval-Augmented Generation (RAG)** pour indexer et interroger des documents juridiques en arabe (droit marocain).

![Interface d'accueil](home.png)
![Démo d'utilisation](demo.png)

---

## 🏗️ Architecture & Fonctionnalités

- **Extraction Hybride** : Détection auto du format PDF (textuel via **PyMuPDF** ou scanné via **GPT-4o Vision**).
- **Prétraitement NLP** : Normalisation de l'arabe (**CAMeL Tools**, **PyArabic**) et découpage sémantique adapté.
- **Recherche & Reranking** : Indexation dans **ChromaDB** avec embeddings **BGE-M3**, suivie d'un re-classement par **BGE-Reranker-v2-M3** (Top-5).
- **Interface Graphique** : UI moderne en React avec support RTL (Right-to-Left).

---

## 🛠️ Stack Technologique Détaillée

### Backend (FastAPI)
*   **FastAPI** (Type : Package de programmation Python | Statut : Free) : Framework web asynchrone performant pour l'exposition des API REST.
*   **Uvicorn** (Type : Package de programmation Python | Statut : Free) : Serveur web ASGI pour exécuter l'application backend.
*   **PyMuPDF** (Type : Package de programmation Python | Statut : Free) : Extraction rapide du texte pour les documents PDF natifs.
*   **GPT-4o Vision** (Type : API Cloud installée via le package de programmation Python `openai` | Statut : Payant) : Modèle de vision par ordinateur pour l'OCR des PDF scannés.
*   **CAMeL Tools** (Type : Package de programmation Python | Statut : Free) : Prétraitement morphologique et normalisation de la langue arabe.
*   **PyArabic** (Type : Package de programmation Python | Statut : Free) : Utilitaires de manipulation de chaînes en langue arabe.
*   **ChromaDB** (Type : Package de programmation Python | Statut : Free) : Base de données vectorielle persistante légère stockée localement.
*   **BGE-M3 & BGE-Reranker-v2-M3** (Type : Modèles Hugging Face chargés via le package de programmation Python `sentence-transformers` | Statut : Free) : Modèles d'intelligence artificielle locaux pour l'embedding et le reranking.
*   **Llama 3.3** via **Groq** (Type : Service d'inférence API Cloud installé via le package de programmation Python `groq` | Statut : Free avec quota gratuit) : Modèle de langage (LLM) pour la génération de réponses juridiques précises.
*   **Poppler** (Type : Logiciel système installé depuis un site web | Statut : Free) : Requis par le package Python `pdf2image` pour le rendu de documents PDF sous forme d'images destinées à l'OCR.

### Frontend (React)
*   **React** (Type : Package de programmation JavaScript/Node.js | Statut : Free) : Bibliothèque pour la création de composants utilisateur interactifs.
*   **Vite** (Type : Package de programmation JavaScript/Node.js | Statut : Free) : Outil de build et serveur de développement rapide.
*   **Axios** (Type : Package de programmation JavaScript/Node.js | Statut : Free) : Client HTTP pour communiquer avec les endpoints FastAPI.

### Prérequis Généraux
*   **Python** (Type : Langage de programmation installé depuis un site web | Statut : Free) : Version 3.11 requise pour le backend.
*   **Node.js** (Type : Environnement d'exécution JavaScript installé depuis un site web | Statut : Free) : Version 18+ requise pour le frontend.

---

## 🚀 Démarrage Rapide

### 1. Variables d'Environnement (`backend/.env`)
```env
AUTO_DETECT_EXTRACTION=true
GROQ_API_KEY=gsk_le_cle_groq
```

### 2. Backend
```bash
cd backend
python -m venv venv311
venv311\Scripts\activate
pip install -r requirements.txt
camel_data -i morphology-db-msa-r13
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
