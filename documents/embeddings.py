from sentence_transformers import SentenceTransformer

# Initialize a private variable to hold the model in memory
_model = None

def get_embedding(text):
    global _model
    
    # LAZY LOADING: Only load the model if it hasn't been loaded yet
    if _model is None:
        print("🧠 Loading AI Model into memory (This might take a few seconds)...")
        _model = SentenceTransformer('all-mpnet-base-v2')
        print("✅ AI Model loaded successfully!")

    if not text or not text.strip():
        return None
    
    embedding = _model.encode(text)
    return embedding.tolist()