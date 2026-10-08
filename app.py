"""ONEAD Assistant IA — Interface Enterprise.

Refonte UX/UI Senior SaaS Enterprise :
- Header fixe, sidebar 280px, home premium, conversation 900px, input Copilot-like.
- Charte : #00AEEF / #00C896 / #0A1220 / #111827 / #FFFFFF / #94A3B8 / #38BDF8
- Typographie Inter / Segoe UI. Aucun emoji. SVG monochromes uniquement.
- Fonctionnel RAG inchange : init_rag, search_with_scores, build_context, build_prompt.
"""
from urllib.parse import quote
from datetime import datetime
from pathlib import Path
import uuid

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


# ---------------------------------------------------------------------------
# Constantes UI
# ---------------------------------------------------------------------------

DOCS_URL = "/app/static/docs"

SUGGESTIONS = [
    {
        "key": "search",
        "title": "Rechercher un document",
        "desc": "Retrouvez un document RH dans la base ONEAD.",
        "prompt": "Quels documents RH sont disponibles dans la base ONEAD ?",
        "icon": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>',
    },
    {
        "key": "procedure",
        "title": "Consulter une procédure",
        "desc": "Accédez aux procédures et modes opératoires.",
        "prompt": "Quelle est la procédure de demande de congé ?",
        "icon": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/></svg>',
    },
    {
        "key": "explore",
        "title": "Explorer la documentation",
        "desc": "Parcourez la documentation d’entreprise.",
        "prompt": "Présente la documentation RH disponible dans la base.",
        "icon": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
    },
    {
        "key": "referentiel",
        "title": "Accéder aux référentiels internes",
        "desc": "Consultez les référentiels et guides internes.",
        "prompt": "Quels référentiels internes puis-je consulter ?",
        "icon": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    },
]

ICONS = {
    "new": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
    "chat": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    "doc": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    "db": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "history": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15.5 14"/></svg>',
    "gear": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    "help": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "clip": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>',
    "search": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>',
    "mic": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/></svg>',
    "send": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>',
    "bell": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
}


# ---------------------------------------------------------------------------
# Sync docs statiques
# ---------------------------------------------------------------------------

def sync_static_docs():
    import shutil

    base = Path(__file__).resolve().parent
    raw_dir = base / "data" / "raw"
    static_dir = base / "static" / "docs"
    static_dir.mkdir(parents=True, exist_ok=True)
    if not raw_dir.exists():
        return
    for pdf in raw_dir.glob("*.pdf"):
        dest = static_dir / pdf.name
        if not dest.exists() or dest.stat().st_size != pdf.stat().st_size:
            shutil.copy2(pdf, dest)


sync_static_docs()


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="ONEAD Assistant IA",
    page_icon="static/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Etat session : multi-conversations, theme, recherche
# ---------------------------------------------------------------------------

def _new_id():
    return uuid.uuid4().hex[:8]


if "theme" not in st.session_state:
    st.session_state.theme = "sombre"
if "conversations" not in st.session_state:
    cid = _new_id()
    st.session_state.conversations = {
        cid: {
            "title": "Nouvelle conversation",
            "created_at": datetime.now().strftime("%d/%m %H:%M"),
            "messages": [
                {
                    "role": "assistant",
                    "content": "Bonjour, je suis l'assistant documentaire ONEAD. Interrogez la base documentaire en langage naturel, je réponds à partir des documents de l'entreprise.",
                    "time": datetime.now().strftime("%H:%M"),
                    "sources": [],
                }
            ],
        }
    }
    st.session_state.active_id = cid
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "history_filter" not in st.session_state:
    st.session_state.history_filter = ""
if "toast_welcome" not in st.session_state:
    st.session_state.toast_welcome = False


def get_active_conv():
    cid = st.session_state.active_id
    if cid not in st.session_state.conversations:
        cid = next(iter(st.session_state.conversations))
        st.session_state.active_id = cid
    return st.session_state.conversations[cid]


