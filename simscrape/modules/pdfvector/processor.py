"""
Process PDFs and create a FAISS vector database.
"""
import os
import pickle
import fitz  # PyMuPDF for PDF text extraction
# import openai
import faiss
# import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# ------------------------
# 1️⃣ CONFIGURATION
# ------------------------
PDF_FOLDER = "./input/pdfs"  # Folder containing PDFs
DB_FILE = "./output/vector_database.pkl"  # Save the FAISS index in output directory
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Local model for embeddings

# Load embedding model
embedder = SentenceTransformer(EMBEDDING_MODEL)

# ------------------------
# 2️⃣ FUNCTION: Extract Text from PDFs
# ------------------------
def extract_text_from_pdfs(pdf_folder):
    """Extract text from PDFs in the given folder."""
    text_data = []

    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, filename)
            doc = fitz.open(pdf_path)

            for page_num, page in enumerate(doc):
                text = page.get_text("text")

                # Store text with metadata
                text_data.append({
                    "text": text,
                    "metadata": {"source": filename, "page": page_num + 1}
                })

    return text_data

# ------------------------
# 3️⃣ FUNCTION: Split Text into Chunks
# ------------------------
def split_text(text_data):
    """Split text into chunks of 512 characters with 50 character overlap."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    chunked_data = []

    for item in text_data:
        chunks = text_splitter.split_text(item["text"])
        for chunk in chunks:
            chunked_data.append({
                "text": chunk,
                "metadata": item["metadata"]
            })

    return chunked_data

# ------------------------
# 4️⃣ FUNCTION: Generate Embeddings
# ------------------------
def generate_embeddings(text_chunks):
    """Generate embeddings for text chunks using the embedding model."""
    texts = [item["text"] for item in text_chunks]
    embeddings = embedder.encode(texts, convert_to_numpy=True)
    return embeddings

# ------------------------
# 5️⃣ FUNCTION: Create & Save FAISS Vector Database
# ------------------------
def create_faiss_db(text_chunks, embeddings):
    """Create and save a FAISS vector database."""
    vector_dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(vector_dim)
    index.add(embeddings) # index.add(embeddings.astype('float32'))  # Convert to float32

    # Save metadata separately
    faiss_db = {"index": index, "text_chunks": text_chunks}

    with open(DB_FILE, "wb") as f:
        pickle.dump(faiss_db, f)

    print(f"✅ Vector database saved as {DB_FILE}")

# ------------------------
# 6️⃣ MAIN PIPELINE
# ------------------------
def main():
    """Main function to execute the PDF processing pipeline."""
    print("🔍 Extracting text from PDFs...")
    text_data = extract_text_from_pdfs(PDF_FOLDER)

    print("✂️ Splitting text into chunks...")
    text_chunks = split_text(text_data)

    print("🔢 Generating embeddings...")
    embeddings = generate_embeddings(text_chunks)

    print("📥 Creating FAISS vector database...")
    create_faiss_db(text_chunks, embeddings)

if __name__ == "__main__":
    main()
