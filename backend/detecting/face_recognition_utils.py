import cv2
import face_recognition
import numpy as np
from typing import List, Tuple, Optional
import json




import face_recognition_models
import numpy as np

def get_face_embedding(face):
    """Возвращает 128-мерный вектор признаков лица"""
    rgb_face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb_face)
    return encodings[0] if len(encodings) > 0 else None

def compare_faces(embedding1, embedding2, tolerance=0.6):
    if embedding1 is None or embedding2 is None:
        return False
    distance = face_recognition.face_distance([embedding1], embedding2)[0]
    return distance < tolerance


def hamming_distance(hash1: str, hash2: str) -> int:
    """Вычисляет расстояние Хэмминга между двумя хэшами"""
    if len(hash1) != len(hash2):
        return float('inf')
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

