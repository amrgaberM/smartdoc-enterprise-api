from sentence_transformers import SentenceTransformer
import torch
import logging

logger = logging.getLogger(__name__)

# Global variable to hold the model in memory once loaded
_model = None

def get_embedding(text):
    global _model
    
    # Only load the model when the first request comes in
    if _model is None:
        logger.info("🧠 [Lazy Load] Initializing Embedding Model (all-mpnet-base-v2)...")
        try:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            _model = SentenceTransformer('all-mpnet-base-v2', device=device)
            logger.info("✅ Model loaded successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {str(e)}")
            raise e

    # Ensure text is not empty
    if not text:
        return [0.0] * 768  # Return zero vector for empty input

    embedding = _model.encode(text)
    return embedding.tolist()