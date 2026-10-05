import json
import re
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from tqdm import tqdm

# CONFIGURATION

INPUT_DIR = Path(r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\raw")
OUTPUT_DIR = Path(r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\output")
LANGUAGE = "fra"
MIN_CHARS = 30   # en dessous, la page est considérée comme scannée


# NETTOYAGE

def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"[\x00-\x08\x0B-\x1F\x7F]", " ", text)   # caractères invisibles (garde \n)
    text = re.sub(r"-\n(\w)", r"\1", text)                    # mots coupés en fin de ligne
    text = re.sub(r"[ \t]+", " ", text)                       # espaces multiples
    text = re.sub(r"\n{3,}", "\n\n", text)                    # lignes vides multiples

    return text.strip()


# EXTRACTION PAGE PAR PAGE

def extract_pages(pdf_path):
    pages = []

    with fitz.open(pdf_path) as doc:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text")

            # Page scannée : OCR de cette page seulement
            if len(text.strip()) < MIN_CHARS:
                image = convert_from_path(
                    str(pdf_path), first_page=i, last_page=i
                )[0]
                text = pytesseract.image_to_string(image, lang=LANGUAGE)

            pages.append({"page": i, "text": clean_text(text)})

    return pages


# TRAITEMENT D'UN PDF

def process_pdf(pdf_path):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / f"{pdf_path.stem}.pages.json"
    pages = extract_pages(pdf_path)

    output_file.write_text(
        json.dumps(pages, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"-> {len(pages)} pages sauvegardées : {output_file}")


# TRAITEMENT DU CORPUS

def main():
    pdf_files = sorted(
        p for p in INPUT_DIR.iterdir() if p.suffix.lower() == ".pdf"
    )

    print(f"Nombre de PDF détectés : {len(pdf_files)}")

    for pdf_file in tqdm(pdf_files):
        print(f"\nTraitement : {pdf_file.name}")
        try:
            process_pdf(pdf_file)
        except Exception as e:
            print(f"ERREUR sur {pdf_file.name} : {e}")

    print("\nTraitement terminé.")


if __name__ == "__main__":
    main()