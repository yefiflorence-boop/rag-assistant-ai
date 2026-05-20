# IMPORTATION DES BIBLIOTHÈQUES 

import os         # Permet de manipuler les fichiers et dossiers
import json       # Permet de lire et écrire des fichiers JSON 
import re         # Permet de faire du nettoyage de texte avec des expressions régulières 

from langchain_community.document_loaders import TextLoader             # Charge des fichiers texte (.txt)
from langchain_text_splitters import RecursiveCharacterTextSplitter     # Permet de découper le texte en morceaux (chunks) avec chevauchement
from langchain_core.documents import Document                           # Représente un document avec son contenu et ses métadonnées



# CONFIGURATION


INPUT_DIR = r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\output"
OUTPUT_DIR = r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\chunks"


# NETTOYAGE TEXTE

def clean_text(text: str) -> str:
    
    # Nettoyage avancé du texte extrait des PDF avant chunking / embeddings.
    

    if not text:
        return ""

    # 1. Normalisation espaces
    text = re.sub(r"\s+", " ", text)

    # 2. Suppression caractères invisibles
    text = re.sub(r"[\x00-\x1F\x7F]", " ", text)

    # 3. Suppression numéros de page
    text = re.sub(r"\bpage\s*\d+\b", "", text, flags=re.IGNORECASE)

    # numéros seuls
    text = re.sub(r"\b\d+\s*$", "", text)

    # 4. Réparer mots coupés
    text = re.sub(r"-\s+", "", text)

    # 5. Ponctuation répétée
    text = re.sub(r"([.,;:!?]){2,}", r"\1", text)

    # 6. Espaces multiples
    text = re.sub(r"\s{2,}", " ", text)

    # 7. Nettoyage final
    text = text.strip()

    return text



# CHUNKING


def create_splitter():
    # Cette fonction crée un splitter pour découper les textes en chunks.
    return RecursiveCharacterTextSplitter(  
        chunk_size=500, 
        chunk_overlap=50, # Découpage avec chevauchement de 50 caractères pour garder du contexte entre les chunks
        separators=["\n\n", "\n", ".", " ", ""] # Découpage par paragraphes, puis lignes, puis phrases, puis espaces, puis caractères si nécessaire
    )


# TRAITEMENT D'UN FICHIER


def process_file(file_path, splitter):

    # Charge le document texte avec l’encodage UTF-8.
    loader = TextLoader(file_path, encoding="utf-8")
    docs = loader.load()                                # Charge le contenu du fichier sous forme de documents LangChain.
    
    # Initialise une liste pour stocker les documents nettoyés.
    cleaned_docs = []

    for doc in docs:                                    # Parcourt chaque document chargé.

        cleaned_text = clean_text(doc.page_content)     # Nettoie le contenu textuel du document.

        cleaned_doc = Document(
            page_content=cleaned_text,
            metadata=doc.metadata
        )

        cleaned_docs.append(cleaned_doc)

   
    # Chunking
   
    chunks = splitter.split_documents(cleaned_docs)     # Découpe les documents nettoyés en plusieurs chunks.

   
    # Préparation sauvegarde
    
    output_data = []                                    # Initialise une liste pour stocker les données des chunks.

    for i, chunk in enumerate(chunks):

        output_data.append({
            "id": i,
            "content": chunk.page_content,
            "source": os.path.basename(file_path),
            "length": len(chunk.page_content) # Calcule la taille du chunk en caractères.
        })

    return output_data



# SAUVEGARDE


def save_chunks(data, output_file):

    with open(output_file, "w", encoding="utf-8") as f:

        json.dump(data, f, ensure_ascii=False, indent=2)


# PIPELINE PRINCIPAL

def main():

    # créer dossier output si absent
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    splitter = create_splitter()             # Crée le splitter utilisé pour le chunking.
    
    # Récupère tous les fichiers texte du dossier INPUT_DIR.
    files = [
        f for f in os.listdir(INPUT_DIR)
        if f.endswith(".txt")
    ]

    print(f"{len(files)} fichiers détectés")
    
    # Parcourt chaque fichier texte.
    for file in files:

        file_path = os.path.join(INPUT_DIR, file)   # Crée le chemin complet du fichier.

        print(f"\nTraitement : {file}")

        chunks = process_file(file_path, splitter)  # Traite le fichier pour obtenir les chunks.
        
         # Crée le chemin du fichier JSON de sortie.
        output_file = os.path.join(
            OUTPUT_DIR,
            file.replace(".txt", "_chunks.json")
        )

        save_chunks(chunks, output_file)

        print(f"Chunks sauvegardés : {output_file}")
        print(f"Nombre de chunks : {len(chunks)}")

    print("\n✔ Chunking terminé")


# EXECUTION

if __name__ == "__main__":

    main()