from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import cv2
import os
import uuid
from pathlib import Path
import numpy as np
from typing import List, Dict
import json
import logging
from sqlalchemy.orm import Session
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Импортируем наши модули
try:
    from models import get_db, Person, FaceDetection
    from face_recognition_utils import get_face_hash, compare_faces

    logger.info("Модели загружены успешно")
except Exception as e:
    logger.error(f"Ошибка загрузки моделей: {e}")

# Инициализация путей к моделям
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "ml_models"

# Создаем папки если их нет
MODELS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
FACES_FOLDER = "faces"  # Папка для сохранения лиц
os.makedirs(FACES_FOLDER, exist_ok=True)

logger.info(f"Путь к моделям: {MODELS_DIR}")

# Пути к файлам моделей
faceProto = str(MODELS_DIR / "opencv_face_detector.pbtxt")
faceModel = str(MODELS_DIR / "opencv_face_detector_uint8.pb")
genderProto = str(MODELS_DIR / "gender_deploy.prototxt")
genderModel = str(MODELS_DIR / "gender_net.caffemodel")
ageProto = str(MODELS_DIR / "age_deploy.prototxt")
ageModel = str(MODELS_DIR / "age_net.caffemodel")

# Глобальные переменные для моделей
face_net = None
gender_net = None
age_net = None

# Глобальные переменные
current_video_path = None
current_video_id = None  # ID текущего видео для фильтрации результатов
genderList = ['Male', 'Female']
ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)


# Попытка загрузить модели
def load_models():
    global face_net, gender_net, age_net

    try:
        if os.path.exists(faceModel) and os.path.exists(faceProto):
            face_net = cv2.dnn.readNet(faceModel, faceProto)
            logger.info("Face detection model loaded successfully")
        else:
            logger.warning("Face detection models not found")

        if os.path.exists(genderModel) and os.path.exists(genderProto):
            gender_net = cv2.dnn.readNet(genderModel, genderProto)
            logger.info("Gender detection model loaded successfully")
        else:
            logger.warning("Gender detection models not found")

        if os.path.exists(ageModel) and os.path.exists(ageProto):
            age_net = cv2.dnn.readNet(ageModel, ageProto)
            logger.info("Age detection model loaded successfully")
        else:
            logger.warning("Age detection models not found")

    except Exception as e:
        logger.error(f"Ошибка загрузки моделей OpenCV: {e}")


# Загружаем модели при старте
load_models()

