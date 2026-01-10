import numpy as np
from enum import StrEnum


class EmbeddingModel(StrEnum):
    # choose bge forb better multilingual performance
    BGE_M3 = "bge-m3"
    #choose for english
    NOMIC = "nomic-embed-text"


# Configuration globale
CURRENT_MODEL = EmbeddingModel.BGE_M3
SIMILARITY_THRESHOLD = 0.75


# Optional sentence-transformers for local fallback
_TRANSFORMER_MODEL = None

def get_embedding(text: str) -> np.ndarray:
    """Get the embedding vector for a given text."""
    try:
        import ollama
        response = ollama.embeddings(model=CURRENT_MODEL, prompt=text)
        return np.array(response['embedding'], dtype=np.float32)
    except (ImportError, Exception) as e:
        # Fallback to sentence-transformers
        global _TRANSFORMER_MODEL
        try:
            from sentence_transformers import SentenceTransformer
            if _TRANSFORMER_MODEL is None:
                # Use a lightweight fast model
                _TRANSFORMER_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
            return _TRANSFORMER_MODEL.encode(text)
        except ImportError:
            raise RuntimeError(
                "Embedding extraction failed. Ollama is unavailable and "
                "sentence-transformers is not installed. "
                "Install with: pip install sentence-transformers"
            )


def compute_similarity(text_a: str, text_b: str) -> float:
    """compute the similarity  score  of cosinus (0 à 1)"""
    vec_a = get_embedding(text_a)
    vec_b = get_embedding(text_b)

    # Ensure numpy arrays
    vec_a = np.array(vec_a)
    vec_b = np.array(vec_b)

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