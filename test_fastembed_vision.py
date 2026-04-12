from fastembed import ImageEmbedding
import numpy as np

def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

try:
    print("Loading model...")
    model = ImageEmbedding(model_name="Qdrant/clip-ViT-B-32-vision")
    print("Model loaded.")
except Exception as e:
    print(f"Error: {e}")
