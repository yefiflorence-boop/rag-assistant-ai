# rag-assistant-ai
Assistant IA documentaire basé sur le RAG
#  ONEAD Assistant RAG

> Assistant IA documentaire interne basé sur l'approche **RAG (Retrieval-Augmented Generation)**  
> Répond aux questions RH à partir des documents internes de l'ONEAD — avec sources citées.

---

##  Présentation

**ONEAD Assistant RAG** est un MVP d'assistant documentaire intelligent développé pour l'Office National de l'Eau et de l'Assainissement de Djibouti.

L'utilisateur pose une question en langage naturel. Le système :
1. Recherche les passages pertinents dans les documents internes indexés
2. Génère une réponse concise basée **uniquement** sur ces passages
3. Cite les sources PDF utilisées
4. Refuse poliment de répondre si l'information n'est pas dans le corpus



##  Fonctionnalités

 Fonctionnalité : Détail 

 Interface de chat : Interface web Streamlit avec historique de conversation 
 Recherche sémantique : Similarité cosinus sur vecteurs ChromaDB 
 Génération IA : Réponse en streaming via Azure OpenAI 
 Sources citées : Nom du fichier PDF affiché après chaque réponse 
 Refus contrôlé : Message explicite si l'information est hors corpus 
 Formats des données : Ingestion PDF



##  Architecture RAG


Question utilisateur
        │
        ▼
┌───────────────────┐
│  Embeddings Azure │  → Transforme la question en vecteur
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│    ChromaDB       │  → Recherche les 5 passages les plus proches
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Prompt augmenté  │  → Question + contexte + règles
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Azure OpenAI LLM │  → Génère la réponse en streaming
└────────┬──────────┘
         │
         ▼
  Réponse +  Source : fichier.pdf
```


##  Structure du projet


rag-assistant-ai/
│
├── app.py                  # Interface Streamlit (point d'entrée)
├── chat_context.py         # Fonction du contexte du chat 
│
├── src/
│   ├── extraction.py        # Extraction texte (PDF en TXT) et Nettoyage du texte extrait         
│   ├── chunking.py          # Découpage en segments (chunks)
│   └── indexation.py        # Pipeline RAG (embeddings, indexation ChromaDB) 
│
├── data/
│   ├── raw/                # Documents bruts à indexer (PDF)
    ├── output/             # Stockage de l'extration des Documents bruts (TXT)
│   ├── chunks/             # Segments JSON produits par chunking.py
│   └── chroma_db/          # Base vectorielle persistante (auto-générée)
│
├── tests/
│   ├── 20_questions.csv    # Jeu de 20 questions de test
├── Static
    ├──logo.png
│
├── .env                    # Clés API (jamais commité sur Git)
├── .gitignore              # Fichiers exclus de Git
├── requirements.txt        # Dépendances Python
└── README.md               # Ce fichier


## Installation

### Prérequis

- Python **3.10** ou supérieur
- Un compte **Azure OpenAI** 
- Un modèle de chat (gpt-4.1-mini)
- Un modèle d'embedding (text-embedding-3-large)
- creer un fichier .env s'il n'existe pas puis y mettre les variables suivantes:
CHAT_MODEL
API_ENDPOINT_GPT
EMBEDDING_MODEL
API_ENDPOINT_EMBEDDING
OPENAI_API_KEY

1. Cloner le dépôt

Terminal
git clone https://github.com/yefiflorence-boop/rag-assistant-ai
cd rag-assistant-ai


2. Créer et activer l'environnement virtuel

Terminal
# Créer l'environnement virtuel
python -m venv .venv

# Activer sur Windows
.venv\Scripts\activate



3. Installer les dépendances
Terminal
pip install -r requirements.txt



##  Lancement

 Étape 1 — Indexer les documents (une seule fois)

Placer les documents PDF dans le dossier `data/raw/`, puis lancer :
  python src/extraction.py && python src/chunking.py && python src/indexation.py


La base vectorielle est créée dans `data/chroma_db/`. Cette étape ne doit être refaite que si nous ajoutons de nouveaux documents.

Étape 2 — Lancer l'interface

Terminal
streamlit run app.py

Ouvrir le navigateur à l'adresse affichée : **http://localhost:8501**



##  Tests 

Le script test: les 20 questions de `tests/20_questions.txt` et affiche :



## Stack technique

 Besoin : Outil 

Langage : Python 3.10+ 
Interface : Streamlit 
Extraction PDF : PyMuPDF (fitz) 
Extraction DOCX :python-docx 
Découpage : LangChain RecursiveCharacterTextSplitter 
Embeddings : Azure OpenAI Embeddings 
Base vectorielle ; ChromaDB (persistant sur disque) 
LLM :Azure OpenAI ( GPT-4.1 mini) 
Orchestration : LangChain 
Variables secrets : python-dotenv 
Versioning : Git / GitHub 


##  Dépendances principales

streamlit
langchain
langchain-openai
langchain-community
chromadb
pymupdf
python-docx
python-dotenv

> Liste complète dans `requirements.txt`

Équipe

Projet réalisé dans le cadre de la formation **AI Engineering** — Groupe 1


Projet à usage interne : Projet pédagogique ONEAD / Formation AI Engineering 

