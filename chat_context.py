import os

from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings

try:
    from langchain_chroma import Chroma            # version recommandée
except ImportError:
    from langchain_community.vectorstores import Chroma


# ENV

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CHAT_MODEL = os.getenv("CHAT_MODEL")
CHAT_ENDPOINT = os.getenv("API_ENDPOINT_GPT")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
EMBEDDING_ENDPOINT = os.getenv("API_ENDPOINT_EMBEDDING")


# DATABASE (même dossier que DB_DIR dans indexation.py)
# Tu peux définir DB_DIR dans le .env pour changer de machine sans modifier le code.

DB_DIR = os.getenv(
    "DB_DIR",
    r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\chroma_db"
)


# INITIALISATION


def init_rag():
    """Initialise le LLM et ChromaDB. Retourne (llm, vectordb)."""

    embedding_function = AzureOpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
        azure_endpoint=EMBEDDING_ENDPOINT
    )

    vectordb = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embedding_function
    )

    llm = AzureChatOpenAI(
        api_key=OPENAI_API_KEY,
        azure_endpoint=CHAT_ENDPOINT,
        deployment_name=CHAT_MODEL,
        api_version="2024-10-21",
        temperature=0.2     # Réponses stables et factuelles
    )

    return llm, vectordb


# CONTEXTE


def build_context(results):
    """Formate les passages ChromaDB en bloc contexte pour le prompt."""

    context = "\n\n".join([

        f"[Document : {doc.metadata.get('source', 'inconnu')} | "
        f"page {doc.metadata.get('page', '?')}]\n"
        f"{doc.page_content}"

        for doc in results
    ])

    return context


# PROMPT


def build_prompt(context, question):
    """Assemble le prompt augmenté : question + contexte RAG."""

    prompt = f"""
Tu es ONEAD Assistant, un assistant documentaire interne expert en procédures RH.

## RÈGLES ABSOLUES:
-Dire bonjour si seulement si c'est une première interaction dans la session, jamais dans les réponses suivantes.
- Réponds UNIQUEMENT à partir du CONTEXTE fourni ci-dessous.
- Si l'information est absente du contexte, réponds exactement :
  "Je n'ai pas trouvé cette information dans les documents disponibles.
   Veuillez consulter la DRH ou le manuel de procédures correspondant."
- Langue : français uniquement.
- Longueur : entre 50 et 150 mots maximum, pas un mot de plus.
- Ton : professionnel, direct, empathique.
- Si la réponse comporte plusieurs étapes ou éléments : utilise une liste à puces (•).
- Ne cite PAS les sources et n'écris pas de lien : l'application affiche elle-même les documents et les pages sous ta réponse.
- Zéro formule de politesse excessive, zéro répétition.

## FORMAT DE RÉPONSE ATTENDU
[Réponse concise en 50-150 mots]
[Liste à puces si plusieurs éléments]

CONTEXTE :
{context}

QUESTION :
{question}
"""

    return prompt