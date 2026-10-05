import json
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

# CONFIGURATION

# Dossier produit par extraction.py (fichiers .pages.json)
INPUT_DIR = Path(r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\output")

# Dossier de sortie des chunks (fichiers _chunks.json)
OUTPUT_DIR = Path(r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\chunks")

CHUNK_SIZE = 800       # taille max d'un chunk (en caractères)
CHUNK_OVERLAP = 100    # chevauchement entre deux chunks d'une même page


# SPLITTER

def create_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        # paragraphes, puis lignes, puis phrases, puis mots
        separators=["\n\n", "\n", ". ", " ", ""]
    )


# TRAITEMENT D'UN FICHIER

def process_file(file_path, splitter):
    """Découpe chaque page en chunks qui gardent leur numéro de page."""

    pages = json.loads(file_path.read_text(encoding="utf-8"))

    # "Manuel_RH.pages.json" -> "Manuel_RH.pdf"
    stem = file_path.name[: -len(".pages.json")]
    pdf_name = f"{stem}.pdf"

    data = []

    for page in pages:

        if not page["text"].strip():
            continue   # page vide

        for j, content in enumerate(splitter.split_text(page["text"])):

            data.append({
                "id": f"{stem}-p{page['page']}-{j}",   # identifiant stable et unique
                "content": content,
                "source": pdf_name,                    # nom du PDF (utilisé pour le lien)
                "page": page["page"],                  # numéro de page (utilisé pour #page=N)
            })

    return data


# PIPELINE PRINCIPAL

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Supprime les anciens chunks pour éviter les doublons à l'indexation
    for old_file in OUTPUT_DIR.glob("*_chunks.json"):
        old_file.unlink()

    splitter = create_splitter()

    files = sorted(INPUT_DIR.glob("*.pages.json"))

    print(f"{len(files)} fichiers détectés")

    for file_path in files:

        print(f"\nTraitement : {file_path.name}")

        chunks = process_file(file_path, splitter)

        stem = file_path.name[: -len(".pages.json")]
        output_file = OUTPUT_DIR / f"{stem}_chunks.json"

        output_file.write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        print(f"Chunks sauvegardés : {output_file}")
        print(f"Nombre de chunks : {len(chunks)}")

    print("\n✔ Chunking terminé")


if __name__ == "__main__":
    main()