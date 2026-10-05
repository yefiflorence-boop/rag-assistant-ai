import hashlib
import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings

try:
    from langchain_chroma import Chroma            # version recommandée
except ImportError:
    from langchain_community.vectorstores import Chroma

from src.config import CHUNKS_DIR, DB_DIR, MANIFEST_PATH, RAW_DIR


# ENV

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
API_ENDPOINT_EMBEDDING = os.getenv("API_ENDPOINT_EMBEDDING")

BATCH_SIZE = 64   # nombre de chunks envoyés à Azure par appel


def _normalize_chunks(raw_chunks, fallback_stem):
    """Accepte l'ancien format (id int, source .txt, sans page) et le nouveau."""
    docs, ids = [], []
    for i, chunk in enumerate(raw_chunks):
        content = chunk.get("content", "")
        if not content or not content.strip():
            continue
        source = chunk.get("source", f"{fallback_stem}.pdf")
        if source.endswith(".txt"):
            source = source[:-4] + ".pdf"
        page = chunk.get("page", "?")
        cid = str(chunk.get("id", f"{fallback_stem}-{i}"))
        docs.append(Document(page_content=content, metadata={"source": source, "page": page}))
        ids.append(cid)
    return docs, ids


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(8192), b""):
            h.update(b)
    return h.hexdigest()[:16]


def main():
    print("Initialisation des embeddings...")

    embedding_function = AzureOpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
        azure_endpoint=API_ENDPOINT_EMBEDDING
    )

    files = sorted(CHUNKS_DIR.glob("*_chunks.json")) if CHUNKS_DIR.exists() else []
    print(f"{len(files)} fichiers détectés dans {CHUNKS_DIR}")

    documents, ids = [], []
    per_doc_counts = {}
    for file_path in files:
        chunks = json.loads(file_path.read_text(encoding="utf-8"))
        docs, chunk_ids = _normalize_chunks(chunks, file_path.stem.replace("_chunks", ""))
        documents.extend(docs)
        ids.extend(chunk_ids)
        if docs:
            per_doc_counts[docs[0].metadata["source"]] = len(docs)

    print(f"Total chunks : {len(documents)}")

    if not documents:
        raise SystemExit("Aucun chunk trouvé : lance d'abord extraction.py puis chunking.py")

    def open_db():
        return Chroma(
            persist_directory=str(DB_DIR),
            embedding_function=embedding_function,
            collection_metadata={"hnsw:space": "cosine"}
        )

    # Repart d'une base vide pour éviter les doublons ou anciens chunks
    vectordb = open_db()
    try:
        vectordb.delete_collection()
    except Exception:
        pass
    vectordb = open_db()

    print("\nIndexation dans ChromaDB...")

    for i in tqdm(range(0, len(documents), BATCH_SIZE)):
        vectordb.add_documents(
            documents[i:i + BATCH_SIZE],
            ids=ids[i:i + BATCH_SIZE]
        )

    print(f"\n✔ ChromaDB créée : {len(documents)} chunks dans {DB_DIR}")

    # Manifeste de traçabilité (reco jury #2 : actualiser la base documentaire)
    raw_pdfs = sorted(RAW_DIR.glob("*.pdf")) if RAW_DIR.exists() else []
    manifest = {
        "date_indexation": date.today().isoformat(),
        "nb_documents": len(raw_pdfs),
        "documents": [
            {"fichier": p.name, "sha256": _sha256(p), "taille_octets": p.stat().st_size}
            for p in raw_pdfs
        ],
        "nb_chunks": len(documents),
        "chunks_par_document": per_doc_counts,
        "embedding_model": EMBEDDING_MODEL,
        "db_dir": str(DB_DIR),
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✔ Manifeste écrit : {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
