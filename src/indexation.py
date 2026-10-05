import json
import os
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings

try:
    from langchain_chroma import Chroma            # version recommandée
except ImportError:
    from langchain_community.vectorstores import Chroma


# ENV

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
API_ENDPOINT_EMBEDDING = os.getenv("API_ENDPOINT_EMBEDDING")


# CONFIGURATION

# Dossier produit par chunking.py
CHUNKS_DIR = Path(r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\chunks")

# Dossier ChromaDB (doit être le même que DB_DIR dans chat_context.py)
DB_DIR = Path(r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\chroma_db")

BATCH_SIZE = 64   # nombre de chunks envoyés à Azure par appel


# EMBEDDINGS

print("Initialisation des embeddings...")

embedding_function = AzureOpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    api_key=OPENAI_API_KEY,
    azure_endpoint=API_ENDPOINT_EMBEDDING
)


# CHARGEMENT DES CHUNKS

documents = []
ids = []

files = sorted(CHUNKS_DIR.glob("*_chunks.json"))

print(f"{len(files)} fichiers détectés")

for file_path in files:

    chunks = json.loads(file_path.read_text(encoding="utf-8"))

    for chunk in chunks:

        documents.append(
            Document(
                page_content=chunk["content"],
                metadata={
                    "source": chunk["source"],   # nom du PDF
                    "page": chunk["page"],       # numéro de page
                }
            )
        )

        ids.append(chunk["id"])

print(f"Total chunks : {len(documents)}")

if not documents:
    raise SystemExit("Aucun chunk trouvé : lance d'abord extraction.py puis chunking.py")


# CRÉATION DE LA BASE


def open_db():
    return Chroma(
        persist_directory=str(DB_DIR),
        embedding_function=embedding_function,
        collection_metadata={"hnsw:space": "cosine"}   # scores de similarité exploitables
    )


# Repart d'une base vide pour éviter les doublons ou anciens chunks
vectordb = open_db()
vectordb.delete_collection()
vectordb = open_db()

print("\nIndexation dans ChromaDB...")

for i in tqdm(range(0, len(documents), BATCH_SIZE)):

    vectordb.add_documents(
        documents[i:i + BATCH_SIZE],
        ids=ids[i:i + BATCH_SIZE]
    )

print(f"\n✔ ChromaDB créée : {len(documents)} chunks dans {DB_DIR}")