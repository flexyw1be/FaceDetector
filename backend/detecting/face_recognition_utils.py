import cv2
import numpy as np
from typing import List, Tuple, Optional
import json


# Для простого сравнения лиц будем использовать хэширование
# В реальном приложении лучше использовать dlib или face_recognition библиотеку

def get_face_hash(face_image: np.ndarray) -> str:
    """Создает простой хэш лица для сравнения"""
    # Преобразуем в grayscale
    if len(face_image.shape) == 3:
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = face_image

    # Изменяем размер до 32x32 для создания хэша
    resized = cv2.resize(gray, (32, 32))

    # Вычисляем среднее значение
    mean = resized.mean()

    # Создаем бинарный хэш
    hash_array = (resized > mean).astype(int)
    hash_string = ''.join(hash_array.flatten().astype(str))

    return hash_string


def hamming_distance(hash1: str, hash2: str) -> int:
    """Вычисляет расстояние Хэмминга между двумя хэшами"""
    if len(hash1) != len(hash2):
        return float('inf')
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))


def compare_faces(hash1: str, hash2: str, threshold: int = 100) -> bool:
    """Сравнивает два лица по хэшам"""
    distance = hamming_distance(hash1, hash2)
    return distance <= threshold