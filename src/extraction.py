

###
import sys
import os
import re
import fitz                  # PyMuPDF
import pdfplumber
import pytesseract

from pdf2image import convert_from_path
from tqdm import tqdm

# Dossier contenant les PDF
INPUT_DIR = r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\raw"

# Dossier de sortie des fichiers texte
OUTPUT_DIR = r"C:\Users\yefif\AI_Projets\rag-assistant-ai\data\output"

# Langue OCR
LANGUAGE = "fra"

# FONCTION DE NETTOYAGE

def clean_text(text):

    # Nettoie le texte extrait.
    

    if not text:
        return ""

    # Supprime les espaces multiples
    text = re.sub(r"\s+", " ", text)

    # Supprime caractères invisibles
    text = re.sub(r"[\x00-\x1F\x7F]", " ", text)

    # Supprime les doubles ponctuations
    text = re.sub(r"([.,;:!?]){2,}", r"\1", text)

    # Supprime numéros de page
    text = re.sub(r"\bPage\s+\d+\b", "", text)

    # Recolle les mots coupés
    text = re.sub(r"-\s+", "", text)

    # Supprime espaces multiples
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()

# EXTRACTION STANDARD

def extract_text_pymupdf(pdf_path):
    
    # Extraction rapide avec PyMuPDF.
    

    text = []

    try:
        doc = fitz.open(pdf_path)

        for page in doc:

            # Extraction texte page
            page_text = page.get_text("text")

            text.append(page_text)

        doc.close()

    except Exception as e:
        print(f"Erreur PyMuPDF : {e}")

    return "\n".join(text)

# EXTRACTION COMPLEXE 

def extract_text_pdfplumber(pdf_path):
    
    #Extraction alternative pour PDF complexes.
    

    text = []

    try:
        with pdfplumber.open(pdf_path) as pdf:

            for page in pdf.pages:

                page_text = page.extract_text()

                if page_text:
                    text.append(page_text)

    except Exception as e:
        print(f"Erreur pdfplumber : {e}")

    return "\n".join(text)


# OCR POUR PDF SCANNÉS

def extract_text_ocr(pdf_path):
    
    # OCR complet via Tesseract
    

    text = []

    try:

        # Conversion PDF -> images
        images = convert_from_path(pdf_path)

        for image in images:

            # OCR
            ocr_text = pytesseract.image_to_string(
                image,
                lang=LANGUAGE
            )

            text.append(ocr_text)

    except Exception as e:
        print(f"Erreur OCR : {e}")

    return "\n".join(text)

# DÉTECTION PDF SCANNÉ

def is_scanned_pdf(pdf_path):
    
    # Vérifie si le PDF contient du texte.
    

    try:

        doc = fitz.open(pdf_path)

        for page in doc:

            text = page.get_text("text")

            # Si du texte existe
            if text.strip():

                doc.close()

                return False

        doc.close()

    except:
        pass

    return True

# TRAITEMENT D'UN PDF

def process_pdf(pdf_path):

    filename = os.path.basename(pdf_path)        # Récupère le nom du fichier PDF 

    output_file = os.path.join(
        OUTPUT_DIR,
        filename.replace(".pdf", ".txt")         # Crée le chemin du fichier texte de sortie en remplaçant l'extension .pdf par .txt
    )

    print(f"\nTraitement : {filename}")

    text = ""                                    # Variable qui contiendra le texte extrait

    # Vérifie si PDF scanné (image) ou s'il contient déjà du texte sélectionnable
    scanned = is_scanned_pdf(pdf_path)

    # CAS PDF SCANNÉ

    if scanned:

        print("-> PDF scanné détecté")

        text = extract_text_ocr(pdf_path)        # Extraction du texte avec OCR Tesseract
    
    # CAS PDF TEXTE

    else:

        print("-> PDF texte détecté")

         # Extraction principale avec PyMuPDF
        text = extract_text_pymupdf(pdf_path) 

        # Vérifie si l'extraction a échoué ou contient trop peu de texte
        if len(text.strip()) < 100:

            print("-> Fallback pdfplumber")

            text = extract_text_pdfplumber(pdf_path)   # Deuxième méthode d'extraction

    # Nettoyage du texte extrait
    cleaned_text = clean_text(text)

    # Sauvegarde du texte nettoyé dans un fichier .txt
    with open(output_file, "w", encoding="utf-8") as f:

        f.write(cleaned_text)

    print(f"-> Sauvegardé : {output_file}")            # Affiche le chemin du fichier sauvegardé

# TRAITEMENT DU CORPUS

def main():

    # Crée une liste contenant tous les fichiers PDF présents dans le dossier INPUT_DIR
    pdf_files = [

        os.path.join(INPUT_DIR, f)

        for f in os.listdir(INPUT_DIR)

        if f.lower().endswith(".pdf")                  # Vérifie que le fichier se termine par .pdf .lower() permet d'accepter .PDF ou .Pdf
    ]

    print(f"Nombre de PDF détectés : {len(pdf_files)}")        # Affiche le nombre total de PDF détectés

    # Traitement
    for pdf_file in tqdm(pdf_files):                           # Parcourt tous les fichiers PDF en affichant une barre de progression

        process_pdf(pdf_file)                                  # Traite chaque PDF individuellement

    print("\nTraitement terminé.")

# LANCEMENT 
if __name__ == "__main__":                                     # Vérifie que le fichier Python est exécuté directement

    main()                                                     # Lance la fonction principale du programme