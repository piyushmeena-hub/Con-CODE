import pickle
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
with open('facedata/names.pkl', 'rb') as f:
    LABELS = pickle.load(f)
with open('facedata/faces.pkl', 'rb') as f:
    FACES = pickle.load(f)
print("FACES shape:", FACES.shape)
print("LABELS length:", len(LABELS))
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)
print("Model fit successfully!")
res = knn.predict(FACES[0].reshape(1, -1))
print("Prediction:", res)
