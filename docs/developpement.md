# Développement — ONEAD Assistant RAG

## 1. Stack technique

| Besoin | Outil (voir `requirements.txt` + `frontend/package.json`) |
|---|---|
| Langage | Python 3.10+ (backend) + TypeScript 5 / React 18 (frontend) |
| Backend API | FastAPI 0.115.12 + Uvicorn 0.46.0 (`api.py`), SSE `text/event-stream` |
| Interface | React 18 + Vite 5 (`frontend/`, port 5173, proxy `/api` + `/files` → `127.0.0.1:8000`) |
| Visionneuse PDF | `pdfjs-dist` (canvas, blob + `#page=N`, zoom, clavier) |
| Extraction PDF | PyMuPDF (`fitz`), fallback OCR `pytesseract` (lang `fra`) + `pdf2image` (+ Tesseract/poppler système) |
| Découpage | `langchain-text-splitters` / `RecursiveCharacterTextSplitter` |
| Embeddings | Azure OpenAI `text-embedding-3-large` (`langchain-openai`) |
| Base vectorielle | ChromaDB 1.5.9 persistée sur disque (`langchain-chroma`, espace `cosine`) |
| LLM | Azure OpenAI `gpt-4.1-mini`, `temperature=0.2`, `api_version="2024-10-21"` |
| Config / secrets | `python-dotenv` (`.env`, jamais commité) + `VITE_API_URL` côté frontend |

L'ancienne interface Streamlit (`app.py`) est **supprimée**. Ne pas réintroduire `streamlit` dans les dépendances.

## 2. Structure du projet

```text
rag-assistant-ai/
├── api.py              # Backend FastAPI : lifespan warmup, /api/*, /files/docs/*, SSE
├── chat_context.py     # init RAG, recherche scorée, prompt, refus, manifest, logging
├── start.ps1           # Lancement unifié (API + frontend, checks, logs en direct)
├── stop.ps1            # Arrêt des 2 processus (arbre complet, par PID et par port)
├── demarrer.bat        # Lanceur double-clic (dev :5173 + :8000)
├── demo.bat            # Lanceur double-clic (démo : 1 processus, 1 origine :8000)
├── arreter.bat         # Lanceur double-clic (arrêt)
├── src/
│   ├── config.py       # Chemins + seuils + contacts DRH (source unique)
│   ├── extraction.py   # PDF → data/output/*.pages.json (page par page + OCR si < 30 car.)
│   ├── chunking.py     # pages → data/chunks/*_chunks.json (800 car., overlap 100, page gardée)
│   └── indexation.py   # chunks → data/chroma_db/ + data/manifest.json (rebuild complet)
├── frontend/
│   ├── vite.config.ts      # host 127.0.0.1:5173, proxy /api + /files → 127.0.0.1:8000 (changeOrigin)
│   ├── package.json        # react, pdfjs-dist, vite, typescript
│   ├── public/logo.svg     # Logo ONEAD vectoriel (transparent, sans cadre)
│   └── src/
│       ├── main.tsx        # Entrée React
│       ├── App.tsx         # Conversations, thème sombre/clair, streaming + repli non-streamé
│       ├── types.ts        # Source, ChatMessage, Conversation, Manifest, DrhContact, ChatDone
│       ├── index.css       # Design system : app 1480px, layout 290px + main 1080px, hero 960px, responsive
│       ├── lib/api.ts      # API_BASE (= VITE_API_URL ou ''), REST + SSE token/done/error
│       └── components/
│           ├── Header.tsx      # Marque ONEAD (OneadMark), titre, avatar
│           ├── Sidebar.tsx     # Nouvelle conversation, recherche, 8 récentes (titres seuls), base, thème, aide
│           ├── HomeHero.tsx    # Logo 128 + question + 4 cartes (pas de sous-titre)
│           ├── ChatThread.tsx  # Bulles, typing/caret limités au message en streaming (streamingId), sources en lignes, DRH
│           ├── Composer.tsx    # Textarea simple (Enter = envoyer)
│           ├── DocViewer.tsx   # Modale pdfjs : blob + #page=N, zoom 0.6–2.5, Échap/flèches, extrait cité
│           ├── OneadLogo.tsx   # Goutte bleue + feuille verte 100 % vectoriel
│           └── icons.tsx       # SVG monochromes, zéro emoji
├── data/
│   ├── raw/            # PDF à indexer (versionnés : 5 fichiers)
│   ├── output/         # *.pages.json [{page, text}] (ignoré par git)
│   ├── chunks/         # *_chunks.json [{id, content, source, page}] (ignoré par git)
│   ├── chroma_db/      # Base vectorielle (ignorée par git, à reconstruire)
│   ├── manifest.json   # 2026-10-08, 5 docs, 3201 chunks, text-embedding-3-large
│   └── feedback/       # unanswered.jsonl (questions sans réponse, ignoré par git)
├── logs/               # Logs de start.ps1 (ignorés par git)
├── .run/               # PIDs des processus (ignorés par git)
├── tests/
│   ├── 20_questions.csv
│   ├── eval_rag.py     # Éval offline (lexicale) + option --with-llm
│   └── rapport_fiabilite.md  # 15 PASS / 5 PARTIEL / 0 FAIL (2026-10-08, base 3201 chunks)
├── notebooks/extraction.ipynb
└── .env                # Clés (non versionné) — voir §3
```

