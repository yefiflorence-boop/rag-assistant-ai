"""Configuration centrale du projet RAG ONEAD.

Tous les chemins sont relatifs à la racine du projet pour permettre
un changement de machine sans modifier le code (reco jury #2 :
actualiser la base documentaire).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "output"
CHUNKS_DIR = DATA_DIR / "chunks"
MANIFEST_PATH = DATA_DIR / "manifest.json"
FEEDBACK_DIR = DATA_DIR / "feedback"
UNANSWERED_PATH = FEEDBACK_DIR / "unanswered.jsonl"

# DB_DIR surchargeable via .env, sinon défaut relatif au projet.
DB_DIR = Path(os.getenv("DB_DIR", str(DATA_DIR / "chroma_db")))

# Seuil de pertinence pour la validation des réponses (reco jury #1).
# Chroma retourne une distance cosinus : plus c'est petit, plus c'est pertinent.
# Au-delà du seuil, le passage est écarté.
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "1.0"))

TOP_K = int(os.getenv("TOP_K", "5"))
MAX_SOURCES = int(os.getenv("MAX_SOURCES", "3"))

# Message de refus unique (reco jury #3 : formaliser le recours à la DRH).
REFUSAL_MESSAGE = (
    "Je n'ai pas trouvé cette information dans les documents disponibles. "
    "Veuillez consulter la DRH ou le manuel de procédures correspondant."
)

DRH_CONTACT = {
    "nom": "Direction des Ressources Humaines — ONEAD",
    "email": os.getenv("DRH_EMAIL", "drh@onead.dj"),
    "tel": os.getenv("DRH_TEL", "+253 21 35 00 00"),
    "horaires": "Dim–Jeu, 8h–17h",
}
