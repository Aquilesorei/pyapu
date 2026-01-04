import numpy as np
import ollama
from enum import StrEnum


class EmbeddingModel(StrEnum):
    # choose bge forb better multilingual performance
    BGE_M3 = "bge-m3"
    #choose for english
    NOMIC = "nomic-embed-text"


# Configuration globale
CURRENT_MODEL = EmbeddingModel.BGE_M3
SIMILARITY_THRESHOLD = 0.75


def get_embedding(text: str) -> np.ndarray:
    """Get the embedding vector for a given text."""
    response = ollama.embeddings(model=CURRENT_MODEL, prompt=text)
    return np.array(response['embedding'], dtype=np.float32)


def compute_similarity(text_a: str, text_b: str) -> float:
    """compute the similarity  score  of cosinus (0 à 1)"""
    vec_a = get_embedding(text_a)
    vec_b = get_embedding(text_b)

    dot = float(np.dot(vec_a, vec_b))
    norm_a = float(np.linalg.norm(vec_a))
    norm_b = float(np.linalg.norm(vec_b))

    return dot / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0


if __name__ == "__main__":
    # Test final
    t1 = "Date limite : 01/01/2025"  # Français
    t2 = "Fälligkeitsdatum: 1. Januar 2025"  # Allemand

    score = compute_similarity(t1, t2)
    is_match = score >= SIMILARITY_THRESHOLD

    print(f"Comparaison FR <-> DE : {score:.4f} | Match: {is_match}")