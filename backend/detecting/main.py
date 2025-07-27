from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import cv2
import os
import uuid
from pathlib import Path
import numpy as np
import json
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from deepface import DeepFace
from sqlalchemy import inspect, text
from sqlalchemy import desc  # Добавлен импорт для сортировки

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "ml_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_FOLDER = "uploads"
FACES_FOLDER = "faces"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FACES_FOLDER, exist_ok=True)

faceProto = str(MODELS_DIR / "opencv_face_detector.pbtxt")
faceModel = str(MODELS_DIR / "opencv_face_detector_uint8.pb")

face_net = None
current_video_path = None
current_video_id = None

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database models
class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True, index=True)
    face_encoding = Column(Text)
    gender = Column(String)
    age_group = Column(String)
    video_id = Column(String)
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    appearance_count = Column(Integer, default=1)


class FaceDetection(Base):
    __tablename__ = "face_detections"
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('persons.id'))
    frame_time = Column(DateTime)
    bounding_box = Column(Text)
    gender = Column(String)
    age_group = Column(String)
    video_id = Column(String)
    image_path = Column(String)
    confidence = Column(Float)  # Добавлен столбец confidence


# Функция для проверки и обновления структуры БД
def check_and_update_db():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('face_detections')]

    if 'confidence' not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE face_detections ADD COLUMN confidence REAL"))
            logger.info("Добавлен столбец confidence в таблицу face_detections")


# Создаем таблицы
Base.metadata.create_all(bind=engine)
# Проверяем и обновляем структуру БД
check_and_update_db()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


def load_models():
    global face_net
    try:
        if os.path.exists(faceModel) and os.path.exists(faceProto):
            face_net = cv2.dnn.readNet(faceModel, faceProto)
            logger.info("Face detection model loaded")
        else:
            logger.warning("Face model not found")
    except Exception as e:
        logger.error(f"Ошибка загрузки моделей OpenCV: {e}")


load_models()

app = FastAPI(title="Face Detection API", debug=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/faces", StaticFiles(directory="faces"), name="faces")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def highlight_face(net, frame, conf_threshold=0.7):  # Увеличен порог до 0.7
    if net is None:
        return []
    try:
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123], False, False)
        net.setInput(blob)
        detections = net.forward()
        boxes = []
        for i in range(detections.shape[2]):
            conf = detections[0, 0, i, 2]
            if conf > conf_threshold:
                x1 = int(detections[0, 0, i, 3] * w)
                y1 = int(detections[0, 0, i, 4] * h)
                x2 = int(detections[0, 0, i, 5] * w)
                y2 = int(detections[0, 0, i, 6] * h)

                # Проверка размера лица
                face_width = x2 - x1
                face_height = y2 - y1
                min_face_size = 80  # Минимальный размер лица в пикселях

                if face_width < min_face_size or face_height < min_face_size:
                    continue

                # Проверка на разумные координаты
                if x1 >= x2 or y1 >= y2 or x2 > w or y2 > h:
                    continue

                boxes.append(([x1, y1, x2, y2], conf))
        return boxes
    except Exception as e:
        logger.error(f"Ошибка в highlight_face: {e}")
        return []



def get_face_embedding(face):
    try:
        # Улучшенная предобработка
        face = cv2.resize(face, (160, 160))

        # Конвертация в float32 и нормализация
        face = face.astype('float32') / 255.0

        # Расширение размерности для модели
        face = np.expand_dims(face, axis=0)

        # Получение эмбеддинга
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

        # Динамический порог: чем больше появлений, тем строже сравнение
        base_threshold = 0.5
        adaptive_threshold = base_threshold + min(0.2, appearance_count * 0.01)

        return similarity > (1 - adaptive_threshold)
    except Exception as e:
        logger.error(f"Error in compare_faces: {e}")
        return False