app = FastAPI(title="Face Detection API", debug=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/faces", StaticFiles(directory="faces"), name="faces")

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def highlight_face(net, frame, conf_threshold=0.5):
    if net is None:
        logger.warning("Face detection model not loaded")
        return []

    try:
        frame_copy = frame.copy()
        frame_height = frame_copy.shape[0]
        frame_width = frame_copy.shape[1]

        blob = cv2.dnn.blobFromImage(frame_copy, 1.0, (300, 300), [104, 117, 123], True, False)
        net.setInput(blob)
        detections = net.forward()
        face_boxes = []

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > conf_threshold:
                x1 = int(detections[0, 0, i, 3] * frame_width)
                y1 = int(detections[0, 0, i, 4] * frame_height)
                x2 = int(detections[0, 0, i, 5] * frame_width)
                y2 = int(detections[0, 0, i, 6] * frame_height)

                # Проверяем границы
                x1 = max(0, min(x1, frame_width - 1))
                x2 = max(0, min(x2, frame_width - 1))
                y1 = max(0, min(y1, frame_height - 1))
                y2 = max(0, min(y2, frame_height - 1))

                if x2 > x1 and y2 > y1:
                    face_boxes.append([x1, y1, x2, y2])

        return face_boxes
    except Exception as e:
        logger.error(f"Ошибка в highlight_face: {e}")
        return []


def save_face_image(frame, box, person_id, detection_id):
    """Сохраняет увеличенное изображение лица"""
    try:
        x1, y1, x2, y2 = box

        # Увеличиваем область чтобы захватить всю голову
        width = x2 - x1
        height = y2 - y1

        # Увеличиваем на 30% с каждой стороны
        expand_x = int(width * 0.3)
        expand_y = int(height * 0.3)

        # Новые координаты с расширением
        new_x1 = max(0, x1 - expand_x)
        new_y1 = max(0, y1 - expand_y)
        new_x2 = min(frame.shape[1], x2 + expand_x)
        new_y2 = min(frame.shape[0], y2 + expand_y)

        # Извлекаем расширенную область
        face_region = frame[new_y1:new_y2, new_x1:new_x2]

        if face_region.size > 0:
            # Создаем имя файла
            face_filename = f"person_{person_id}_detection_{detection_id}.jpg"
            face_path = os.path.join(FACES_FOLDER, face_filename)

            # Рисуем квадрат вокруг лица на расширенном изображении
            cv2.rectangle(face_region,
                          (expand_x, expand_y),
                          (expand_x + width, expand_y + height),
                          (0, 255, 0), 2)

            # Сохраняем изображение
            cv2.imwrite(face_path, face_region)
            return face_filename
        return None
    except Exception as e:
        logger.error(f"Error saving face image: {e}")
        return None


def process_frame_for_detection(frame, frame_time, db: Session, video_id: str):
    """Обрабатывает один кадр и сохраняет результаты в БД"""
    if face_net is None:
        return []

    try:
        face_boxes = highlight_face(face_net, frame, conf_threshold=0.3)
        frame_results = []

        for box in face_boxes:
            x1, y1, x2, y2 = box
            face = frame[max(0, y1):min(y2, frame.shape[0] - 1),
                   max(0, x1):min(x2, frame.shape[1] - 1)]

            if face.size == 0:
                continue

            # Получаем хэш лица для сравнения
            face_hash = get_face_hash(face)

            # Определяем пол и возраст
            gender_pred = "Unknown"
            age_pred = "Unknown"

            if gender_net is not None and age_net is not None:
                try:
                    blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
                    gender_net.setInput(blob)
                    gender_pred_idx = gender_net.forward().argmax()
                    gender_pred = genderList[gender_pred_idx] if gender_pred_idx < len(genderList) else "Unknown"

                    age_net.setInput(blob)
                    age_pred_idx = age_net.forward().argmax()
                    age_pred = ageList[age_pred_idx] if age_pred_idx < len(ageList) else "Unknown"
                except Exception as e:
                    logger.error(f"Error in predictions: {e}")

            # Ищем похожее лицо в базе данных для текущего видео
            similar_person_id = None
            persons = db.query(Person).filter(Person.video_id == video_id).all()

            for person in persons:
                if person.face_encoding:
                    stored_hash = person.face_encoding
                    if compare_faces(face_hash, stored_hash, threshold=200):
                        similar_person_id = person.id
                        # Обновляем информацию о персоне
                        person.last_seen = datetime.utcnow()
                        person.appearance_count += 1
                        if person.gender == 'Unknown' or not person.gender:
                            person.gender = gender_pred
                        db.commit()
                        break

            # Если похожее лицо не найдено, создаем новую запись
            if similar_person_id is None:
                new_person = Person(
                    face_encoding=face_hash,
                    gender=gender_pred,
                    age_group=age_pred,
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                    video_id=video_id  # Связываем с текущим видео
                )
                db.add(new_person)
                db.commit()
                db.refresh(new_person)
                similar_person_id = new_person.id

            # Сохраняем детекцию лица
            detection = FaceDetection(
                person_id=similar_person_id,
                frame_time=frame_time,
                bounding_box=json.dumps(box),
                gender=gender_pred,
                age_group=age_pred,
                video_id=video_id  # Связываем с текущим видео
            )
            db.add(detection)
            db.commit()
            db.refresh(detection)

            # Сохраняем изображение лица
            face_filename = save_face_image(frame, box, similar_person_id, detection.id)

            frame_results.append({
                "person_id": similar_person_id,
                "box": box,
                "gender": gender_pred,
                "age": age_pred,
                "frame_time": frame_time,
                "face_image": face_filename
            })

        return frame_results
    except Exception as e:
        logger.error(f"Error processing frame: {e}")
        return []


@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    try:
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ['mp4', 'avi', 'mov']:
            raise HTTPException(status_code=400, detail="Unsupported video format")

        video_id = str(uuid.uuid4())
        filename = f"{video_id}.{file_extension}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        with open(filepath, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Проверка: существует ли файл?
        if not os.path.exists(filepath):
            raise HTTPException(status_code=500, detail="File not saved")

        # Проверка: можно ли открыть видео через OpenCV?
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            cap.release()
            raise HTTPException(status_code=500, detail="Cannot open video with OpenCV - corrupted or incompatible")
        cap.release()

        global current_video_path, current_video_id
        current_video_path = filepath
        current_video_id = video_id

        return {
            "filename": filename,
            "video_id": video_id,
            "path": f"/uploads/{filename}",  # важно: путь для фронтенда
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/process-video/")
async def process_video(db: Session = Depends(get_db)):
    """Обработка видео и сохранение результатов в БД"""
    global current_video_path, current_video_id

    if current_video_path is None or current_video_id is None:
        raise HTTPException(status_code=404, detail="No video uploaded")

    if not os.path.exists(current_video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    cap = cv2.VideoCapture(current_video_path)
    if not cap.isOpened():
        raise HTTPException(status_code=500, detail="Cannot open video file")

    frame_count = 0
    processed_detections = []

    # Обрабатываем только первые 30 кадров для тестирования
    max_frames = 30

    while frame_count < max_frames:
        success, frame = cap.read()
        if not success:
            break

        frame_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        frame_results = process_frame_for_detection(frame, frame_time, db, current_video_id)

        if frame_results:
            processed_detections.extend(frame_results)

        frame_count += 1

    cap.release()

    return {
        "message": "Video processed successfully",
        "total_frames": frame_count,
        "detections_count": len(processed_detections),
        "video_id": current_video_id
    }


@app.get("/results/")
async def get_video_results(db: Session = Depends(get_db)):
    """Получение результатов только для текущего видео"""
    global current_video_id

    if current_video_id is None:
        raise HTTPException(status_code=404, detail="No video processed")

    try:
        # Получаем всех людей для текущего видео
        persons = db.query(Person).filter(Person.video_id == current_video_id).all()

        # Получаем все детекции для текущего видео
        detections = db.query(FaceDetection).filter(FaceDetection.video_id == current_video_id).all()

        # Группируем детекции по персонам
        persons_with_detections = []
        for person in persons:
            person_detections = [d for d in detections if d.person_id == person.id]
            persons_with_detections.append({
                "person": {
                    "id": person.id,
                    "gender": person.gender,
                    "age_group": person.age_group,
                    "first_seen": person.first_seen.isoformat() if person.first_seen else None,
                    "last_seen": person.last_seen.isoformat() if person.last_seen else None,
                    "appearance_count": person.appearance_count
                },
                "detections": [
                    {
                        "id": detection.id,
                        "frame_time": detection.frame_time,
                        "bounding_box": json.loads(detection.bounding_box) if detection.bounding_box else [],
                        "gender": detection.gender,
                        "age_group": detection.age_group,
                        "face_image": f"http://localhost:8000/face-image/person_{detection.person_id}_detection_{detection.id}.jpg"
                    }
                    for detection in person_detections
                ]
            })

        return {
            "video_id": current_video_id,
            "persons": persons_with_detections,
            "total_persons": len(persons_with_detections),
            "total_detections": len(detections)
        }
    except Exception as e:
        logger.error(f"Error retrieving results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/face-image/{filename}")
async def get_face_image(filename: str):
    """Получение изображения лица"""
    face_path = os.path.join(FACES_FOLDER, filename)
    if os.path.exists(face_path):
        return FileResponse(face_path)
    raise HTTPException(status_code=404, detail="Face image not found")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "models": {
            "face_detection": face_net is not None,
            "gender_detection": gender_net is not None,
            "age_detection": age_net is not None
        }
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")