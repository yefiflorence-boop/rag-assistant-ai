import os
import json
import re

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# CONFIGURATION


INPUT_DIR = r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\output"
OUTPUT_DIR = r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\chunks"


# NETTOYAGE TEXTE


def clean_text(text: str) -> str:
    """
    Nettoyage avancé du texte extrait des PDF
    avant chunking / embeddings.
    """

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

    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""]
    )


# TRAITEMENT D'UN FICHIER


def process_file(file_path, splitter):

    # Charger document
    loader = TextLoader(file_path, encoding="utf-8")
    docs = loader.load()

    
    # Nettoyage
    
    cleaned_docs = []

    for doc in docs:

        cleaned_text = clean_text(doc.page_content)

        cleaned_doc = Document(
            page_content=cleaned_text,
            metadata=doc.metadata
        )

        cleaned_docs.append(cleaned_doc)

   
    # Chunking
   
    chunks = splitter.split_documents(cleaned_docs)

   
    # Préparation sauvegarde
    
    output_data = []

    for i, chunk in enumerate(chunks):

        output_data.append({
            "id": i,
            "content": chunk.page_content,
            "source": os.path.basename(file_path),
            "length": len(chunk.page_content)
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

    splitter = create_splitter()

    files = [
        f for f in os.listdir(INPUT_DIR)
        if f.endswith(".txt")
    ]

    print(f"{len(files)} fichiers détectés")

    for file in files:

        file_path = os.path.join(INPUT_DIR, file)

        print(f"\nTraitement : {file}")

        chunks = process_file(file_path, splitter)

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