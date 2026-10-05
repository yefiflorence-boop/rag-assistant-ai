from urllib.parse import quote

import streamlit as st
from chat_context import (
    init_rag,
    build_context,
    build_prompt
)


# CONFIGURATION

# Les PDF doivent être dans le dossier static/docs/ (à côté de ce fichier).
# Avec enableStaticServing = true, Streamlit les sert à l'adresse app/static/docs/<nom>.pdf
DOCS_URL = "app/static/docs"

MAX_SOURCES = 3   # nombre maximum de documents affichés sous une réponse


# CONFIGURATION DE LA PAGE

st.set_page_config(
    page_title="ONEAD Assistant",
    page_icon="",
    layout="centered"
)


# LOAD RAG

@st.cache_resource  # Évite de recharger ChromaDB à chaque interaction
def load_rag():
    return init_rag()


llm, vectordb = load_rag()


# LIENS VERS LES SOURCES

def source_links(results):
    """Construit la liste des liens 'document, page N' (sans doublons)."""

    seen = set()
    lines = []

    for doc in results:

        name = doc.metadata.get("source")
        page = doc.metadata.get("page")

        if not name or (name, page) in seen:
            continue

        seen.add((name, page))

        # Ouvre le PDF directement à la bonne page grâce à #page=N
        url = f"{DOCS_URL}/{quote(name)}#page={page}"
        lines.append(f"- 📄 [{name} — page {page}]({url})")

        if len(lines) >= MAX_SOURCES:
            break

    return "\n".join(lines)


# LOGO

col1, col2, col3 = st.columns([1,2,1])

with col2:
    st.image("static/logo.png", width=150)


# HEADER

st.title(" Assistant documentaire ONEAD")

st.caption(
    "Bienvenue sur ONEAD Assistant RH."
)

st.divider()


# MEMORY

# Initialisation de l'historique avec le message d'accueil
if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Bonjour 👋 Je suis l'assistant documentaire ONEAD. Posez-moi vos questions RH."
        }
    ]


# AFFICHAGE HISTORIQUE

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# INPUT USER

question = st.chat_input(
    "Posez votre question..."
)


# PIPELINE RAG

if question:

    # Affichage du message utilisateur
    with st.chat_message("user"):
        st.markdown(question)

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    # Retrieval : 5 passages les plus proches dans ChromaDB
    results = vectordb.similarity_search(
        question,
        k=5
    )

    # Construction du contexte et du prompt augmenté
    context = build_context(results)

    prompt = build_prompt(
        context,
        question
    )

    # Génération et affichage de la réponse en streaming
    with st.chat_message("assistant"):

        response_placeholder = st.empty()
        full_response = ""

        for chunk in llm.stream(prompt):
            full_response += chunk.content
            response_placeholder.markdown(full_response)

        # Liens vers les documents sources (pas affichés si le modèle n'a rien trouvé)
        if "Je n'ai pas trouvé" not in full_response:

            links = source_links(results)

            if links:
                full_response += "\n\n**Sources :**\n" + links
                response_placeholder.markdown(full_response)

    # Sauvegarde dans l'historique de session (les liens sont inclus)
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })