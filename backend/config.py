import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "ml_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_FOLDER = "uploads"
FACES_FOLDER = "faces"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FACES_FOLDER, exist_ok=True)

# Пути к моделям
faceProto = str(MODELS_DIR / "opencv_face_detector.pbtxt")
faceModel = str(MODELS_DIR / "opencv_face_detector_uint8.pb")

# Настройки базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"