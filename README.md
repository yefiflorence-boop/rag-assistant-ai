# ONEAD Assistant RAG

> Assistant IA documentaire interne basé sur l'approche **RAG (Retrieval-Augmented Generation)**
> Répond aux questions RH à partir des documents internes de l'ONEAD — avec sources citées.

---

## Présentation

**ONEAD Assistant RAG** est un MVP d'assistant documentaire intelligent développé pour l'Office National de l'Eau et de l'Assainissement de Djibouti.

L'utilisateur pose une question en langage naturel. Le système :
1. Recherche les passages pertinents dans les documents internes indexés (top-5 ChromaDB)
2. Génère une réponse concise basée **uniquement** sur ces passages (Azure OpenAI, streaming SSE)
3. Cite les sources PDF avec numéro de page réel (`Source : nom.pdf — p. N`)
4. Refuse poliment avec recours DRH si l'information n'est pas dans le corpus

Interface actuelle : **frontend React + TypeScript (Vite)** + **backend FastAPI** (`api.py`).
L'ancienne interface Streamlit (`app.py`) a été **supprimée** — ne plus utiliser `streamlit run`.

---

## Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| Interface de chat | Frontend React Enterprise : header fixe, sidebar 290px, hero premium, fil 1080px, thèmes sombre/clair |
| Recherche sémantique | Similarité cosinus sur vecteurs ChromaDB, filtre par seuil `SIMILARITY_THRESHOLD` |
| Génération IA | Réponse en streaming SSE via Azure OpenAI (`POST /api/chat/stream`, events `token` puis `done`, repli `POST /api/chat`) |
| Sources citées | Lignes texte simples collées à la réponse (`ChatThread.tsx`), visionneuse PDF intégrée (`DocViewer.tsx`, pdfjs-dist) + ouverture blob nouvel onglet `#page=N` sans téléchargement |
| Refus contrôlé | Message unique + carte Recours DRH + journalisation `data/feedback/unanswered.jsonl` |
| Formats des données | Ingestion PDF avec numéros de page réels (fallback OCR `fra`) |
| Traçabilité | Sidebar « Base à jour · N docs » + `data/manifest.json` (date, SHA-256, nb chunks, modèle) |

---

## Architecture RAG

```text
Question utilisateur (Composer.tsx)
        │
        ▼
┌───────────────────┐
│  Embeddings Azure │  → Transforme la question en vecteur (text-embedding-3-large)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│    ChromaDB       │  → Recherche les 5 passages les plus proches (filtre score <= seuil)
└────────┬──────────┘  (chat_context.py:search_with_scores)
         │
         ▼
┌───────────────────┐
│  Prompt augmenté  │  → Question + contexte + règles (chat_context.py:build_prompt)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Azure OpenAI LLM │  → Génère la réponse en streaming (gpt-4.1-mini, temperature=0.2)
└────────┬──────────┘  (api.py:_answer_sync / chat_stream)
         │
         ▼
  Réponse + Sources : fichier.pdf — p. N (+ extrait cité dans la visionneuse)
```

## Architecture système déployée

```text
Navigateur ──HTTP──▶ Frontend Vite :5173 ──/api + /files (proxy)──▶ Backend FastAPI :8000 (api.py)
                                                                          │  .env (clés Azure, jamais commité)
                                                                          ├─▶ ChromaDB locale (data/chroma_db/, rebuild via indexation.py)
                                                                          ├─▶ Azure OpenAI Embeddings (question → vecteur)
                                                                          ├─▶ Azure OpenAI Chat gpt-4.1-mini (réponse streamée SSE)
                                                                          └─▶ data/raw/*.pdf servis via GET /files/docs/{nom} (inline, #page=N)
                                                                               + data/manifest.json (fraîcheur base)
```

Pas de Streamlit, pas de base externe : un processus FastAPI + fichiers locaux + APIs Azure + SPA React.

---

## Structure du projet (à jour)

