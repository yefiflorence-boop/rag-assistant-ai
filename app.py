from urllib.parse import quote

import streamlit as st
from chat_context import (
    init_rag,
    build_context,
    build_prompt,
    search_with_scores,
    is_refusal,
    log_unanswered,
    get_manifest_info,
)
from src.config import DRH_CONTACT, MAX_SOURCES, TOP_K


# CONFIGURATION

# Les PDF doivent être dans le dossier static/docs/ (à côté de ce fichier).
# Avec enableStaticServing = true, Streamlit les sert à l'adresse app/static/docs/<nom>.pdf
DOCS_URL = "app/static/docs"


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
        if page and str(page) != "?":
            url = f"{DOCS_URL}/{quote(str(name))}#page={page}"
            lines.append(f"- 📄 [{name} — page {page}]({url})")
        else:
            url = f"{DOCS_URL}/{quote(str(name))}"
            lines.append(f"- 📄 [{name}]({url})")

        if len(lines) >= MAX_SOURCES:
            break

    return "\n".join(lines)


def drh_card():
    """Carte de recours DRH formalisée (reco jury #3)."""
    st.warning(
        f"**Recours DRH** — {DRH_CONTACT['nom']}\n\n"
        f"📧 {DRH_CONTACT['email']} | 📞 {DRH_CONTACT['tel']}\n\n"
        f"🕒 {DRH_CONTACT['horaires']}\n\n"
        "Votre question a été journalisée pour une revue par la DRH."
    )


# SIDEBAR : FRAÎCHEUR DE LA BASE (reco jury #2)

manifest = get_manifest_info()
with st.sidebar:
    st.subheader("📚 Base documentaire")
    if manifest:
        st.write(f"**Mise à jour :** {manifest.get('date_indexation', '?')}")
        st.write(f"**Documents :** {manifest.get('nb_documents', '?')}")
        st.write(f"**Chunks :** {manifest.get('nb_chunks', '?')}")
        st.caption(f"Modèle : {manifest.get('embedding_model', '?')}")
    else:
        st.caption("Base non versionnée — lancez `src/indexation.py` pour générer `data/manifest.json`.")


# LOGO

col1, col2, col3 = st.columns([1, 2, 1])

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

    # Retrieval validé : passages filtrés par seuil de pertinence (reco jury #1)
    results, scored = search_with_scores(vectordb, question, k=TOP_K)

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

        # Refus contrôlé → carte DRH + journalisation (reco jury #3)
        if is_refusal(full_response) or not results:
            if not is_refusal(full_response):
                # Sécurité : si aucun passage pertinent, on force le refus
                # plutôt que de laisser le modèle halluciner.
                from src.config import REFUSAL_MESSAGE
                full_response = REFUSAL_MESSAGE
                response_placeholder.markdown(full_response)
            log_unanswered(question, scored)
            drh_card()
            full_response += (
                f"\n\n**Recours DRH :** {DRH_CONTACT['nom']} — "
                f"{DRH_CONTACT['email']} / {DRH_CONTACT['tel']}"
            )
        else:
            # Liens vers les documents sources
            links = source_links(results)

            if links:
                full_response += "\n\n**Sources :**\n" + links
                response_placeholder.markdown(full_response)

    # Sauvegarde dans l'historique de session (les liens sont inclus)
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response
    })
