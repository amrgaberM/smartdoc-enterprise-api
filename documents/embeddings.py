from sentence_transformers import SentenceTransformer

# We use a small, fast model perfect for standard CPUs
# 'all-mpnet-base-v2' is widely used and robust (768 dimensions)
MODEL_NAME = 'all-mpnet-base-v2'
model = SentenceTransformer(MODEL_NAME)

def get_embedding(text):
    """
    Converts a string of text into a list of 768 numbers.
    """
    if not text or not text.strip():
        return None
        
    # Generate the vector
    vector = model.encode(text)
    
    # Convert numpy array to standard python list (for database storage)
    return vector.tolist()