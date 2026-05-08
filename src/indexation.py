import os
import json
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# ENV

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print("")

# CONFIGURATION

CHUNKS_DIR = r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\chunks"

#  TON DOSSIER CHROMADB
DB_DIR = r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\chroma_db"

EMBEDDING_MODEL =os.getenv("EMBEDDING_MODEL")
API_ENDPOINT_EMBEDDING=os.getenv("API_ENDPOINT_EMBEDDING")

# EMBEDDINGS OPENAI

print("Initialisation d'OPENAI...")

embedding_function = AzureOpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    api_key=OPENAI_API_KEY, 
    azure_endpoint=API_ENDPOINT_EMBEDDING
)

print("Embeddings chargés")


# CHARGEMENT DES CHUNKS


documents = []

files = [
    f for f in os.listdir(CHUNKS_DIR)
    if f.endswith(".json")
]

print(f"\n{len(files)} fichiers détectés")


for file in files:

    file_path = os.path.join(CHUNKS_DIR, file)

    print(f"\nLecture : {file}")

    with open(file_path, "r", encoding="utf-8") as f:

        chunks = json.load(f)

    for chunk in chunks:
        voir=embedding_function.embed_documents(chunk["content"])
        print(f"\nLecture : {voir[0]}")
        #document = Document(

         #   page_content=chunk["content"],

          #  metadata={
           #     "source": chunk["source"],
            #    "chunk_id": chunk["id"],
             #   "length": chunk["length"]
            #}
        #)

        #documents.append(document)


#print(f"\nTotal chunks : {len(documents)}")

# CREATION CHROMADB

#print("\nCréation de ChromaDB...")

#vectordb = Chroma.from_documents(
#    documents=documents,
#    embedding=embedding_function,
##    persist_directory=DB_DIR
#)

# Sauvegarde disque
#vectordb.persist()

#print("\n ChromaDB créée avec succès")
#print(f" Sauvegardée dans : {DB_DIR}")