```text
rag-assistant-ai/
│
├── api.py                  # Backend FastAPI (point d'entrée : uvicorn api:app --port 8000)
├── chat_context.py         # Init RAG, recherche scorée, prompt, refus, manifest, logging
│
├── start.ps1               # Lancement unifié (API + frontend, checks, logs en direct)
├── stop.ps1                # Arrêt des 2 processus (arbre complet, par PID et par port)
├── demarrer.bat            # Lanceur double-clic (mode dev, :5173 + :8000)
├── arreter.bat             # Lanceur double-clic (arrêt)
├── demo.bat                # Lanceur double-clic (mode démo, 1 processus, 1 origine :8000)
│
├── src/
│   ├── config.py           # Chemins + seuils + contacts DRH (source unique)
│   ├── extraction.py       # PDF → data/output/*.pages.json (page par page + OCR si < 30 car.)
│   ├── chunking.py         # pages → data/chunks/*_chunks.json (800 car., overlap 100, page gardée)
│   └── indexation.py       # chunks → data/chroma_db/ + data/manifest.json (rebuild complet)
│
├── frontend/               # SPA React + TypeScript (Vite)
│   ├── vite.config.ts      # host 127.0.0.1:5173, proxy /api + /files → 127.0.0.1:8000, VITE_API_URL supporté
│   ├── package.json        # react 18, pdfjs-dist, vite 5, typescript 5
│   ├── index.html
│   ├── public/logo.svg     # Logo ONEAD vectoriel (fond transparent, sans cadre)
│   └── src/
│       ├── main.tsx        # Entrée React
│       ├── App.tsx         # État global : conversations, thème, streaming + repli non-streamé
│       ├── types.ts        # Source, ChatMessage, Conversation, Manifest, DrhContact, ChatDone
│       ├── index.css       # Design system (app 1480px, sidebar 290px, main 1080px, responsive)
│       ├── lib/api.ts      # Client REST + SSE (API_BASE = VITE_API_URL ou '' via proxy Vite)
│       └── components/
│           ├── Header.tsx      # Marque ONEAD + titre + avatar
│           ├── Sidebar.tsx     # Nouvelle conversation, recherche, 8 récentes (sans puces), base, thème, aide
│           ├── HomeHero.tsx    # Logo + question + 4 cartes suggestions (sans sous-titre)
│           ├── ChatThread.tsx  # Bulles, typing/caret limités au message en streaming, sources en lignes, carte DRH
│           ├── Composer.tsx    # Saisie simple (Enter = envoyer, pas de barre d'outils)
│           ├── DocViewer.tsx   # Visionneuse pdfjs (blob + #page=N, zoom, Échap/flèches, extrait cité)
│           ├── OneadLogo.tsx   # Logo vectoriel goutte bleue + feuille verte (sombre/clair)
│           └── icons.tsx       # SVG monochromes (zéro emoji)
│
├── data/
│   ├── raw/                # Documents bruts à indexer (5 PDF versionnés)
│   ├── output/             # *.pages.json [{page, text}] (ignoré par git)
│   ├── chunks/             # *_chunks.json [{id, content, source, page}] (ignoré par git)
│   ├── chroma_db/          # Base vectorielle persistante (ignorée par git, à reconstruire)
│   ├── manifest.json       # Traçabilité : 2026-10-08, 5 docs, 3201 chunks, text-embedding-3-large
│   └── feedback/           # unanswered.jsonl (questions sans réponse, ignoré par git)
│
├── logs/                   # Logs start.ps1 (backend.log, frontend.log) — ignoré par git
├── .run/                   # PIDs des processus (api.pid, web.pid) — ignoré par git
│
├── tests/
│   ├── 20_questions.csv    # Jeu de 20 questions (nominal / hors_corpus / ambigu / multi_doc)
│   ├── eval_rag.py         # Éval offline + option --with-llm
│   └── rapport_fiabilite.md# Dernier rapport : 15 PASS / 5 PARTIEL / 0 FAIL (2026-10-08, base 3201 chunks)
│
├── notebooks/extraction.ipynb  # Exploration extraction (non rejoué en CI)
├── .env                    # Clés API + seuils (jamais commité)
├── .gitignore              # Exclut .env, output/chunks/chroma_db, unanswered.jsonl, node_modules, dist, logs, .run
├── requirements.txt        # Dépendances Python backend (pip freeze UTF-8, tout en un seul fichier)
└── README.md               # Ce fichier
```

