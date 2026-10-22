# Déploiement — ONEAD Assistant RAG

## 1. Architecture déployée

```text
Utilisateur ──HTTPS──▶ Frontend React (Vite : build dist/ ou dev :5173)
                            │  proxy /api + /files → backend (ou VITE_API_URL absolue)
                            ▼
                       Backend FastAPI :8000 (api.py : lifespan warmup, chat, SSE, fichiers)
                            │  .env (clés Azure, jamais commité)
                            ├─▶ ChromaDB locale (data/chroma_db/, rebuild via indexation.py)
                            ├─▶ Azure OpenAI Embeddings (question → vecteur)
                            └─▶ Azure OpenAI Chat gpt-4.1-mini (réponse streamée SSE token/done)
                                     ▲
                     data/manifest.json (fraîcheur base) + data/raw/*.pdf via /files/docs (#page=N)
```

Pas de Streamlit, pas de backend séparé supplémentaire, pas de base externe :
un processus FastAPI + fichiers locaux + APIs Azure + SPA React (dev Vite ou `dist/` statique).

Ancienne architecture Streamlit (`app.py`, `.streamlit/config.toml`, `static/docs/*.pdf` +
`enableStaticServing`) : **supprimée, ne plus déployer**.

## 2. Ce qui est versionné / ce qui ne l'est pas

| Versionné (git) | Reconstruit / fourni au déploiement |
|---|---|
| `api.py`, `chat_context.py`, `src/`, `tests/`, `notebooks/` | — |
| `data/raw/*.pdf` (5 docs), `data/manifest.json` | — |
| `frontend/` (dont `src/lib/api.ts`, `vite.config.ts`, `public/logo.svg`) | `frontend/node_modules/`, `frontend/dist/` (build `npm run build`) |
| `requirements.txt`, `frontend/package.json` + `package-lock.json`, `README.md`, `docs/` | — |
| `start.ps1`, `stop.ps1`, `demarrer.bat`, `demo.bat`, `arreter.bat` | — (scripts de lancement, versionnés) |
| `.vscode/` (`tasks.json`, `launch.json`, `settings.json`) | — (aide au développement) |

Ignorés et donc **absents d'un clone frais** :
`.env`, `.streamlit/secrets.toml`, `data/output/*`, `data/chunks/*`, `data/chroma_db/*`,
`data/feedback/unanswered.jsonl`, `frontend/node_modules/`, `frontend/dist/`,
`frontend/.vite/`, `logs/`, `.run/`.

Conséquence : **chaque environnement doit reconstruire la base**
(`extraction → chunking → indexation`) ou recevoir une copie de
`data/chroma_db/` + `data/manifest.json` issue d'une indexation de référence (ici 2026-10-08, 3201 chunks).

## 3. Prérequis cible

- Python **3.10+**, ~2 Go disque (corpus + ChromaDB 3201 chunks + OCR).
- Node.js **20+** pour builder/servir le frontend.
- Binaires OCR : **Tesseract** (pack langue `fra`) + **poppler**
  (`convert_from_path` dans `src/extraction.py:42-44`). Sans eux, seules les
  pages scannées (< 30 car.) perdent en qualité.
- Accès réseau sortant vers les 2 endpoints Azure OpenAI + clé `OPENAI_API_KEY`.
- Variables d'environnement (toutes dans `.env` en local, ou secrets du
  hébergeur en prod ; `VITE_API_URL` côté frontend) — voir tableau :

| Variable | Requis | Remarque prod |
|---|---|---|
| `OPENAI_API_KEY`, `CHAT_MODEL`, `API_ENDPOINT_GPT` | oui | Nom de **déploiement** Azure, pas le nom public du modèle |
| `EMBEDDING_MODEL`, `API_ENDPOINT_EMBEDDING` | oui | Doit matcher le modèle du `manifest.json` (`text-embedding-3-large`) |
| `DB_DIR` | non | Défaut `data/chroma_db` ; pointer vers un volume persistant en conteneur |
| `TOP_K` (5), `MAX_SOURCES` (3), `SIMILARITY_THRESHOLD` (1.0) | non | Ne changer qu'après ré-éval (`tests/eval_rag.py`) |
| `DRH_EMAIL`, `DRH_TEL` | non | Personnaliser par site sans toucher au code |
| `VITE_API_URL` | non | URL absolue du backend (ex. `https://api…`) quand le frontend `dist/` n'est pas servi par le même domaine ; vide = chemins relatifs `/api`, `/files` |

## 4. Procédure de déploiement (VM / serveur interne)

