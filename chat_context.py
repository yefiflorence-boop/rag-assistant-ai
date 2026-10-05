import json
from datetime import datetime

from dotenv import load_dotenv
import os

from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings

try:
    from langchain_chroma import Chroma            # version recommandée
except ImportError:
    from langchain_community.vectorstores import Chroma

from src.config import (
    DB_DIR,
    MANIFEST_PATH,
    UNANSWERED_PATH,
    REFUSAL_MESSAGE,
    SIMILARITY_THRESHOLD,
)


# ENV

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CHAT_MODEL = os.getenv("CHAT_MODEL")
CHAT_ENDPOINT = os.getenv("API_ENDPOINT_GPT")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
EMBEDDING_ENDPOINT = os.getenv("API_ENDPOINT_EMBEDDING")


# INITIALISATION


def init_rag():
    """Initialise le LLM et ChromaDB. Retourne (llm, vectordb)."""

    embedding_function = AzureOpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
        azure_endpoint=EMBEDDING_ENDPOINT
    )

    vectordb = Chroma(
        persist_directory=str(DB_DIR),
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


# RECHERCHE VALIDÉE (reco jury #1)


def search_with_scores(vectordb, question, k=5, threshold=None):
    """Recherche validée : filtre les passages au-delà du seuil de distance.

    Retourne (docs_filtres, scores_bruts).
    - docs_filtres : documents dont distance <= threshold
    - scores_bruts : liste (doc, score) complète pour audit
    """
    if threshold is None:
        threshold = SIMILARITY_THRESHOLD

    try:
        scored = vectordb.similarity_search_with_relevance_scores(question, k=k)
    except Exception:
        # Fallback si la méthode scorée n'est pas disponible
        docs = vectordb.similarity_search(question, k=k)
        return docs, [(d, None) for d in docs]

    filtered = [doc for doc, score in scored if score is None or score <= threshold]
    return filtered, scored


def is_refusal(text):
    """Détecte si la réponse du modèle est un refus contrôlé."""
    if not text:
        return True
    return REFUSAL_MESSAGE[:30] in text or "Je n'ai pas trouvé" in text


def validate_response(question, docs, response_text, scored=None):
    """Valide la réponse par rapport au référentiel (reco jury #1).

    Retourne un dict d'audit : {valide, raisons, nb_sources, score_moyen}.
    """
    raisons = []
    if not docs:
        raisons.append("aucun passage récupéré (seuil trop strict ou base vide)")
    if is_refusal(response_text):
        # Un refus contrôlé est valide s'il n'y avait rien de pertinent
        return {
            "valide": True,
            "type": "refus_controle",
            "raisons": ["refus contrôlé + renvoi DRH"],
            "nb_sources": 0,
            "score_moyen": None,
        }
    if not response_text or len(response_text.strip()) < 20:
        raisons.append("réponse vide ou trop courte")
    sources = {d.metadata.get("source") for d in docs if d.metadata.get("source")}
    if not sources:
        raisons.append("aucune source traçable")
    scores = [s for _, s in (scored or []) if s is not None]
    score_moyen = sum(scores) / len(scores) if scores else None
    return {
        "valide": len(raisons) == 0,
        "type": "reponse",
        "raisons": raisons or ["réponse ancrée sur N passage(s)"],
        "nb_sources": len(sources),
        "score_moyen": score_moyen,
    }


# CONTEXTE


def build_context(results):
    """Formate les passages ChromaDB en bloc contexte pour le prompt."""

    if not results:
        return "(aucun passage pertinent récupéré)"

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
  "{REFUSAL_MESSAGE}"
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


# MANIFESTE + FEEDBACK DRH (reco jury #2 et #3)


def get_manifest_info():
    """Lit data/manifest.json (date de mise à jour, nb docs/chunks)."""
    if not MANIFEST_PATH.exists():
        return None
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def log_unanswered(question, scored=None):
    """Journalise les questions sans réponse pour revue DRH (reco jury #3)."""
    try:
        UNANSWERED_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "date": datetime.now().isoformat(timespec="seconds"),
            "question": question,
            "scores": [s for _, s in (scored or []) if s is not None][:5],
        }
        with open(UNANSWERED_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
