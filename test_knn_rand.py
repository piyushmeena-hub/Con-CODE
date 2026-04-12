import pickle
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
with open('facedata/names.pkl', 'rb') as f:
    LABELS = pickle.load(f)
with open('facedata/faces.pkl', 'rb') as f:
    FACES = pickle.load(f)

knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)

# Create a random face
rand_face = np.random.randint(0, 255, (1, 7500))
dist, ind = knn.kneighbors(rand_face)
print("Distance for random noise:", dist)

# What if we give it a completely black image?
black_face = np.zeros((1, 7500))
dist, ind = knn.kneighbors(black_face)
print("Distance for black:", dist)
