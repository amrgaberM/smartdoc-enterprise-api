from sentence_transformers import SentenceTransformer
import torch
import logging

logger = logging.getLogger(__name__)

_model = None


def get_embedding(text):
    global _model
    
    if _model is None:
        logger.info("Loading embedding model (all-MiniLM-L6-v2)...")
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        _model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
        logger.info("Model loaded successfully")
    
    if not text:
        return [0.0] * 384
    
    embedding = _model.encode(text)
    return embedding.tolist()