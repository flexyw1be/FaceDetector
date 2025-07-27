import cv2
import numpy as np
from deepface import DeepFace
import logging
from datetime import datetime
from models import Person, FaceDetection
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_age_group(age):
    age = int(age)
    if age <= 2:
        return "(0-2)"
    elif 4 <= age <= 6:
        return "(4-6)"
    elif 8 <= age <= 12:
        return "(8-12)"
    elif 15 <= age <= 20:
        return "(15-20)"
    elif 25 <= age <= 32:
        return "(25-32)"
    elif 38 <= age <= 43:
        return "(38-43)"
    elif 48 <= age <= 53:
        return "(48-53)"
    else:
        return "(60-100)"


def get_face_embedding(face):
    try:
        face = cv2.resize(face, (160, 160))
        face = face.astype('float32') / 255.0
        face = np.expand_dims(face, axis=0)

        embedding_obj = DeepFace.represent(
            img_path=face,
            model_name='Facenet',
            enforce_detection=False,
            detector_backend='skip'
        )

        if isinstance(embedding_obj, list):
            return np.array(embedding_obj[0]['embedding'])
        return np.array(embedding_obj['embedding'])
    except Exception as e:
        logger.error(f"Error in get_face_embedding: {e}")
        return None


def compare_faces(embedding1, embedding2, appearance_count=1):
    if embedding1 is None or embedding2 is None:
        return False

    try:
        emb1, emb2 = np.array(embedding1), np.array(embedding2)
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        base_threshold = 0.5
        adaptive_threshold = base_threshold + min(0.2, appearance_count * 0.01)
        return similarity > (1 - adaptive_threshold)
    except Exception as e:
        logger.error(f"Error in compare_faces: {e}")
        return False


def is_valid_face(face_img):
    if face_img.size == 0:
        return False
    if face_img.shape[0] < 50 or face_img.shape[1] < 50:
        return False
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    contrast = cv2.meanStdDev(gray)[1][0][0]
    if contrast < 20:
        return False
    return True