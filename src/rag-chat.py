import os
from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings

import json
from langchain_community.vectorstores import Chroma

# ENV

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CHAT_MODEL = os.getenv("CHAT_MODEL")
CHAT_ENDPOINT= os.getenv("API_ENDPOINT_GPT")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
EMBEDDING_ENDPOINT = os.getenv("API_ENDPOINT_EMBEDDING")


# CHROMADB

DB_DIR = r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\chroma_db"

# EMBEDDINGS


embedding_function = AzureOpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    api_key=OPENAI_API_KEY,
    azure_endpoint=EMBEDDING_ENDPOINT
)

# LOAD VECTOR DB

vectordb = Chroma(
    persist_directory=DB_DIR,
    embedding_function=embedding_function
)

# CHAT MODEL

llm = AzureChatOpenAI(
    api_key=OPENAI_API_KEY,
    azure_endpoint=CHAT_ENDPOINT,
    deployment_name=CHAT_MODEL,
    api_version="2024-02-15-preview",
    temperature=0.2
)


# QUESTION UTILISATEUR

question = input("\nPose ta question : ")

# RECHERCHE VECTORIELLE

results = vectordb.similarity_search(
    question,
    k=5
)

# CONTEXTE
# Boucle sur les résultats trouvés

context = "\n\n".join([
    f"SOURCE: {doc.metadata.get('source', 'inconnue')}\nMETADATA: {json.dumps(doc.metadata, ensure_ascii=False)}\nCONTENU:\n{doc.page_content}"
    for doc in results
])


# PROMPT AUGMENTÉ

prompt = f"""
Tu es un assistant IA spécialisé.

Réponds uniquement à partir du contexte fourni.

CONTEXTE :
{context}

QUESTION :
{question}


Toujours répondre en français et de manière concise avec les sources citées.
"""

# GENERATION IA

response = llm.invoke(prompt)

# AFFICHAGE
print (response)

print("\n==========================")
print("REPONSE IA")
print("==========================\n")

print(response.content)