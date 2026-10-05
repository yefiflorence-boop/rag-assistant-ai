# Déploiement — ONEAD Assistant RAG

## 1. Architecture déployée

```text
Utilisateur ──HTTPS──▶ Streamlit (app.py: load_rag, chat, sidebar manifest)
                           │  .env (clés Azure, jamais commité)
                           ├─▶ ChromaDB locale (data/chroma_db/, rebuild via indexation.py)
                           ├─▶ Azure OpenAI Embeddings (question → vecteur)
                           └─▶ Azure OpenAI Chat gpt-4.1-mini (réponse streamée)
                                    ▲
                    data/manifest.json (fraîcheur base) + static/docs/*.pdf (#page=N)
```

Pas de backend séparé, pas de base externe : un seul processus Streamlit +
fichiers locaux + APIs Azure.

## 2. Ce qui est versionné / ce qui ne l'est pas

| Versionné (git) | Reconstruit / fourni au déploiement |
|---|---|
| `app.py`, `chat_context.py`, `src/`, `tests/`, `notebooks/` | — |
| `data/raw/*.pdf` (5 docs), `data/manifest.json` | — |
| `requirements.txt`, `README.md`, `docs/` | — |
| `static/logo.png`, `static/docs/.gitkeep` | `static/docs/*.pdf` à copier (voir §4) |

Ignorés (`.gitignore:151-223`) et donc **absents d'un clone frais** :
`.env`, `data/output/*`, `data/chunks/*`, `data/chroma_db/*`,
`data/feedback/unanswered.jsonl`, `.streamlit/secrets.toml`.

Conséquence : **chaque environnement doit reconstruire la base**
(`extraction → chunking → indexation`) ou recevoir une copie de
`data/chroma_db/` + `data/manifest.json` issue d'une indexation de référence.

## 3. Prérequis cible

- Python **3.10+**, ~2 Go disque (corpus + ChromaDB 5282 chunks + OCR).
- Binaires OCR : **Tesseract** (pack langue `fra`) + **poppler**
  (`convert_from_path` dans `src/extraction.py:41-44`). Sans eux, seules les
  pages scannées échouent.
- Accès réseau sortant vers les 2 endpoints Azure OpenAI + clé `OPENAI_API_KEY`.
- Variables d'environnement (toutes dans `.env` en local, ou secrets du
  hébergeur en prod) — voir tableau :

| Variable | Requis | Remarque prod |
|---|---|---|
| `OPENAI_API_KEY`, `CHAT_MODEL`, `API_ENDPOINT_GPT` | oui | Nom de **déploiement** Azure, pas le nom public du modèle |
| `EMBEDDING_MODEL`, `API_ENDPOINT_EMBEDDING` | oui | Doit matcher le modèle du `manifest.json` (`text-embedding-3-large`) |
| `DB_DIR` | non | Défaut `data/chroma_db` ; pointer vers un volume persistant en conteneur |
| `TOP_K` (5), `MAX_SOURCES` (3), `SIMILARITY_THRESHOLD` (1.0) | non | Ne changer qu'après ré-éval (`tests/eval_rag.py`) |
| `DRH_EMAIL`, `DRH_TEL` | non | Personnaliser par site sans toucher au code |

## 4. Procédure de déploiement (VM / serveur interne)

```powershell
git clone https://github.com/yefiflorence-boop/rag-assistant-ai
cd rag-assistant-ai
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# .env de production (permissions restrictives, jamais dans git)
# OPENAI_API_KEY, CHAT_MODEL, API_ENDPOINT_GPT, EMBEDDING_MODEL, API_ENDPOINT_EMBEDDING, ...

# 1. Reconstruire la base (obligatoire sur un clone frais)
python src/extraction.py
python src/chunking.py
python src/indexation.py

# 2. Rendre les PDF cliquables : copier le corpus vers static/docs/
Copy-Item data/raw/*.pdf static/docs/
# + activer le serving statique :
# .streamlit/config.toml  →  [server]  enableStaticServing = true
# (fichier absent du repo : à créer ; sans lui, app.py:20
#  DOCS_URL = "app/static/docs" renvoie 404)

# 3. Lancer (prod : derrière un reverse-proxy + HTTPS, port interne)
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

Vérifications : sidebar « Base documentaire » renseigne date/nb docs
(= `data/manifest.json`) ; une question nominale affiche `Sources :` avec lien
`#page=N` qui ouvre le PDF ; une question hors corpus affiche refus + carte DRH
et ajoute une ligne à `data/feedback/unanswered.jsonl`.

## 5. Variante Streamlit Community Cloud

1. Pousser le repo (sans `.env`, sans `chroma_db/`).
2. Sur le dashboard : **Secrets** = contenu du `.env`.
3. `requirements.txt` est installé automatiquement.
4. Base vectorielle : soit la reconstruire au premier démarrage (nécessite les
   binaires OCR — souvent indisponibles sur l'offre gratuite → préférer
   pré-indexer localement puis versionner un export, ou exposer `DB_DIR` via un
   stockage externe), soit limiter le corpus aux PDF 100 % textuels.
5. `static/docs/*.pdf` : à pousser via Git LFS si volumineux (ici ~13 Mo au total).

## 6. Variante Docker (recommandée pour prod reproductible)

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-fra poppler-utils && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p .streamlit && printf '[server]\nenableStaticServing = true\n' > .streamlit/config.toml
# La base est reconstruite au build OU montée en volume (voir ci-dessous)
CMD ["sh", "-c", "python src/extraction.py && python src/chunking.py && python src/indexation.py && cp data/raw/*.pdf static/docs/ && streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]
```

- Monter `DB_DIR` et `data/feedback/` sur volumes persistants si l'on veut
  éviter la ré-indexation à chaque redémarrage.
- Injecter les 5 variables Azure via secrets du orchestrateur, pas en `ENV` clair.

## 7. Mise à jour du corpus (runbook)

1. Ajouter/remplacer des PDF dans `data/raw/`.
2. Relancer `python src/extraction.py && python src/chunking.py && python src/indexation.py`
   (**rebuild complet** : `delete_collection()`, pas d'incrémental).
3. Recopier les nouveaux PDF dans `static/docs/`.
4. Contrôler `data/manifest.json` (date du jour, `nb_documents`, SHA-256) et la
   sidebar de l'app.
5. Relancer `python tests/eval_rag.py` et archiver `tests/rapport_fiabilite.md`.
6. Redémarrer Streamlit (le `@st.cache_resource` de `app.py:34` charge la base
   une fois par processus).

## 8. Sécurité et exploitation

- **Secrets** : `.env` / `.streamlit/secrets.toml` jamais commités ; rotation de
  `OPENAI_API_KEY` côté Azure sans changer le code.
- **Données** : `unanswered.jsonl` contient des questions d'agents (potentiellement
  nominatives) — restreindre l'accès au dossier `data/feedback/`, le sauvegarder,
  l'exploiter côté DRH pour enrichir le corpus.
- **Réseau** : exposer uniquement via HTTPS + authentification (reverse-proxy,
  VPN intranet ou SSO Streamlit) — l'app n'a pas de login natif.
- **Supervision minimale** : vérifier au démarrage les logs Azure (429/401),
  la présence de `manifest.json`, et la croissance de `unanswered.jsonl`
  (pic de refus = corpus à compléter ou seuil à ajuster).

## 9. Dépannage rapide

| Symptôme | Cause probable | Action |
|---|---|---|
| Sidebar « Base non versionnée » | `manifest.json` absent | Relancer `src/indexation.py` |
| Liens sources en 404 | `static/docs/` vide ou `enableStaticServing` manquant | Copier les PDF + créer `.streamlit/config.toml` |
| `Aucun chunk trouvé` à l'indexation | `chunking.py` non lancé ou `data/output/` vide | Relancer extraction puis chunking |
| OCR en erreur | Tesseract/poppler absents | Installer + pack `fra` |
| Refus systématiques | `SIMILARITY_THRESHOLD` trop strict / base vide | Contrôler manifest, tester `TOP_K`/`threshold`, ré-évaluer |
| 401/404 Azure | Mauvais endpoint ou nom de déploiement | Vérifier `API_ENDPOINT_*` et `CHAT_MODEL` (= deployment name) |
