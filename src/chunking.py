import json

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import OUTPUT_DIR as INPUT_DIR, CHUNKS_DIR as OUTPUT_DIR

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

def _pdf_name_for_txt(txt_stem):
    # Compatibilité ascendante : les anciens .txt correspondent à des PDF.
    return f"{txt_stem}.pdf" if not txt_stem.lower().endswith(".pdf") else txt_stem


def process_pages_file(file_path, splitter):
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

    return data, pdf_name


def process_txt_file(file_path, splitter):
    """Supporte l'ancien format data/output/*.txt (sans numéros de page)."""
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    stem = file_path.stem
    pdf_name = _pdf_name_for_txt(stem.replace(".txt", "")) if stem.endswith(".txt") else f"{stem}.pdf"
    # Cas courant : "Manuel.txt" -> "Manuel.pdf"
    if pdf_name.endswith(".txt.pdf"):
        pdf_name = pdf_name[: -len(".txt.pdf")] + ".pdf"

    data = []
    for j, content in enumerate(splitter.split_text(text)):
        if not content.strip():
            continue
        data.append({
            "id": f"{stem}-{j}",
            "content": content,
            "source": pdf_name,
            "page": "?",
        })
    return data, pdf_name


# PIPELINE PRINCIPAL

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Supprime les anciens chunks pour éviter les doublons à l'indexation
    for old_file in OUTPUT_DIR.glob("*_chunks.json"):
        old_file.unlink()

    splitter = create_splitter()

    pages_files = sorted(INPUT_DIR.glob("*.pages.json")) if INPUT_DIR.exists() else []
    txt_files = sorted(INPUT_DIR.glob("*.txt")) if INPUT_DIR.exists() else []

    print(f"Dossier entrée : {INPUT_DIR}")
    print(f"{len(pages_files)} fichiers .pages.json + {len(txt_files)} fichiers .txt détectés")

    for file_path in pages_files:

        print(f"\nTraitement : {file_path.name}")

        chunks, _ = process_pages_file(file_path, splitter)

        stem = file_path.name[: -len(".pages.json")]
        output_file = OUTPUT_DIR / f"{stem}_chunks.json"

        output_file.write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        print(f"Chunks sauvegardés : {output_file}")
        print(f"Nombre de chunks : {len(chunks)}")

    for file_path in txt_files:
        # Évite de retraiter un .txt déjà couvert par un .pages.json du même stem
        if (INPUT_DIR / f"{file_path.stem}.pages.json").exists():
            continue
        print(f"\nTraitement (legacy txt) : {file_path.name}")

        chunks, _ = process_txt_file(file_path, splitter)

        output_file = OUTPUT_DIR / f"{file_path.stem}_chunks.json"
        output_file.write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"Chunks sauvegardés : {output_file}")
        print(f"Nombre de chunks : {len(chunks)}")

    print("\n✔ Chunking terminé")


if __name__ == "__main__":
    main()