def save_face_image(frame, box, person_id, detection_id):
    try:
        x1, y1, x2, y2 = box
        h, w = frame.shape[:2]

        # Увеличиваем область вокруг лица
        expand = 0.3
        new_x1 = max(0, x1 - int((x2 - x1) * expand))
        new_y1 = max(0, y1 - int((y2 - y1) * expand))
        new_x2 = min(w, x2 + int((x2 - x1) * expand))
        new_y2 = min(h, y2 + int((y2 - y1) * expand))

        face_region = frame[new_y1:new_y2, new_x1:new_x2]
        if face_region.size == 0:
            logger.warning("Пустая область лица")
            return None

        # Пропускаем слишком маленькие лица
        if (new_x2 - new_x1) < 50 or (new_y2 - new_y1) < 50:
            logger.warning("Слишком маленькое лицо, пропускаем")
            return None

        person_dir = os.path.join(BASE_DIR, FACES_FOLDER, f"person_{person_id}")
        os.makedirs(person_dir, exist_ok=True)

        filename = f"face_{detection_id}.jpg"
        img_path = os.path.join(person_dir, filename)

        # Исправление: сохраняем изображение в правильном цветовом пространстве
        # OpenCV работает с BGR, поэтому сохраняем как есть
        success = cv2.imwrite(img_path, face_region, [cv2.IMWRITE_JPEG_QUALITY, 90])

        if not success:
            logger.error(f"Не удалось сохранить изображение: {img_path}")
            return None

        return f"faces/person_{person_id}/{filename}"
    except Exception as e:
        logger.error(f"Ошибка сохранения лица: {e}")
        return None


def track_faces(existing_tracks, new_boxes, frame):
    # Простая реализация треклинга на основе расстояния
    tracked = []
    used_indices = set()

    for i, (box, _) in enumerate(existing_tracks):
        min_distance = float('inf')
        match_idx = -1

        for j, (new_box, conf) in enumerate(new_boxes):
            if j in used_indices:
                continue

            # Рассчитываем расстояние между центрами боксов
            cx1 = (box[0] + box[2]) / 2
            cy1 = (box[1] + box[3]) / 2
            cx2 = (new_box[0] + new_box[2]) / 2
            cy2 = (new_box[1] + new_box[3]) / 2

            distance = np.sqrt((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2)

            if distance < min_distance and distance < 100:  # Максимальное расстояние для треклинга
                min_distance = distance
                match_idx = j

        if match_idx != -1:
            tracked.append((new_boxes[match_idx], i))
            used_indices.add(match_idx)
        else:
            # Сохраняем существующий трек с уменьшенным confidence
            tracked.append(((box, max(0.1, conf * 0.9)), i))

    # Добавляем новые обнаружения
    for j, (box, conf) in enumerate(new_boxes):
        if j not in used_indices:
            tracked.append(((box, conf), -1))  # -1 = новый трек

    return tracked


face_tracks = []


def is_valid_face(face_img):
    """Проверяет, является ли обнаруженная область реальным лицом"""
    if face_img.size == 0:
        return False

    # Проверка минимального размера
    if face_img.shape[0] < 50 or face_img.shape[1] < 50:
        return False

    # Преобразование в grayscale для анализа
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)

    # Проверка контрастности (лица обычно имеют хороший контраст)
    contrast = cv2.meanStdDev(gray)[1][0][0]
    if contrast < 20:  # Низкая контрастность
        return False

    return True


def process_frame_for_detection(frame, frame_time, db: Session, video_id: str):
    global face_tracks
    if face_net is None:
        logger.error("Модель детекции лиц не загружена!")
        return []

    try:
        # Улучшенная предобработка кадра
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        frame_processed = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        new_boxes = highlight_face(face_net, frame_processed, 0.7)
        tracked_boxes = track_faces(face_tracks, new_boxes, frame_processed)
        face_tracks = [item[0] for item in tracked_boxes]

        results = []
        for item in tracked_boxes:
            # Безопасная распаковка значений
            try:
                box_info, track_id = item
                box, conf = box_info
            except Exception as e:
                logger.error(f"Ошибка распаковки значений трека: {e}")
                continue

            x1, y1, x2, y2 = box
            # Проверка корректности координат
            if x1 >= x2 or y1 >= y2:
                continue

            face_region = frame[y1:y2, x1:x2]

            # Пропускаем слишком маленькие области
            if face_region.size == 0 or face_region.shape[0] < 50 or face_region.shape[1] < 50:
                continue

            # Проверка валидности лица
            if not is_valid_face(face_region):
                continue

            # Получаем embedding
            embedding = get_face_embedding(face_region)
            if embedding is None:
                logger.warning("Не удалось получить embedding лица")
                continue

            # Анализ пола и возраста
            gender = "Unknown"
            age_group = "Unknown"
            try:
                rgb_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2RGB)
                analysis = DeepFace.analyze(
                    img_path=rgb_face,
                    actions=['gender', 'age'],
                    enforce_detection=False,
                    detector_backend='opencv',
                    silent=True  # Уменьшаем вывод в консоль
                )

                if isinstance(analysis, list):
                    analysis = analysis[0]

                if 'gender' in analysis:
                    gender = max(analysis['gender'].items(), key=lambda x: x[1])[0]

                if 'age' in analysis:
                    age = analysis['age']
                    age_group = get_age_group(age)

                logger.info(f"Анализ: пол={gender}, возраст={age}, группа={age_group}")
            except Exception as e:
                logger.error(f"Ошибка анализа: {e}")

            # Поиск похожих лиц
            similar_id = None
            persons = db.query(Person).filter(Person.video_id == video_id).all()

            for p in persons:
                if p.face_encoding:
                    try:
                        stored_embedding = np.frombuffer(p.face_encoding, dtype=np.float64)
                        if compare_faces(embedding, stored_embedding, p.appearance_count):
                            similar_id = p.id
                            p.last_seen = datetime.utcnow()
                            p.appearance_count += 1

                            # Усредняем эмбеддинги
                            n = p.appearance_count
                            updated_embedding = (stored_embedding * (n - 1) + embedding) / n
                            p.face_encoding = updated_embedding.tobytes()
                            db.commit()
                            break
                    except Exception as e:
                        logger.error(f"Ошибка сравнения лиц: {e}")
                        continue

            # Создаем новую запись, если лицо не найдено
            if similar_id is None:
                try:
                    new_person = Person(
                        face_encoding=embedding.tobytes(),
                        gender=gender,
                        age_group=age_group,
                        video_id=video_id,
                        first_seen=datetime.utcnow(),
                        last_seen=datetime.utcnow(),
                        appearance_count=1
                    )
                    db.add(new_person)
                    db.commit()
                    db.refresh(new_person)
                    similar_id = new_person.id
                    logger.info(f"Создан новый person_id: {similar_id}")
                except Exception as e:
                    db.rollback()
                    logger.error(f"Ошибка создания Person: {e}")
                    continue

            # Создаем запись обнаружения
            detection_time = datetime.utcfromtimestamp(frame_time)
            detection = FaceDetection(
                person_id=similar_id,
                frame_time=detection_time,
                bounding_box=json.dumps(box),
                gender=gender,
                age_group=age_group,
                video_id=video_id,
                image_path=None,
                confidence=conf
            )
            db.add(detection)
            db.commit()
            db.refresh(detection)

            # Сохраняем изображение
            img_path = save_face_image(frame, box, similar_id, detection.id)
            if img_path:
                detection.image_path = img_path
                db.commit()
            else:
                logger.warning(f"Не удалось сохранить изображение для detection_id: {detection.id}")
                # Удаляем запись, если не удалось сохранить изображение
                db.delete(detection)
                db.commit()
                continue

            results.append({
                "person_id": similar_id,
                "box": box,
                "gender": gender,
                "age": age_group,
                "frame_time": frame_time,
                "face_image": img_path,
                "confidence": conf
            })

        return results
    except Exception as e:
        logger.error(f"Критическая ошибка обработки кадра: {e}")
        db.rollback()
        return []

