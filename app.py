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

@st.cache_resource
def load_rag():

    return init_rag()


llm, vectordb = load_rag()

# logo
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

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Bonjour 👋 Je suis l’assistant documentaire ONEAD. Posez-moi vos questions RH."
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



# QUESTION


if question:


    # MESSAGE USER
    with st.chat_message("user"):

        st.markdown(question)

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })


    # SEARCH
    results = vectordb.similarity_search(
        question,
        k=5
    )


    # CONTEXT
    context = build_context(results)


    # PROMPT
    prompt = build_prompt(
        context,
        question
    )


    # RESPONSE
    with st.chat_message("assistant"):

        response_placeholder = st.empty()

        full_response = ""


        # STREAMING
        for chunk in llm.stream(prompt):

            full_response += chunk.content

            response_placeholder.markdown(full_response)


    # SAVE MEMORY
    st.session_state.messages.append({

        "role": "assistant",
        "content": full_response
    })