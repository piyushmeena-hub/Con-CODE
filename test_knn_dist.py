import pickle
import numpy as np
from sklearn.neighbors import KNeighborsClassifier

with open('facedata/names.pkl', 'rb') as f:
    LABELS = pickle.load(f)
with open('facedata/faces.pkl', 'rb') as f:
    FACES = pickle.load(f)

knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)

dist, ind = knn.kneighbors(FACES[0].reshape(1, -1))
print("Distance for same face:", dist)

