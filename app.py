import streamlit as st
from chat_context import (
    init_rag,
    build_context,
    build_prompt
)


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

    # Sauvegarde dans l'historique de session
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })