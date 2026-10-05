# Développement — ONEAD Assistant RAG

## 1. Stack technique

| Besoin | Outil (voir `requirements.txt`, encodage UTF-16) |
|---|---|
| Langage | Python 3.10+ (testé ici en 3.14.3) |
| Interface | Streamlit (`app.py`) |
| Extraction PDF | PyMuPDF (`fitz`), fallback OCR `pytesseract` (lang `fra`) + `pdf2image` |
| Découpage | `langchain-text-splitters` / `RecursiveCharacterTextSplitter` |
| Embeddings | Azure OpenAI `text-embedding-3-large` (`langchain-openai`) |
| Base vectorielle | ChromaDB persistée sur disque (`langchain-chroma`, espace `cosine`) |
| LLM | Azure OpenAI `gpt-4.1-mini`, `temperature=0.2`, `api_version="2024-10-21"` |
| Config / secrets | `python-dotenv` (`.env`, jamais commité) |

## 2. Structure du projet

```text
rag-assistant-ai/
├── app.py              # Interface Streamlit (point d'entrée)
├── chat_context.py     # init RAG, recherche, prompt, refus, manifest, logging
├── src/
│   ├── config.py       # Chemins + seuils + contacts DRH (source unique)
│   ├── extraction.py   # PDF → data/output/*.pages.json (page par page + OCR)
│   ├── chunking.py     # pages → data/chunks/*_chunks.json (800 car., overlap 100)
│   ├── indexation.py   # chunks → data/chroma_db/ + data/manifest.json
│   └── test.py         # Snippet manuel de test similarité (chemin absolu en dur)
├── data/
│   ├── raw/            # PDF à indexer (versionnés : 5 fichiers)
│   ├── output/         # *.pages.json (ignoré par git)
│   ├── chunks/         # *_chunks.json (ignoré par git)
│   ├── chroma_db/      # Base vectorielle (ignorée par git, à reconstruire)
│   ├── manifest.json   # Traçabilité : date, docs + SHA-256, nb chunks, modèle
│   └── feedback/       # unanswered.jsonl (questions sans réponse, ignoré par git)
├── static/docs/        # PDF servis en lien (actuellement seul `.gitkeep` — à remplir)
├── tests/
│   ├── 20_questions.csv
│   ├── eval_rag.py     # Éval offline (lexicale) + option --with-llm
│   └── rapport_fiabilite.md
├── notebooks/extraction.ipynb
└── .env                # Clés (non versionné) — voir §3
```

Fichiers ignorés par git (`.gitignore:218-223`) : `.env`, `data/output/*`,
`data/chunks/*`, `data/chroma_db/*`, `data/feedback/unanswered.jsonl`.

## 3. Configuration (`.env`)

Variables lues dans `chat_context.py:26-34`, `src/indexation.py:23-27`,
`src/config.py:26-33` :

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

`src/config.py` centralise les chemins (`BASE_DIR`-relatifs) et constantes :
`REFUSAL_MESSAGE`, `DRH_CONTACT`, `TOP_K`, `MAX_SOURCES`, `SIMILARITY_THRESHOLD`.

## 4. Installation et lancement local

```powershell
# 1. Cloner puis environnement virtuel
git clone https://github.com/yefiflorence-boop/rag-assistant-ai
cd rag-assistant-ai
python -m venv .venv
.venv\Scripts\activate

# 2. Dépendances (+ binaires OCR : Tesseract avec pack langue fra,
#    et poppler pour pdf2image — requis par src/extraction.py:6-7)
pip install -r requirements.txt

# 3. Renseigner .env (voir tableau §3)

# 4. Indexer le corpus (une seule fois, à refaire si data/raw/ change)
python src/extraction.py
python src/chunking.py
python src/indexation.py

# 5. Lancer l'interface
streamlit run app.py   # → http://localhost:8501
```

Prérequis OCR souvent oublié : sans Tesseract + `fra` et sans poppler,
`extraction.py` échoue uniquement sur les pages scannées (< 30 caractères).

## 5. Pipeline de données

### 5.1 Extraction (`src/extraction.py`)

- `extract_pages()` : ouvre chaque PDF avec PyMuPDF, extrait le texte page par page.
- Si page < `MIN_CHARS = 30` → considérée comme scannée → OCR de cette page
  uniquement (`convert_from_path` + `pytesseract.image_to_string(lang="fra")`).
- `clean_text()` : supprime caractères invisibles, recolle les mots coupés
  (`-\n`), écrase espaces/lignes multiples.
- Sortie : `data/output/<nom>.pages.json` = `[{page, text}]`.

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
  `sha256` (16 hex) + taille, `chunks_par_document`, modèle d'embedding.
  C'est ce fichier que la sidebar Streamlit affiche.

## 6. Runtime applicatif (`app.py` + `chat_context.py`)

1. `init_rag()` (`chat_context.py:40-62`, `@st.cache_resource` dans `app.py:34-39`) :
   construit `AzureOpenAIEmbeddings` + `Chroma(persist_directory=DB_DIR)` et
   `AzureChatOpenAI(temperature=0.2)`.
2. `search_with_scores(vectordb, question, k=TOP_K)` (`chat_context.py:68-86`) :
   `similarity_search_with_relevance_scores` puis **filtre `score <= threshold`**
   (distance cosinus : plus petit = plus pertinent). Fallback sans score si la
   méthode scorée est indisponible.
3. `build_context()` : concatène `[Document : <source> | page <n>]\n<texte>`.
4. `build_prompt()` : system RH strict (français, 50–150 mots, puces, refus exact
   si hors contexte, ne pas citer les sources — l'app s'en charge).
5. Streaming : `llm.stream(prompt)` affiché chunk par chunk
   (`app.py:176-178`), puis soit liens sources (`source_links`, dédoublonnés,
   capés à `MAX_SOURCES`, URL `app/static/docs/<nom>.pdf#page=N`), soit refus +
   carte DRH + `log_unanswered()`.
6. Utilitaires : `is_refusal()` (détecte les 30 premiers caractères du message
   de refus), `validate_response()` (audit : passages + sources traçables),
   `get_manifest_info()` / `log_unanswered()`.

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
- Dernier rapport : **20 questions — 16 PASS / 4 PARTIEL / 0 FAIL**.
- `notebooks/extraction.ipynb` : exploration de l'extraction (non rejoué en CI).
- `src/test.py` : snippet ad hoc avec **chemin absolu en dur** (`DB_DIR =
  C:\Users\yefif\…`) — ne pas utiliser tel quel, préférer `src.config.DB_DIR`.

## 8. Conventions et points d'attention

- Tous les chemins passent par `src/config.py` (relatifs à `BASE_DIR`) sauf
  `src/test.py` (à corriger si réutilisé).
- `temperature=0.2` : réponses stables/factuelles — ne pas monter sans ré-évaluer.
- `SIMILARITY_THRESHOLD=1.0` par défaut : permissif ; un refus abusif se règle
  ici ou via `TOP_K`, puis ré-évaluer avec `tests/eval_rag.py`.
- `static/docs/` est vide (`.gitkeep`) : les liens sources renvoient 404 tant
  que les PDF n'y sont pas copiés **et** que `enableStaticServing` n'est pas
  activé (voir doc Déploiement).