Fichiers ignorés par git : `.env`, `.streamlit/secrets.toml`, `data/output/*`,
`data/chunks/*`, `data/chroma_db/*`, `data/feedback/unanswered.jsonl`,
`frontend/node_modules/`, `frontend/dist/`, `frontend/.vite/`, `logs/`, `.run/`.
Exception conservée : `!frontend/src/lib/` (versionne `frontend/src/lib/api.ts`).

Supprimés (ne plus documenter comme actifs) : `app.py`, `static/` (dossier vide),
`src/test.py`, `frontend/public/logo.png`, `.streamlit/config.toml`.

## 3. Configuration (`.env` + frontend)

Variables lues dans `chat_context.py:28-34`, `src/indexation.py:25-27`,
`src/config.py:25-33`, `frontend/src/lib/api.ts:5` :

| Variable | Obligatoire | Exemple / défaut | Usage |
|---|---|---|---|
| `OPENAI_API_KEY` | oui | `***` | Azure OpenAI (chat + embeddings) |
| `CHAT_MODEL` | oui | `gpt-4.1-mini` (nom de déploiement) | `AzureChatOpenAI(deployment_name=…)` |
| `API_ENDPOINT_GPT` | oui | `https://…openai.azure.com/…` | Endpoint chat |
| `EMBEDDING_MODEL` | oui | `text-embedding-3-large` | `AzureOpenAIEmbeddings(model=…)` |
| `API_ENDPOINT_EMBEDDING` | oui | `https://…openai.azure.com/…` | Endpoint embeddings |
| `DB_DIR` | non | `data/chroma_db` | Surcharge du dossier ChromaDB |
| `SIMILARITY_THRESHOLD` | non | `1.0` | Seuil de distance (voir §5) |
| `TOP_K` | non | `5` | Passages récupérés |
| `MAX_SOURCES` | non | `3` | Liens sources affichés |
| `DRH_EMAIL` / `DRH_TEL` | non | `drh@onead.dj` / `+253 21 35 00 00` | Carte recours DRH |
| `VITE_API_URL` (frontend) | non | `""` (proxy Vite) ou `http://127.0.0.1:8000` | Base URL absolue si proxy inactif (`frontend/src/lib/api.ts:5`) |

`src/config.py` centralise les chemins (`BASE_DIR`-relatifs) et constantes :
`REFUSAL_MESSAGE`, `DRH_CONTACT`, `TOP_K`, `MAX_SOURCES`, `SIMILARITY_THRESHOLD`.

## 4. Installation et lancement local

### 4.1 Lancement unifié (recommandé)

```powershell
# Un seul script : backend (:8000) + frontend (:5173), logs en direct, Ctrl+C = arrêt
.\demarrer.bat          # double-clic Windows
powershell -ExecutionPolicy Bypass -File .\start.ps1   # équivalent en ligne de commande

# Arrêt manuel (par PID et par port)
.\stop.ps1   ou   .\arreter.bat
```

