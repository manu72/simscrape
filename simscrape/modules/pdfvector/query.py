"""
Query the FAISS index and return the top relevant chunks.
"""
import pickle
from typing import List, Dict
import argparse
import sys
import logging
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
# import faiss
# import numpy as np

# Load environment variables
load_dotenv()

# ------------------------
# CONFIGURATION
# ------------------------
DB_FILE = os.getenv("DB_FILE", "./output/vector_database.pkl")  # Use environment variable
MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")  # Use environment variable

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the FAISS index
def load_vector_db():
    """Load the FAISS vector database and embeddings model."""
    try:
        with open(DB_FILE, "rb") as f:
            faiss_db = pickle.load(f)
        embedder = SentenceTransformer(MODEL_NAME)
        return faiss_db["index"], faiss_db["text_chunks"], embedder
    except FileNotFoundError:
        logger.error("Vector database not found at %s", DB_FILE)
        sys.exit(1)
    except Exception as e:
        logger.error("Error: %s", str(e))
        sys.exit(1)

# Function to get top relevant chunks
def query_faiss(query: str, min_score: float = 0.5, max_results: int = 20) -> List[Dict]:
    """
    Query the FAISS index and return relevant chunks above the score threshold.
    
    Args:
        query (str): The search query
        min_score (float): Minimum similarity score (0.0 to 1.0)
        max_results (int): Maximum number of results to consider
        
    Returns:
        List[Dict]: List of results with text, metadata, and similarity score
    """
    index, text_chunks, embedder = load_vector_db()

    query_embedding = embedder.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_embedding, max_results)  # Get more results initially

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        score = 1 - (dist / 2)  # Convert distance to similarity score
        if score >= min_score:  # Only include results above threshold
            results.append({
                "text": text_chunks[idx]["text"],
                "metadata": text_chunks[idx]["metadata"],
                "score": score
            })

    return results

def main():
    """CLI interface for querying the vector database."""
    parser = argparse.ArgumentParser(description="Query the PDF vector database")
    parser.add_argument("query", help="The search query")
    parser.add_argument("--min-score", type=float, default=0.5,
                       help="Minimum similarity score (0.0 to 1.0)")
    parser.add_argument("--max-results", type=int, default=20,
                       help="Maximum number of results to consider")
    args = parser.parse_args()

    try:
        results = query_faiss(args.query, args.min_score, args.max_results)
        logger.info("\n🔎 Results for: %s\n", args.query)
        logger.info("Found %d results with score >= %f", len(results), args.min_score)

        # Sort results by score in descending order
        for i, result in enumerate(sorted(results, key=lambda x: x['score'], reverse=True), 1):
            logger.info("\n--- Result %d (Score: %.2f) ---", i, result['score'])
            logger.info("Source: %s, Page: %s", result['metadata']['source'], result['metadata']['page'])
            logger.info("Text: %s...", result['text'][:200])
    except Exception as e:
        logger.error("Error: %s", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
