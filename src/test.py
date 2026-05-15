# Importation du module os
# Sert à interagir avec le système (variables d’environnement, fichiers, dossiers)
import os

# Importation de load_dotenv
# Permet de charger les variables du fichier .env
from dotenv import load_dotenv

# Importation du modèle d'embeddings Azure OpenAI
# Sert à transformer le texte en vecteurs numériques
from langchain_openai import AzureOpenAIEmbeddings

# Importation de Chroma
# Sert à charger et utiliser la base vectorielle ChromaDB
from langchain_community.vectorstores import Chroma


# Charge automatiquement les variables du fichier .env
load_dotenv()


# Récupère la clé API OpenAI depuis le fichier .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Récupère le nom du modèle d'embedding
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# Récupère l'endpoint Azure OpenAI
API_ENDPOINT_EMBEDDING = os.getenv("API_ENDPOINT_EMBEDDING")


# Chemin du dossier contenant la base ChromaDB
DB_DIR = r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\chroma_db"


# Création de la fonction d'embedding
# Cette fonction convertira le texte en vecteurs
embedding_function = AzureOpenAIEmbeddings(

    # Nom du modèle d'embedding
    model=EMBEDDING_MODEL,

    # Clé API OpenAI
    api_key=OPENAI_API_KEY,

    # URL du service Azure OpenAI
    azure_endpoint=API_ENDPOINT_EMBEDDING
)


# Chargement de la base vectorielle ChromaDB
vectordb = Chroma(

    # Dossier où se trouve la base sauvegardée
    persist_directory=DB_DIR,

    # Fonction d'embedding utilisée pour les recherches
    embedding_function=embedding_function
)


# Affiche un message indiquant que la base est bien chargée
print("ChromaDB chargée")


# Question que l'utilisateur veut rechercher
query = "Comment fonctionne la gestion des absences à l'ONEAD ?"


# Recherche des documents les plus similaires à la question
results = vectordb.similarity_search(

    # Texte recherché
    query,

    # Nombre de résultats à retourner
    k=5
)


# Boucle sur les résultats trouvés
for i, doc in enumerate(results):

    # Affiche le numéro du résultat
    print(f"\nRésultat {i+1}")

    # Affiche une ligne de séparation
    print("-" * 50)

    # Affiche le contenu du chunk trouvé
    print("Contenu :")

    # Affiche le texte du document
    print(doc.page_content)

    # Affiche les métadonnées du document
    print("\nMetadata :")

    # Affiche les informations associées au document
    # Exemple : source, id du chunk, longueur...
    print(doc.metadata)