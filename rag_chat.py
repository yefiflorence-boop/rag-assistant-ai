import os
import json

from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings

from langchain_community.vectorstores import Chroma


# =====================================================
# ENV
# =====================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CHAT_MODEL = os.getenv("CHAT_MODEL")
CHAT_ENDPOINT = os.getenv("API_ENDPOINT_GPT")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
EMBEDDING_ENDPOINT = os.getenv("API_ENDPOINT_EMBEDDING")


# =====================================================
# DATABASE
# =====================================================

DB_DIR = r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\chroma_db"


# =====================================================
# INITIALISATION
# =====================================================

def init_rag():

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
        api_version="2024-02-15-preview",
        temperature=0.2
    )

    return llm, vectordb


# =====================================================
# CONTEXTE
# =====================================================

def build_context(results):

    context = "\n\n".join([

        f"SOURCE: {os.path.splitext(doc.metadata.get('source', 'inconnue'))[0]}.pdf\n"
        f"METADATA: {json.dumps(doc.metadata, ensure_ascii=False)}\n"
        f"CONTENU:\n{doc.page_content}"

        for doc in results
    ])

    return context


# =====================================================
# PROMPT
# =====================================================

def build_prompt(context, question):

    prompt = f"""
Tu es ONEAD Assistant, un assistant documentaire interne expert en procédures RH.

## RÈGLES ABSOLUES
- Réponds UNIQUEMENT à partir du CONTEXTE fourni ci-dessous.
- Si l'information est absente du contexte, réponds exactement :
  "Je n'ai pas trouvé cette information dans les documents disponibles.
   Veuillez consulter la DRH ou le manuel de procédures correspondant."
- Langue : français uniquement.
- Longueur : entre 50 et 150 mots maximum, pas un mot de plus.
- Ton : professionnel, direct, empathique.
- Si la réponse comporte plusieurs étapes ou éléments : utilise une liste à puces (•).
- Cite toujours la source (numéro de section ou titre du chapitre) en fin de réponse.
- Zéro formule de politesse excessive, zéro répétition.

## FORMAT DE RÉPONSE ATTENDU
[Réponse concise en 50-150 mots]
[Liste à puces si plusieurs éléments]
Source : nom_du_fichier.pdf [Titre de la section ou numéro du chapitre]

CONTEXTE :
{context}

QUESTION :
{question}
"""

    return prompt