```powershell
git clone https://github.com/yefiflorence-boop/rag-assistant-ai
cd rag-assistant-ai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# .env de production (permissions restrictives, jamais dans git)
# OPENAI_API_KEY, CHAT_MODEL, API_ENDPOINT_GPT, EMBEDDING_MODEL, API_ENDPOINT_EMBEDDING, ...

# 1. Reconstruire la base (obligatoire sur un clone frais)
python src/extraction.py
python src/chunking.py
python src/indexation.py

# 2. Frontend : installer puis builder (ou dev en recette)
cd frontend
npm install
npm run build   # → frontend/dist/ (index.html + assets + logo.svg + pdf.worker)
cd ..

# 3. Lancer le backend (prod : derrière un reverse-proxy + HTTPS, port interne)
uvicorn api:app --host 127.0.0.1 --port 8000

# 4. Servir le frontend dist/ (au choix) :
#    a) via le même reverse-proxy (recommandé : même origine → pas de CORS/VITE_API_URL),
#    b) npx vite preview --port 4173 (recette uniquement),
#    c) npm run dev (recette : http://localhost:5173, proxy /api+/files actif).
```

Variante « une seule origine » (sans reverse-proxy, pour la démo) : construire le
front puis laisser FastAPI le servir lui-même sur le port 8000 —

```powershell
cd frontend && npm run build && cd ..
$env:SERVE_FRONTEND = "1"          # active le montage StaticFiles de frontend/dist
uvicorn api:app --host 127.0.0.1 --port 8000
# → http://127.0.0.1:8000 sert l'UI ET l'API (même origine, plus de CORS)
```

Équivalently `.\demo.bat` (ou `.\start.ps1 -Single`) qui enchaîne build + lancement.

Plus aucune étape `Copy-Item data/raw/*.pdf static/docs/` ni `.streamlit/config.toml` :
les PDF sont servis par FastAPI (`GET /files/docs/{nom}`, `inline`, `#page=N` préservé,
ouverture frontend en blob sans téléchargement). Le dossier `static/` n'existe plus.

Vérifications : `GET /api/health` → `status ok` ; sidebar « Base à jour · 5 docs »
(= `data/manifest.json` 2026-10-08, 3201 chunks) ; `GET /api/documents` liste 5 PDF ;
une question nominale affiche `Source : … — p. N` + visionneuse à la bonne page ;
une question hors corpus affiche refus + carte DRH et ajoute une ligne à `data/feedback/unanswered.jsonl`.

## 5. Variante hébergement frontend + API séparés (remplace l'ancienne variante Streamlit Cloud)

1. Pousser le repo (sans `.env`, sans `chroma_db/`, sans `node_modules/`/`dist/`).
2. Backend (VM, conteneur, PaaS Python) : installer `requirements.txt`, injecter le `.env` en secrets,
   reconstruire la base (`extraction → chunking → indexation`) ou monter `DB_DIR` persistant,
   lancer `uvicorn api:app --host 0.0.0.0 --port 8000` (CORS déjà limité à `localhost:5173/3000` dans `api.py:48-58` — élargir aux domaines prod).
3. Frontend (hébergeur statique) : `npm install && npm run build`, publier `frontend/dist/`,
   renseigner `VITE_API_URL=https://<backend>` au build si origines différentes.
4. Base vectorielle : pré-indexer localement puis restaurer `data/chroma_db/` + `manifest.json`,
   ou reconstruire sur la cible (nécessite Tesseract/poppler seulement si PDF scannés).
5. PDF volumineux (~13 Mo au total) : servis par le backend, pas besoin de Git LFS côté frontend.

## 6. Variante conteneurisée (Docker)

> **Statut : non retenue pour ce projet.** Le build d'image s'est révélé trop long sur
> le poste de travail (réseau à ~80 ko/s : 13 min pour `apt-get`, > 30 min pour
> `pip install`) et donc incompatible avec une démonstration. Le déploiement de
> référence reste le **mode local** : `.\demo.bat` (une seule origine, un seul
> processus) ou `.\demarrer.bat` (dev avec HMR), derrière un reverse-proxy HTTPS
> si l'on expose le service.
>
> Les fichiers `Dockerfile` / `docker-compose.yml` ont été retirés du dépôt ;
> voici l'architecture qui avait été validée, à réintroduire si le besoin change.

```text
étape 1 (node:20-slim) : npm ci → npm run build → frontend/dist
étape 2 (python:3.12-slim) :
    apt-get install tesseract-ocr tesseract-ocr-fra poppler-utils curl
    pip install -r requirements-runtime.txt
    copie api.py, chat_context.py, src/, data/raw/, manifest.json + frontend/dist
    ENV SERVE_FRONTEND=1 → FastAPI sert l'API ET l'interface sur :8000
```