def create_conversation():
    cid = _new_id()
    st.session_state.conversations[cid] = {
        "title": "Nouvelle conversation",
        "created_at": datetime.now().strftime("%d/%m %H:%M"),
        "messages": [
            {
                "role": "assistant",
                "content": "Bonjour, je suis l'assistant documentaire ONEAD. Posez votre question, je réponds à partir des documents de l'entreprise.",
                "time": datetime.now().strftime("%H:%M"),
                "sources": [],
            }
        ],
    }
    st.session_state.active_id = cid
    st.session_state.pending_question = None


def active_messages():
    return get_active_conv()["messages"]


def is_home():
    msgs = active_messages()
    return len(msgs) <= 1 and msgs[0]["role"] == "assistant"


# ---------------------------------------------------------------------------
# CSS Enterprise (sombre / clair)
# ---------------------------------------------------------------------------

def inject_css(theme: str):
    dark = theme != "clair"
    if dark:
        bg, surface, surface2 = "#0A1220", "#111827", "#0D1626"
        text, muted = "#FFFFFF", "#94A3B8"
        border = "rgba(255,255,255,0.08)"
        input_bg = "#131E32"
        bubble_user = "linear-gradient(135deg, #00AEEF 0%, #0090C8 100%)"
        bubble_assistant = "#141F33"
        hero_sub = "#94A3B8"
    else:
        bg, surface, surface2 = "#F6F9FC", "#FFFFFF", "#EEF3F8"
        text, muted = "#0F172A", "#64748B"
        border = "rgba(15,23,42,0.08)"
        input_bg = "#FFFFFF"
        bubble_user = "linear-gradient(135deg, #00AEEF 0%, #0090C8 100%)"
        bubble_assistant = "#FFFFFF"
        hero_sub = "#64748B"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root {{
            --onead-primary: #00AEEF;
            --onead-secondary: #00C896;
            --onead-accent: #38BDF8;
            --onead-bg: {bg};
            --onead-surface: {surface};
            --onead-surface-2: {surface2};
            --onead-border: {border};
            --onead-text: {text};
            --onead-muted: {muted};
        }}
        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
            background: var(--onead-bg) !important;
            color: var(--onead-text) !important;
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
        }}
        header[data-testid="stHeader"] {{ display: none !important; }}
        #MainMenu, footer {{ visibility: hidden !important; }}
        .block-container {{
            max-width: 1060px !important;
            padding-top: 0.5rem !important;
            padding-bottom: 10rem !important;
        }}

        /* ---- Sidebar 280px ---- */
        [data-testid="stSidebar"] {{
            width: 280px !important;
            min-width: 280px !important;
            background: var(--onead-surface) !important;
            border-right: 1px solid var(--onead-border) !important;
        }}
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: 0.35rem; }}
        .side-label {{
            font-size: 11px; font-weight: 600; letter-spacing: .08em;
            text-transform: uppercase; color: var(--onead-muted);
            margin: 16px 4px 6px 4px;
        }}
        .side-item {{
            display: flex; align-items: center; gap: 10px;
            padding: 9px 12px; border-radius: 10px;
            color: var(--onead-text); font-size: 13.5px; font-weight: 500;
        }}
        .side-item svg {{ color: var(--onead-muted); flex-shrink: 0; }}
        .side-meta {{ font-size: 12px; color: var(--onead-muted); padding: 2px 4px; }}
        [data-testid="stSidebar"] .stButton > button {{
            width: 100%; text-align: left; border-radius: 10px !important;
            background: transparent !important; color: var(--onead-text) !important;
            border: 1px solid transparent !important; font-size: 13.5px !important;
            font-weight: 500 !important; padding: 8px 12px !important;
        }}
        [data-testid="stSidebar"] .stButton > button:hover {{
            background: rgba(0,174,239,0.08) !important;
            border-color: var(--onead-border) !important;
        }}
        .btn-primary button, button[kind="primary"] {{
            background: linear-gradient(135deg, #00AEEF, #00C896) !important;
            border: none !important; color: #fff !important;
            border-radius: 12px !important; font-weight: 600 !important;
        }}

        /* ---- Header fixe ---- */
        .onead-header {{
            position: sticky; top: 0; z-index: 50;
            display: flex; align-items: center; justify-content: space-between;
            gap: 16px; padding: 14px 20px; margin: 8px 0 18px 0;
            background: color-mix(in srgb, var(--onead-surface) 82%, transparent);
            backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
            border: 1px solid var(--onead-border); border-radius: 16px;
            box-shadow: 0 8px 28px rgba(0,0,0,0.28);
        }}
        .onead-brand {{ display: flex; align-items: center; gap: 12px; min-width: 180px; }}
        .onead-brand img {{
            height: 38px; width: auto; border-radius: 10px;
            box-shadow: 0 4px 16px rgba(0,174,239,0.35);
            background: #fff; padding: 3px;
        }}
        .onead-brand-name {{ font-weight: 700; font-size: 17px; letter-spacing: .02em; }}
        .onead-brand-name span {{ color: var(--onead-primary); }}
        .onead-title {{ text-align: center; flex: 1; }}
        .onead-title h1 {{ font-size: 17px !important; font-weight: 700 !important; margin: 0 !important; }}
        .onead-title p {{ margin: 2px 0 0 0 !important; font-size: 12.5px; color: var(--onead-muted); }}
        .onead-actions {{ display: flex; align-items: center; gap: 10px; min-width: 180px; justify-content: flex-end; }}
        .icon-btn {{
            width: 36px; height: 36px; display: inline-flex; align-items: center; justify-content: center;
            border-radius: 10px; border: 1px solid var(--onead-border);
            background: rgba(255,255,255,0.03); color: var(--onead-muted); position: relative;
        }}
        .icon-btn .dot {{
            position: absolute; top: 8px; right: 9px; width: 7px; height: 7px;
            background: var(--onead-secondary); border-radius: 50%;
        }}
        .avatar {{
            width: 36px; height: 36px; border-radius: 50%;
            background: linear-gradient(135deg, #00AEEF, #00C896);
            display: inline-flex; align-items: center; justify-content: center;
            font-size: 12px; font-weight: 700; color: #fff;
        }}

        /* ---- Hero ---- */
        .onead-hero {{ text-align: center; padding: 34px 12px 8px 12px; animation: fadeUp .5s ease both; }}
        .onead-hero img {{
            height: 64px; border-radius: 16px; background: #fff; padding: 6px;
            box-shadow: 0 12px 40px rgba(0,174,239,0.30); margin-bottom: 18px;
        }}
        .onead-hero h2 {{ font-size: 30px !important; font-weight: 700 !important; margin: 0 0 10px 0 !important; }}
        .onead-hero p {{ color: {hero_sub}; font-size: 15px; max-width: 640px; margin: 0 auto !important; line-height: 1.6; }}
        @keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}

        /* ---- Cartes 16px ---- */
        .onead-card {{
            border: 1px solid var(--onead-border); border-radius: 16px;
            background: var(--onead-surface);
            padding: 18px; height: 100%;
            transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
        }}
        .onead-card:hover {{
            transform: translateY(-2px);
            border-color: rgba(0,174,239,0.45);
            box-shadow: 0 10px 28px rgba(0,174,239,0.12);
        }}
        .onead-card .card-icon {{
            width: 38px; height: 38px; border-radius: 11px;
            display: flex; align-items: center; justify-content: center;
            background: rgba(0,174,239,0.12); color: var(--onead-primary);
            margin-bottom: 12px;
        }}
        .onead-card h3 {{ font-size: 14.5px !important; font-weight: 600 !important; margin: 0 0 6px 0 !important; }}
        .onead-card p {{ font-size: 12.8px; color: var(--onead-muted); margin: 0 0 12px 0 !important; line-height: 1.5; }}
        .onead-grid button {{
            width: 100%; border-radius: 10px !important;
            border: 1px solid var(--onead-border) !important;
            background: rgba(0,174,239,0.07) !important;
            color: var(--onead-primary) !important;
            font-size: 13px !important; font-weight: 600 !important;
        }}

        /* ---- Conversation 900px ---- */
        .chat-wrap {{ max-width: 900px; margin: 0 auto; }}
        .msg-row {{ display: flex; margin: 14px 0; animation: fadeUp .3s ease both; }}
        .msg-row.user {{ justify-content: flex-end; }}
        .msg-row.assistant {{ justify-content: flex-start; }}
        .bubble {{
            max-width: 78%; padding: 13px 16px; border-radius: 16px;
            font-size: 14.2px; line-height: 1.65; white-space: normal;
        }}
        .bubble.user-b {{
            background: {bubble_user}; color: #fff;
            border-bottom-right-radius: 6px;
            box-shadow: 0 6px 20px rgba(0,174,239,0.25);
        }}
        .bubble.assist-b {{
            background: {bubble_assistant}; color: var(--onead-text);
            border: 1px solid var(--onead-border);
            border-bottom-left-radius: 6px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.18);
        }}
        .msg-meta {{ font-size: 11px; color: var(--onead-muted); margin-top: 6px; }}
        .msg-row.user .msg-meta {{ text-align: right; }}
        .src-card {{
            border: 1px solid var(--onead-border); border-radius: 12px;
            background: rgba(56,189,248,0.06); padding: 10px 12px; margin-top: 10px;
            font-size: 12.8px;
        }}
        .src-card a {{ color: var(--onead-accent) !important; text-decoration: none !important; font-weight: 600; }}
        .src-card a:hover {{ text-decoration: underline !important; }}
        .drh-card {{
            border: 1px solid rgba(0,200,150,0.35); border-left: 4px solid #00C896;
            background: rgba(0,200,150,0.07); border-radius: 12px;
            padding: 14px 16px; margin-top: 12px; font-size: 13.5px;
        }}

        /* ---- Typing / chargement pro ---- */
        .typing {{ display: inline-flex; gap: 5px; padding: 6px 2px; }}
        .typing span {{
            width: 7px; height: 7px; border-radius: 50%;
            background: var(--onead-primary); animation: blink 1.2s infinite;
        }}
        .typing span:nth-child(2) {{ animation-delay: .15s; }}
        .typing span:nth-child(3) {{ animation-delay: .3s; }}
        @keyframes blink {{ 0%, 80%, 100% {{ opacity: .25; }} 40% {{ opacity: 1; }} }}
        [data-testid="stSpinner"] p {{ color: var(--onead-muted) !important; font-size: 13px !important; }}

        /* ---- Input Copilot 60px / 16px ---- */
        [data-testid="stChatInput"] {{
            position: fixed !important; bottom: 18px !important;
            max-width: 900px !important; left: 50% !important;
            transform: translateX(-50%) !important; z-index: 60 !important;
        }}
        [data-testid="stChatInput"] textarea {{
            min-height: 60px !important; border-radius: 16px !important;
            background: {input_bg} !important; color: var(--onead-text) !important;
            border: 1px solid var(--onead-border) !important;
            box-shadow: 0 10px 32px rgba(0,0,0,0.30) !important;
            font-size: 14.5px !important; padding: 16px 18px !important;
        }}
        [data-testid="stChatInput"] textarea:focus {{
            border-color: rgba(0,174,239,0.6) !important;
            box-shadow: 0 0 0 3px rgba(0,174,239,0.15) !important;
        }}
        .input-toolbar {{
            max-width: 900px; margin: 10px auto 0 auto;
            display: flex; align-items: center; gap: 8px;
        }}
        .tool-hint {{ font-size: 11.5px; color: var(--onead-muted); margin-left: auto; }}

        ::-webkit-scrollbar {{ width: 9px; height: 9px; }}
        ::-webkit-scrollbar-thumb {{ background: rgba(148,163,184,0.28); border-radius: 8px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}

        /* ---- Responsive ---- */
        @media (max-width: 900px) {{
            .onead-title p {{ display: none; }}
            .onead-brand, .onead-actions {{ min-width: auto; }}
            .onead-hero h2 {{ font-size: 24px !important; }}
            .bubble {{ max-width: 88%; }}
            [data-testid="stChatInput"] {{ max-width: calc(100vw - 24px) !important; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_css(st.session_state.theme)


# ---------------------------------------------------------------------------
# Header fixe
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="onead-header">
      <div class="onead-brand">
        <img src="/app/static/logo.png" alt="ONEAD" />
        <div class="onead-brand-name">ONE<span>AD</span></div>
      </div>
      <div class="onead-title">
        <h1>ONEAD Assistant IA</h1>
        <p>Votre assistant documentaire intelligent</p>
      </div>
      <div class="onead-actions">
        <span class="icon-btn" title="Notifications">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
          <span class="dot"></span>
        </span>
        <span class="icon-btn" title="Paramètres">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        </span>
        <span class="avatar" title="Profil utilisateur">AD</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar 280px
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
    if st.button("+  Nouvelle conversation", use_container_width=True):
        create_conversation()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="side-label">Recherche</div>', unsafe_allow_html=True)
    st.session_state.history_filter = st.text_input(
        "Rechercher",
        value=st.session_state.history_filter,
        placeholder="Rechercher dans l'historique...",
        label_visibility="collapsed",
    )

    st.markdown('<div class="side-label">Conversations récentes</div>', unsafe_allow_html=True)
    filt = st.session_state.history_filter.strip().lower()
    conv_items = list(st.session_state.conversations.items())
    shown = 0
    for cid, conv in reversed(conv_items):
        hay = (conv["title"] + " " + " ".join(m.get("content", "") for m in conv["messages"])).lower()
        if filt and filt not in hay:
            continue
        label = conv["title"][:38] + ("…" if len(conv["title"]) > 38 else "")
        prefix = "● " if cid == st.session_state.active_id else "○ "
        if st.button(prefix + label, key=f"conv_{cid}"):
            st.session_state.active_id = cid
            st.rerun()
        shown += 1
        if shown >= 8:
            break
    if shown == 0:
        st.markdown('<div class="side-meta">Aucune conversation trouvée.</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-label">Documents importés</div>', unsafe_allow_html=True)
    docs = sorted((Path("static/docs")).glob("*.pdf")) if Path("static/docs").exists() else []
    if docs:
        st.markdown(f'<div class="side-meta">{len(docs)} document(s) disponible(s)</div>', unsafe_allow_html=True)
        with st.expander(f"Voir les {min(len(docs), 20)} documents"):
            for d in docs[:20]:
                st.markdown(f"- {d.name}")
    else:
        st.markdown('<div class="side-meta">Aucun document importé.</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-label">Base documentaire</div>', unsafe_allow_html=True)
    manifest = get_manifest_info()
    if manifest:
        st.markdown(
            f'<div class="side-meta">Mise à jour : {manifest.get("date_indexation", "?")}<br>'
            f'Documents : {manifest.get("nb_documents", "?")} — '
            f'Chunks : {manifest.get("nb_chunks", "?")}<br>'
            f'Modèle : {manifest.get("embedding_model", "?")}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption("Base non versionnée — lancez src/indexation.py pour générer data/manifest.json.")

    st.markdown('<div class="side-label">Historique</div>', unsafe_allow_html=True)
    total_msgs = sum(len(c["messages"]) for c in st.session_state.conversations.values())
    st.markdown(
        f'<div class="side-meta">{len(st.session_state.conversations)} conversation(s) — {total_msgs} message(s)</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-label">Paramètres</div>', unsafe_allow_html=True)
    theme_choice = st.radio(
        "Thème",
        options=["sombre", "clair"],
        index=0 if st.session_state.theme == "sombre" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        st.rerun()

    st.markdown('<div class="side-label">Aide</div>', unsafe_allow_html=True)
    with st.expander("Aide et confidentialité"):
        st.markdown(
            "Posez vos questions en langage naturel. Les réponses sont générées "
            "exclusivement à partir des documents ONEAD indexés. "
            "Aucune donnée n'est utilisée hors de ce périmètre."
        )
        st.markdown(
            f"Recours : {DRH_CONTACT['nom']} — {DRH_CONTACT['email']} / {DRH_CONTACT['tel']}"
        )


# ---------------------------------------------------------------------------
# RAG
# ---------------------------------------------------------------------------

@st.cache_resource
def load_rag():
    return init_rag()


llm, vectordb = load_rag()


def build_source_objects(results):
    seen = set()
    sources = []
    for doc in results:
        name = doc.metadata.get("source")
        page = doc.metadata.get("page")
        if not name or (name, page) in seen:
            continue
        seen.add((name, page))
        if page and str(page) != "?":
            url = f"{DOCS_URL}/{quote(str(name))}#page={page}"
            label = f"{name} — page {page}"
        else:
            url = f"{DOCS_URL}/{quote(str(name))}"
            label = f"{name}"
        sources.append({"name": str(name), "page": str(page), "url": url, "label": label})
        if len(sources) >= MAX_SOURCES:
            break
    return sources


def render_message(msg):
    role = msg["role"]
    time = msg.get("time", "")
    content = msg.get("content", "")
    sources = msg.get("sources", [])
    cls = "user" if role == "user" else "assistant"
    bcls = "user-b" if role == "user" else "assist-b"
    who = "Vous" if role == "user" else "ONEAD Assistant"
    with st.container():
        st.markdown(
            f'<div class="chat-wrap"><div class="msg-row {cls}"><div style="max-width:78%;width:fit-content;">'
            f'<div class="bubble {bcls}">{content}</div>'
            f'<div class="msg-meta">{who} · {time}</div>'
            f"</div></div></div>",
            unsafe_allow_html=True,
        )
    if sources:
        links = "".join(
            f'<div class="src-card"><a href="{s["url"]}" target="_blank">{s["label"]}</a>'
            f'<div style="color:var(--onead-muted);font-size:12px;">Document consulté — cliquez pour ouvrir à la page citée.</div></div>'
            for s in sources
        )
        st.markdown(
            f'<div class="chat-wrap"><div class="msg-row assistant"><div style="max-width:78%;">'
            f'<div style="font-size:12px;font-weight:600;color:var(--onead-muted);margin-bottom:2px;">RÉFÉRENCES DOCUMENTAIRES</div>'
            f"{links}</div></div></div>",
            unsafe_allow_html=True,
        )
    if msg.get("drh"):
        st.markdown(
            f'<div class="chat-wrap"><div class="drh-card">'
            f"<b>Recours DRH — {DRH_CONTACT['nom']}</b><br>"
            f"{DRH_CONTACT['email']} · {DRH_CONTACT['tel']}<br>"
            f"<span style='color:var(--onead-muted);'>{DRH_CONTACT['horaires']}</span><br>"
            f"Votre question a été journalisée pour une revue par la DRH."
            f"</div></div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Page d'accueil premium
# ---------------------------------------------------------------------------

if is_home():
    st.markdown(
        """
        <div class="onead-hero">
          <img src="/app/static/logo.png" alt="ONEAD" />
          <h2>Comment puis-je vous aider aujourd'hui ?</h2>
          <p>Interrogez votre base documentaire ONEAD en langage naturel et obtenez des réponses fiables basées sur les connaissances de l'entreprise.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    cols = st.columns(4)
    for i, sug in enumerate(SUGGESTIONS):
        with cols[i]:
            st.markdown(
                f"""
                <div class="onead-card">
                  <div class="card-icon">{sug["icon"]}</div>
                  <h3>{sug["title"]}</h3>
                  <p>{sug["desc"]}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div class="onead-grid">', unsafe_allow_html=True)
            if st.button("Utiliser", key=f"sug_{sug['key']}", use_container_width=True):
                st.session_state.pending_question = sug["prompt"]
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
else:
    for m in active_messages():
        render_message(m)


# ---------------------------------------------------------------------------
# Barre d'actions + champ de saisie Copilot
# ---------------------------------------------------------------------------

st.markdown('<div class="chat-wrap"><div class="input-toolbar">', unsafe_allow_html=True)
t1, t2, t3, _ = st.columns([0.14, 0.14, 0.14, 0.58])
with t1:
    if st.button("Joindre", help="Pièce jointe", key="tb_attach"):
        st.toast("Pièce jointe : fonction disponible prochainement.")
with t2:
    if st.button("Recherche", help="Recherche documentaire", key="tb_search"):
        st.toast("Recherche documentaire activée sur la base ONEAD.")
with t3:
    if st.button("Micro", help="Microphone", key="tb_mic"):
        st.toast("Dictée vocale : fonction disponible prochainement.")
st.markdown(
    '<div class="tool-hint">Réponses basées exclusivement sur vos documents ONEAD</div></div></div>',
    unsafe_allow_html=True,
)

question = st.chat_input("Posez votre question sur les documents ONEAD...")

if st.session_state.pending_question and not question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None


# ---------------------------------------------------------------------------
# Pipeline RAG
# ---------------------------------------------------------------------------

if question:
    now = datetime.now().strftime("%H:%M")
    conv = get_active_conv()
    conv["messages"].append({"role": "user", "content": question, "time": now, "sources": []})
    if conv["title"] == "Nouvelle conversation":
        conv["title"] = question[:45] + ("…" if len(question) > 45 else "")

    render_message(conv["messages"][-1])

    with st.spinner("ONEAD Assistant consulte la base documentaire..."):
        results, scored = search_with_scores(vectordb, question, k=TOP_K)
        context = build_context(results)
        prompt = build_prompt(context, question)

        placeholder = st.empty()
        placeholder.markdown(
            '<div class="chat-wrap"><div class="msg-row assistant">'
            '<div class="bubble assist-b"><span class="typing"><span></span><span></span><span></span></span></div>'
            "</div></div>",
            unsafe_allow_html=True,
        )
        full_response = ""
        holder = st.empty()
        for chunk in llm.stream(prompt):
            full_response += chunk.content
            holder.markdown(
                f'<div class="chat-wrap"><div class="msg-row assistant">'
                f'<div style="max-width:78%;"><div class="bubble assist-b">{full_response}</div>'
                f'<div class="msg-meta">ONEAD Assistant · {now}</div></div></div></div>',
                unsafe_allow_html=True,
            )
        placeholder.empty()

    sources = build_source_objects(results)
    needs_drh = is_refusal(full_response) or not results
    if needs_drh and not is_refusal(full_response):
        from src.config import REFUSAL_MESSAGE

        full_response = REFUSAL_MESSAGE
    if needs_drh:
        log_unanswered(question, scored)
        st.toast("Question transmise pour revue DRH.")

    assistant_msg = {
        "role": "assistant",
        "content": full_response,
        "time": datetime.now().strftime("%H:%M"),
        "sources": [] if needs_drh else sources,
        "drh": needs_drh,
    }
    conv["messages"].append(assistant_msg)
    st.rerun()