Fichiers **supprimés** au fil du projet : `app.py` (Streamlit), `static/` (dossier vide,
les PDF sont servis depuis `data/raw/` via `/files/docs`), `src/test.py` (snippet ad hoc
à chemin absolu), `frontend/public/logo.png` (le SVG suffit), `.streamlit/config.toml`.

---

## Installation

### Prérequis

- Python **3.10+**
- Node.js **20+** (frontend)
- Un compte **Azure OpenAI**
- Un déploiement de chat (`CHAT_MODEL`, ex. `gpt-4.1-mini`)
- Un déploiement d'embedding (`EMBEDDING_MODEL`, ex. `text-embedding-3-large`)
- Binaires OCR : **Tesseract** (pack langue `fra`) + **poppler** (requis seulement pour les pages scannées)
- Créer un fichier `.env` (jamais commité) avec :

```text
OPENAI_API_KEY
CHAT_MODEL
API_ENDPOINT_GPT
EMBEDDING_MODEL
API_ENDPOINT_EMBEDDING
# Optionnels : DB_DIR, SIMILARITY_THRESHOLD (défaut 1.0), TOP_K (5), MAX_SOURCES (3), DRH_EMAIL, DRH_TEL
# Frontend seul : VITE_API_URL (ex. http://127.0.0.1:8000 si le proxy Vite est inactif)
```

### 1. Cloner le dépôt

```powershell
git clone https://github.com/yefiflorence-boop/rag-assistant-ai
cd rag-assistant-ai
```

### 2. Backend Python

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend React

```powershell
cd frontend
npm install
```

---

## Lancement

### Lancement unifié (recommandé) — une seule commande

**Double-clic** sur `demarrer.bat` (ou en ligne de commande) :

```powershell
.\demarrer.bat
# ou
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

Le script démarre les deux serveurs, attend que la base RAG soit préchargée, affiche les
URLs et ouvre http://localhost:5173 dans le navigateur. **Ctrl+C** dans la fenêtre
arrête proprement les deux processus (logs en direct `[API]` / `[WEB]`).

```powershell
.\stop.ps1            # arrêt manuel (backend + frontend, par PID et par port)
.\arreter.bat         # idem en double-clic
.\start.ps1 -NoBrowser   # sans ouvrir le navigateur
```

| Fichier | Rôle |
|---|---|
| `start.ps1` | vérifie l'environnement, lance API + frontend, affiche les logs en direct |
| `stop.ps1` | arrête les deux processus (PID dans `.run\`, puis par port 8000/5173) |
| `demarrer.bat` / `arreter.bat` | lanceurs double-clic Windows |
| `demo.bat` | **mode démonstration** : 1 processus, 1 seule origine (`:8000`) |

Fichiers générés (ignorés par git) : `logs/backend.log`, `logs/frontend.log`,
`.run/api.pid`, `.run/web.pid`.

### Mode démonstration — une seule origine (1 processus)

```powershell
.\demo.bat
# ou : powershell -ExecutionPolicy Bypass -File .\start.ps1 -Single
```

`npm run build` puis FastAPI sert **l'API et l'interface** sur
**http://127.0.0.1:8000** (montage `StaticFiles` de `frontend/dist`, activé par
`SERVE_FRONTEND=1`). Plus de proxy Vite, plus de CORS, une seule URL à retenir.
Le build est refait à chaque lancement (≈35 s) pour que la démo montre toujours
le code actuel.

### Dans Visual Studio Code

- `Ctrl+Shift+B` → **Start full stack** (API `:8000` + Vite `:5173` en parallèle).
- `F5` → **Debug API** (points d'arrêt dans `api.py` / `chat_context.py`).
- Panneau *Tasks* → *Build frontend*, *Reindexer le corpus*, *Evaluer la fiabilite*.

### Lancement manuel (2 terminaux)

#### Étape 1 — Indexer les documents (une seule fois, à refaire si `data/raw/` change)

```powershell
python src/extraction.py
python src/chunking.py
python src/indexation.py
```

La base vectorielle est créée dans `data/chroma_db/` + `data/manifest.json` (2026-10-08 : 3201 chunks paginés).

#### Étape 2 — Lancer le backend

```powershell
uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