| Élément | Décision | Raison |
|---|---|---|
| Base vectorielle | volume `./data/chroma_db` | 219 Mo : jamais dupliquée dans l'image |
| Secrets | `env_file: .env` | jamais dans l'image ni dans le dépôt |
| `requirements-runtime.txt` | distinct de `requirements.txt` | le freeze complet contient pandas/pyarrow/altair/langgraph/pdfplumber/kubernetes (~120 Mo inutiles) |
| Healthcheck | `curl /api/health` | `restart: unless-stopped` ne redémarre pas un conteneur à moitié prêt |

### Variante sans conteneur (référence)

```powershell
cd frontend ; npm run build ; cd ..
$env:SERVE_FRONTEND = "1"
uvicorn api:app --host 127.0.0.1 --port 8000
```

ou `.\demo.bat` qui enchaîne build + lancement.

## 7. Mise à jour du corpus (runbook)

1. Ajouter/remplacer des PDF dans `data/raw/`.
2. Relancer `python src/extraction.py && python src/chunking.py && python src/indexation.py`
   (**rebuild complet** : `delete_collection()`, pas d'incrémental).
3. Contrôler `data/manifest.json` (date du jour, `nb_documents`, `nb_chunks`, `chunks_par_document`, SHA-256) et la
   sidebar (`Base à jour · N docs`) + `GET /api/manifest` + `GET /api/documents`.
4. Relancer `python tests/eval_rag.py [--with-llm]` et archiver `tests/rapport_fiabilite.md`
   (l'actuel : 15 PASS / 5 PARTIEL / 0 FAIL, base 2026-10-08 / 3201 chunks).
5. Redémarrer Uvicorn (le RAG est chargé en mémoire via `_rag()` + `lifespan` warmup ; pas de `@st.cache_resource`).
6. Aucune copie vers `static/docs/` requise : `GET /files/docs/{nom}` lit directement `data/raw/`.

## 8. Sécurité et exploitation

- **Secrets** : `.env` / secrets hébergeur jamais commités ; rotation de
  `OPENAI_API_KEY` côté Azure sans changer le code. Restreindre le CORS prod aux domaines réels (`api.py:48-58`).
- **Données** : `unanswered.jsonl` contient des questions d'agents (potentiellement
  nominatives) — restreindre l'accès au dossier `data/feedback/`, le sauvegarder,
  l'exploiter côté DRH pour enrichir le corpus.
- **Réseau** : exposer uniquement via HTTPS + authentification (reverse-proxy,
  VPN intranet ou SSO) — ni FastAPI ni Vite n'ont de login natif.
- **Supervision minimale** : vérifier au démarrage les logs Azure (429/401),
  la présence de `manifest.json`, `/api/health` (`rag_loaded` passe à vrai après warmup),
  et la croissance de `unanswered.jsonl` (pic de refus = corpus à compléter ou seuil à ajuster).

## 9. Dépannage rapide

| Symptôme | Cause probable | Action |
|---|---|---|
| Sidebar « 0 document(s) » / manifest vide | `manifest.json` absent ou `indexation.py` non relancé | Relancer `extraction → chunking → indexation`, vérifier `GET /api/manifest` |
| `rag_loaded: false` durable | Clés Azure absentes/invalides (warmup silencieux) | Vérifier `.env`, logs uvicorn, `API_ENDPOINT_*` et `CHAT_MODEL` (= deployment name) |
| Liens sources en 404 | Mauvais `VITE_API_URL` ou proxy Vite inactif en prod | En dev : `npm run dev` (proxy actif) ; en prod : même origine ou `VITE_API_URL` absolue ; tester `GET /files/docs/<nom>` |
| `Aucun chunk trouvé` à l'indexation | `chunking.py` non lancé ou `data/output/` vide | Relancer extraction puis chunking |
| OCR en erreur | Tesseract/poppler absents | Installer + pack `fra` (pages scannées seulement) |
| Refus systématiques | `SIMILARITY_THRESHOLD` trop strict / base vide | Contrôler manifest, tester `TOP_K`/`threshold`, ré-évaluer (`tests/eval_rag.py`) |
| 401/404 Azure | Mauvais endpoint ou nom de déploiement | Vérifier `API_ENDPOINT_*` et `CHAT_MODEL` (= deployment name) |
| SSE coupé / pas de streaming | Proxy/Nginx bufferise les events | Conserver headers `Cache-Control: no-cache`, `X-Accel-Buffering: no` (`api.py:278-285`) ; le frontend bascule sur `POST /api/chat` |
| PDF téléchargé au lieu d'être lu | Ancien lien direct sans blob | Comportement actuel : blob + `window.open(blob#page=N)` (`ChatThread.tsx:openDoc`), aucun `Content-Disposition: attachment` côté API (`inline`) |
