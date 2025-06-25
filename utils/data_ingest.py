import os
from utils.vector_db import add_chunk, create_tables
from PyPDF2 import PdfReader
import docx2txt

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(docx_path):
    return docx2txt.process(docx_path)

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks

def ingest_file(file_path, source=None):
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        print(f"Skipping unsupported file: {file_path}")
        return
    chunks = chunk_text(text)
    for chunk in chunks:
        add_chunk(chunk, source=source or file_path)

if __name__ == "__main__":
    create_tables()
    folder = "data/legal_pdfs"
    for fname in os.listdir(folder):
        if fname.lower().endswith((".pdf", ".docx")):
            print(f"Ingesting: {fname}")
            ingest_file(os.path.join(folder, fname))
    print("Ingestion complete!")