Vérifier `http://127.0.0.1:8000/api/health` → `{"status":"ok","rag_loaded":...}` (`rag_loaded` devient vrai après pré-chargement en tâche de fond).

#### Étape 3 — Lancer le frontend

```powershell
cd frontend
npm run dev
```

Ouvrir **http://localhost:5173** (Vite proxifie `/api` et `/files` vers `127.0.0.1:8000` ; sinon renseigner `VITE_API_URL`).

Build production : `npm run build` (`tsc --noEmit && vite build` → `frontend/dist/`) puis `npm run preview`.

---

## Tests

```powershell
python tests/eval_rag.py              # offline : retrieval lexical sur data/chunks, sans clé
python tests/eval_rag.py --with-llm   # + 5 questions réelles ChromaDB + Azure (si .env présent)
```

Jeu `tests/20_questions.csv` : `nominal` (12 Q), `hors_corpus` (4 Q, refus attendu), `ambigu` (2 Q), `multi_doc` (2 Q).
Dernier `tests/rapport_fiabilite.md` : **15 PASS / 5 PARTIEL / 0 FAIL** — régénéré sur la
base courante (2026-10-08, 3201 chunks, `text-embedding-3-large`). Les 5 PARTIEL
portent sur des questions nominales dont la source attendue n'apparaît pas dans les
passages récupérés (critère lexical de l'éval offline, pas un défaut de l'application).

---

## Stack technique

| Besoin | Outil |
|---|---|
| Langage | Python 3.10+ |
| Backend API | FastAPI 0.115.12 + Uvicorn 0.46.0 (SSE `text/event-stream`) |
| Interface | React 18 + TypeScript 5 + Vite 5 (`frontend/`) |
| Visionneuse PDF | pdfjs-dist (canvas, blob + `#page=N`) |
| Extraction PDF | PyMuPDF 1.27.2.3 (`fitz`), fallback OCR `pytesseract` (lang `fra`) + `pdf2image` (+ Tesseract/poppler système) |
| Découpage | `langchain-text-splitters` / `RecursiveCharacterTextSplitter` (800 car., overlap 100) |
| Embeddings | Azure OpenAI `text-embedding-3-large` (`langchain-openai`) |
| Base vectorielle | ChromaDB 1.5.9 persistée sur disque (`langchain-chroma`, espace `cosine`) |
| LLM | Azure OpenAI `gpt-4.1-mini`, `temperature=0.2`, `api_version="2024-10-21"` |
| Orchestration | LangChain / langchain-core |
| Config / secrets | `python-dotenv` (`.env`, jamais commité) + `VITE_API_URL` côté frontend |
| Versioning | Git / GitHub |

---

## Dépendances principales

Backend (`requirements.txt`, pip freeze) :

```text
fastapi==0.115.12
uvicorn==0.46.0
starlette==0.46.2
chromadb==1.5.9
langchain / langchain-openai / langchain-community / langchain-text-splitters
pymupdf==1.27.2.3
pdf2image + pytesseract (+ binaires système Tesseract fra / poppler)
python-dotenv
```

Frontend (`frontend/package.json`) :

```text
react / react-dom 18.3.1
pdfjs-dist ^6.4.299
vite ^5.4.0 + @vitejs/plugin-react + typescript ^5.4.5
```

> Listes complètes dans `requirements.txt` et `frontend/package.json` (+ `frontend/package-lock.json`).

---

## Équipe

Projet réalisé dans le cadre de la formation **AI Engineering** — Groupe 1

Projet à usage interne : Projet pédagogique ONEAD / Formation AI Engineering