@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...)):
    try:
        ext = file.filename.split('.')[-1].lower()
        if ext not in ['mp4', 'avi', 'mov']:
            raise HTTPException(400, "Unsupported format")

        video_id = str(uuid.uuid4())
        filename = f"{video_id}.mp4"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        with open(filepath, "wb") as f:
            f.write(await file.read())

        if not os.path.exists(filepath):
            raise HTTPException(500, "File not saved")

        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            cap.release()
            raise HTTPException(500, "Cannot open video")
        cap.release()

        global current_video_path, current_video_id
        current_video_path = filepath
        current_video_id = video_id

        return {
            "filename": filename,
            "video_id": video_id,
            "path": f"/uploads/{filename}",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(500, str(e))


processing_status = {
    "is_processing": False,
    "progress": 0,
    "current_video_id": None,
    "message": ""
}


@app.post("/process-video/")
async def start_process_video(db: Session = Depends(get_db)):
    global processing_status, current_video_path, current_video_id

    if not current_video_path or not current_video_id:
        raise HTTPException(404, "No video uploaded")

    if processing_status["is_processing"]:
        raise HTTPException(409, "Video processing already in progress")

    processing_status = {
        "is_processing": True,
        "progress": 0,
        "current_video_id": current_video_id,
        "message": "Начало обработки..."
    }

    def process_video():
        try:
            cap = cv2.VideoCapture(current_video_path)
            if not cap.isOpened():
                raise Exception("Не удалось открыть видеофайл")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = max(1, int(fps / 5)) if fps > 0 else 1

            frame_number = 0
            while True:
                ret, frame = cap.read()
                if not ret: break

                if frame_number % frame_interval == 0:
                    time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                    process_frame_for_detection(frame, time, db, current_video_id)

                if total_frames > 0:
                    progress = int((frame_number / total_frames) * 100)
                    processing_status["progress"] = progress
                    processing_status["message"] = f"Обработка кадра {frame_number}/{total_frames}"

                frame_number += 1

            processing_status.update({
                "is_processing": False,
                "progress": 100,
                "message": "Обработка завершена"
            })
            cap.release()
        except Exception as e:
            processing_status.update({
                "is_processing": False,
                "message": f"Ошибка: {str(e)}"
            })
            logger.error(f"Ошибка обработки видео: {e}")

    import threading
    thread = threading.Thread(target=process_video)
    thread.start()

    return {"message": "Video processing started", "video_id": current_video_id}


@app.get("/process-video/status")
async def get_processing_status():
    return processing_status


@app.get("/results/")
async def get_results(db: Session = Depends(get_db)):
    if not current_video_id:
        raise HTTPException(404, "No video processed")

    try:
        # Фильтруем людей с минимальным количеством появлений
        min_appearances = 2  # Минимум 2 появления

        # Получаем людей, отсортированных по количеству появлений (по убыванию)
        persons = db.query(Person).filter(
            Person.video_id == current_video_id,
            Person.appearance_count >= min_appearances
        ).order_by(Person.appearance_count.desc()).all()  # Сортировка по убыванию

        detections = db.query(FaceDetection).filter(FaceDetection.video_id == current_video_id).all()

        results = []
        for p in persons:
            person_dets = [d for d in detections if d.person_id == p.id]

            # Собираем все изображения для этого человека
            face_images = []
            for d in person_dets:
                if d.image_path:
                    face_images.append(f"http://localhost:8000/{d.image_path}")

            results.append({
                "id": p.id,
                "gender": p.gender,
                "age_group": p.age_group,
                "appearance_count": p.appearance_count,
                "face_images": face_images,
                "detections": [{
                    "id": d.id,
                    "frame_time": d.frame_time,
                    "gender": d.gender,
                    "age_group": d.age_group,
                    "face_image": f"http://localhost:8000/{d.image_path}" if d.image_path else None,
                    "confidence": d.confidence
                } for d in person_dets]
            })

        return {"video_id": current_video_id, "persons": results}
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(500, str(e))


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "models": {
            "face_detection": face_net is not None,
            "face_recognition": True
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
