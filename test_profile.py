import cv2
import pickle
from sklearn.neighbors import KNeighborsClassifier

with open('facedata/names.pkl', 'rb') as f:
    LABELS = pickle.load(f)
with open('facedata/faces.pkl', 'rb') as f:
    FACES = pickle.load(f)

knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(FACES, LABELS)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

import sqlite3
conn = sqlite3.connect('database/scholara.db')
c = conn.cursor()
c.execute("SELECT reference_face_url FROM users")
ref = c.fetchone()[0]
print("Reference face URL:", ref)

img = cv2.imread(ref)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
faces = face_cascade.detectMultiScale(gray, 1.3, 5)

if len(faces) > 0:
    x, y, w, h = faces[0]
    crop = img[y:y+h, x:x+w, :]
    resized = cv2.resize(crop, (50,50)).flatten().reshape(1, -1)
    name = knn.predict(resized)[0]
    print("Predicted name for profile photo:", name)
else:
    print("No face found in profile photo")