`start.ps1` (racine) :

- vérifie l'environnement (`venv\Scripts\python.exe` → `.venv` → `python` du PATH, `.env`,
  `frontend/node_modules`, ports 8000/5173 libres) et s'arrête avec un message clair sinon ;
- lance `uvicorn api:app --reload` et `npm run dev -- --strictPort` en arrière-plan
  (logs dans `logs/backend.log` et `logs/frontend.log`, PID dans `.run/api.pid` / `.run/web.pid`) ;
- attend `GET /api/health` **et `rag_loaded: true`** (warmup ChromaDB + Azure, jusqu'à 120 s) ;
- affiche les URLs, ouvre `http://localhost:5173` (option `-NoBrowser`) ;
- affiche les logs des deux serveurs en direct (préfixes `[API]` / `[WEB]`) ;
- `Ctrl+C` → appelle `stop.ps1` (arrêt des deux processus, arborescence comprise).

Options : `-NoBrowser`, `-SkipChecks`. `stop.ps1` accepte `-Quiet`.

> Les dossiers `logs/` et `.run/` sont ignorés par git.

### 4.1 bis Mode démonstration (une seule origine)

```powershell
.\demo.bat
# ou : powershell -ExecutionPolicy Bypass -File .\start.ps1 -Single
```

- `npm run build` (`tsc --noEmit && vite build` → `frontend/dist/`, ≈35 s) ;
- FastAPI sert ensuite **l'API et le build React** sur `http://127.0.0.1:8000`
  (`SERVE_FRONTEND=1` → `app.mount("/", StaticFiles(directory="frontend/dist", html=True))`
  dans `api.py`, montage posé après les routes API) ;
- plus de proxy Vite, plus de CORS, une seule URL à retenir pour la présentation ;
- pas de HMR : toute modif du front exige un nouveau `demo.bat`.

Variables utiles : `SERVE_FRONTEND` (`1` pour activer le montage statique),
`VITE_API_URL` (URL absolue du backend si le proxy Vite est désactivé).

### 4.1 ter Dans Visual Studio Code

`.vscode/tasks.json` (compound tasks) et `.vscode/launch.json` (debug) :

| Action | Raccourci |
|---|---|
| Start full stack (API + Vite) | `Ctrl+Shift+B` |
| Debug API (points d'arrêt) | `F5` |
| Build frontend / Reindexer / Evaluer | panneau *Tasks* → *Run Task* |

`settings.json` fixe `python.defaultInterpreterPath` sur `venv\Scripts\python.exe`.

### 4.2 Installation et lancement manuel

```powershell
# 1. Cloner puis environnement virtuel backend
git clone https://github.com/yefiflorence-boop/rag-assistant-ai
cd rag-assistant-ai
python -m venv venv
venv\Scripts\activate

# 2. Dépendances backend (+ binaires OCR : Tesseract avec pack langue fra,
#    et poppler pour pdf2image — requis par src/extraction.py:7)
pip install -r requirements.txt

# 3. Dépendances frontend (Node 20+)
cd frontend
npm install
cd ..

# 4. Renseigner .env (voir tableau §3)

# 5. Indexer le corpus (une seule fois, à refaire si data/raw/ change)
python src/extraction.py
python src/chunking.py
python src/indexation.py

# 6. Lancer le backend
uvicorn api:app --host 127.0.0.1 --port 8000 --reload   # → /api/health

# 7. Lancer le frontend (autre terminal)
cd frontend
npm run dev   # → http://localhost:5173
```

Prérequis OCR souvent oublié : sans Tesseract + `fra` et sans poppler,
`extraction.py` échoue uniquement sur les pages scannées (< 30 caractères) et conserve le texte natif.

Build frontend : `npm run build` (`tsc --noEmit && vite build` → `frontend/dist/`), `npm run preview` (port 4173).

## 5. Pipeline de données

### 5.1 Extraction (`src/extraction.py`)

- `extract_pages()` : ouvre chaque PDF avec PyMuPDF, extrait le texte page par page.
- Si page < `MIN_CHARS = 30` → considérée comme scannée → OCR de cette page
  uniquement (`convert_from_path` + `pytesseract.image_to_string(lang="fra")`).
- `clean_text()` : supprime caractères invisibles, recolle les mots coupés
  (`-\n`), écrase espaces/lignes multiples.
- Sortie : `data/output/<nom>.pages.json` = `[{page, text}]` avec numéros de page réels.

### 5.2 Chunking (`src/chunking.py`)

- `RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100,
  separators=["\n\n", "\n", ". ", " ", ""])`.
- Chaque chunk garde `{"id": "<stem>-p<page>-<j>", "content", "source": "<nom>.pdf",
  "page": <n>}` — l'ID stable évite les doublons à l'indexation.
- Compatibilité ascendante `*.txt` → `page: "?"` (legacy).
- Les anciens `*_chunks.json` sont supprimés avant chaque run.

### 5.3 Indexation (`src/indexation.py`)

- Normalise les chunks → `Document(page_content, metadata={source, page})`.
- Ouvre ChromaDB (`hnsw:space: cosine`), **`delete_collection()` puis rebuild
  complet** : pas d'indexation incrémentale, toute relance repart de zéro.
- Insertion par lots `BATCH_SIZE = 64`.
- Écrit `data/manifest.json` : date, nb docs/chunks, liste des PDF avec
  `sha256` (16 hex) + taille, `chunks_par_document`, modèle d'embedding, `db_dir` relatif.
  État actuel : `2026-10-08`, 5 docs, **3201 chunks** (142 / 102 / 102 / 1890 / 965).
  C'est ce fichier que la sidebar React affiche (`Base à jour · N docs`).

## 6. Runtime applicatif (`api.py` + `chat_context.py` + `frontend/`)

Backend (`api.py`) :

1. `lifespan` + `_warm_rag()` (`api.py:32-43`) : pré-charge LLM + ChromaDB en thread daemon (évite le démarrage à froid).
2. `GET /api/health` (`api.py:151-155`) : rapide et non-bloquant, ne charge pas le RAG (`rag_loaded = _rag.cache_info().currsize > 0`).
3. `GET /api/manifest|documents|drh`, `GET /files/docs/{nom}` (`api.py:158-198`) : manifest, liste des PDF de `data/raw/`, contact DRH, PDF en `inline` (RFC 5987, `Accept-Ranges`, anti-traversal).
4. `POST /api/chat` (`api.py:201-206` → `_answer_sync:89-148`) : réponse complète JSON `{answer, sources, refusal, meta}`.
5. `POST /api/chat/stream` (`api.py:209-286`) : SSE events `token` (delta) puis `done` (payload final), headers `Cache-Control: no-cache`, `X-Accel-Buffering: no`.
6. Sources : dédoublonnées `(nom, page)`, capées à `MAX_SOURCES`, URL `/files/docs/{nom}#page=N`, `excerpt` 280 car. Si refus → `REFUSAL_MESSAGE` + `log_unanswered()` + `meta.drh`.

RAG (`chat_context.py`) :

1. `init_rag()` (`chat_context.py:40-62`) : `AzureOpenAIEmbeddings` + `Chroma(persist_directory=DB_DIR)` et `AzureChatOpenAI(temperature=0.2)`.
2. `search_with_scores(vectordb, question, k=TOP_K)` (`chat_context.py:68-86`) :
   `similarity_search_with_relevance_scores` puis **filtre `score <= threshold`**
   (distance cosinus : plus petit = plus pertinent). Fallback sans score si indisponible.
3. `build_context()` : concatène `[Document : <source> | page <n>]\n<texte>`.
4. `build_prompt()` : system RH strict (français, 50–150 mots, puces, refus exact
   si hors contexte, ne pas citer les sources — le frontend s'en charge).
5. Utilitaires : `is_refusal()` (30 premiers caractères du message de refus), `validate_response()` (audit), `get_manifest_info()` / `log_unanswered()`.

Frontend :

- `App.tsx` : conversations multiples, thème `sombre`/`clair` persisté, `streamChat()` puis repli `postChat()`, `notice` si refus, `isHome` (hero si 1 message) sinon fil.
- `lib/api.ts` : `API_BASE = VITE_API_URL ?? ''`, `fetchManifest|Documents|Drh|Health`, `postChat`, `streamChat` (parse SSE `\n\n`, events `token`/`done`/`error`).
- `ChatThread.tsx:61` : `streamingId` = dernier message si `loading` — seuls le `typing` et le `stream-caret` de la réponse en cours s'animent. Sources en lignes texte simples `Source : nom — p. N` (bouton → `DocViewer`), carte DRH si `refusal`, scroll non-intrusif (seulement si déjà en bas).
- `DocViewer.tsx` : `pdfjs-dist` (worker `pdf.worker.min.mjs`), `fetch(url sans #)` → blob → `window.open(blobUrl + #page=N)` (jamais de téléchargement), repli navigation directe ; rendu canvas DPR, navigation pages, zoom 0.6–2.5, bouton `Page citée`, extrait cité affiché, `Échap`/flèches.
- `Sidebar.tsx` : bouton nouvelle conversation, recherche historique, 8 conversations récentes (titres seuls, sans `●`/`○`), pied `Base à jour · N docs` + switch thème + aide.
- `HomeHero.tsx` : logo `OneadLogoStacked` 128, question unique, 4 cartes suggestions (sans sous-titre).
- `Composer.tsx` : textarea seule (`Enter` = envoyer), bouton envoi désactivé si vide/chargement.
- `index.css` : `.app` 1480px, `.layout` `290px + minmax(0,1fr)` gap 28px, `.main` 1080px centré, `.hero` 960px centré, `.card-grid` 4 → 2 → 1 colonnes, responsive tablette/mobile.

## 7. Tests et fiabilité

```powershell
python tests/eval_rag.py              # offline : retrieval lexical sur data/chunks, sans clé
python tests/eval_rag.py --with-llm   # + 5 questions réelles ChromaDB + Azure (si .env présent)
```

- `eval_rag.py:run_offline` simule le comportement attendu par catégorie et
  vérifie prompt (`CONTEXTE`/`QUESTION`), refus (`is_refusal`) et audit
  (`validate_response`), puis écrit `tests/rapport_fiabilite.md`.
- Jeu : `tests/20_questions.csv` (`id,categorie,question,reponse_attendue,
  document_attendu,comportement_attendu`).
- Dernier rapport archivé : **20 questions — 15 PASS / 5 PARTIEL / 0 FAIL**,
  régénéré sur la **base courante (2026-10-08, 3201 chunks)**. Les 5 PARTIEL sont des
  questions nominales dont le document attendu n'apparaît pas dans les passages
  récupérés (critère lexical de l'éval offline).
- `notebooks/extraction.ipynb` : exploration de l'extraction (non rejoué en CI).

## 8. Conventions et points d'attention

- Tous les chemins backend passent par `src/config.py` (relatifs à `BASE_DIR`).
- `temperature=0.2` : réponses stables/factuelles — ne pas monter sans ré-évaluer.
- `SIMILARITY_THRESHOLD=1.0` par défaut : permissif ; un refus abusif se règle
  ici ou via `TOP_K`, puis ré-évaluer avec `tests/eval_rag.py`.
- Les PDF sont servis **directement** depuis `data/raw/*.pdf` par `api.py:serve_doc`
  via `/files/docs` (le frontend utilise ces URL + blob) : aucun dossier `static/`.
- `requirements.txt` est un `pip freeze` **UTF-8 tout-en-un** (runtime + dev, 143 lignes) : `langchain-chroma==1.1.0`
  (compatible `chromadb`/otel), `fastapi==0.115.12`, `starlette==0.46.2` alignée, `uvicorn`, sans `streamlit`
  (`app.py` supprimé — `streamlit` exclu volontairement même s'il reste dans un vieux `venv`).
- PowerShell : les apostrophes françaises doivent être **doublées** dans les chaînes
  à apostrophes simples (`'Verification de l''environnement'`), sinon le script ne parse pas.
- Frontend : ne pas remettre les préfixes `●`/`○` dans la sidebar, ni le sous-titre du hero,
  ni l'animation de frappe sur le message de bienvenue (`streamingId` dans `ChatThread.tsx:61`).
