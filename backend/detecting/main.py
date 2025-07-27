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
from models import get_db, Person, FaceDetection
from deepface import DeepFace

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
    allow_origins=["http://localhost:5175"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def highlight_face(net, frame, conf_threshold=0.5):
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
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w, x2)
                y2 = min(h, y2)
                if x2 > x1 and y2 > y1:
                    boxes.append([x1, y1, x2, y2])
        return boxes
    except Exception as e:
        logger.error(f"Ошибка в highlight_face: {e}")
        return []


def get_face_embedding(face):
    try:
        rgb_face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

        embedding_obj = DeepFace.represent(
            img_path=rgb_face,
            model_name='Facenet',
            enforce_detection=False
        )

        if isinstance(embedding_obj, list):
            if len(embedding_obj) > 0:
                return np.array(embedding_obj[0]['embedding'])
            return None
        elif isinstance(embedding_obj, dict):
            return np.array(embedding_obj['embedding'])
        return None
    except Exception as e:
        logger.error(f"Error in get_face_embedding: {e}")
        return None


def compare_faces(embedding1, embedding2, threshold=0.6):
    if embedding1 is None or embedding2 is None:
        return False

    try:
        emb1 = np.array(embedding1)
        emb2 = np.array(embedding2)

        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

        return similarity > (1 - threshold)
    except Exception as e:
        logger.error(f"Error in compare_faces: {e}")
        return False


def save_face_image_to_person_folder(frame, box, person_id, detection_id):
    try:
        x1, y1, x2, y2 = box
        h, w = frame.shape[:2]

        expand = 0.3
        new_x1 = max(0, x1 - int((x2 - x1) * expand))
        new_y1 = max(0, y1 - int((y2 - y1) * expand))
        new_x2 = min(w, x2 + int((x2 - x1) * expand))
        new_y2 = min(h, y2 + int((y2 - y1) * expand))

        face_region = frame[new_y1:new_y2, new_x1:new_x2]
        if face_region.size == 0:
            logger.warning("Пустая область лица для сохранения")
            return None

        person_folder = os.path.join(FACES_FOLDER, f"person_{person_id}")
        os.makedirs(person_folder, exist_ok=True)

        filename = f"face_{detection_id}.jpg"
        face_path = os.path.join(BASE_DIR, FACES_FOLDER, f"person_{person_id}", filename)

        os.makedirs(os.path.dirname(face_path), exist_ok=True)

        success = cv2.imwrite(face_path, face_region, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not success:
            logger.error(f"Не удалось сохранить изображение по пути: {face_path}")
            return None

        relative_path = f"faces/person_{person_id}/{filename}"  # Убрали начальный слэш
        logger.info(f"Сохранено лицо: {relative_path}")
        return relative_path
    except Exception as e:
        logger.error(f"Ошибка сохранения лица: {str(e)}")
        return None


def process_frame_for_detection(frame, frame_time, db: Session, video_id: str):
    if face_net is None:
        logger.error("Модель детекции лиц не загружена!")
        return []

    try:
        boxes = highlight_face(face_net, frame, 0.2)
        results = []

        if not boxes:
            logger.warning(f"На кадре {frame_time} не обнаружено лиц")
            return []

        logger.info(f"На кадре {frame_time} обнаружено {len(boxes)} лиц")

        for box in boxes:
            x1, y1, x2, y2 = box
            face = frame[y1:y2, x1:x2]

            if face.size == 0:
                logger.warning("Обнаружено лицо нулевого размера")
                continue

            rgb_face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

            embedding = get_face_embedding(face)
            if embedding is None:
                logger.warning("Не удалось получить embedding лица")
                continue

            gender = "Unknown"
            age_group = "Unknown"
            try:
                analysis = DeepFace.analyze(
                    img_path=rgb_face,
                    actions=['gender', 'age'],
                    enforce_detection=False,
                    detector_backend='opencv'
                )

                if isinstance(analysis, list):
                    analysis = analysis[0]

                if 'gender' in analysis:
                    gender = max(analysis['gender'].items(), key=lambda x: x[1])[0]

                if 'age' in analysis:
                    age = analysis['age']
                    age_group = get_age_group(age)

                logger.info(f"DeepFace анализ: пол={gender}, возраст={age}, группа={age_group}")
            except Exception as e:
                logger.error(f"Ошибка DeepFace анализа: {e}")
                db.rollback()

            similar_id = None
            persons = db.query(Person).filter(Person.video_id == video_id).all()

            for p in persons:
                if p.face_encoding:
                    stored_embedding = np.frombuffer(p.face_encoding, dtype=np.float64)
                    if compare_faces(embedding, stored_embedding, 0.6):
                        similar_id = p.id
                        p.last_seen = datetime.utcnow()
                        p.appearance_count += 1
                        try:
                            db.commit()
                            logger.info(f"Найдено совпадение с person_id: {similar_id}")
                        except:
                            db.rollback()
                            logger.error("Ошибка при обновлении записи в БД")
                        break

            if similar_id is None:
                new_person = Person(
                    face_encoding=embedding.tobytes(),
                    gender=str(gender),
                    age_group=str(age_group),
                    video_id=video_id,
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                    appearance_count=1
                )
                db.add(new_person)
                try:
                    db.commit()
                    db.refresh(new_person)
                    similar_id = new_person.id
                    logger.info(f"Создан новый person_id: {similar_id}")
                except Exception as e:
                    db.rollback()
                    logger.error(f"Ошибка при создании новой записи в БД: {e}")
                    continue

            detection = FaceDetection(
                person_id=similar_id,
                frame_time=frame_time,
                bounding_box=json.dumps(box),
                gender=str(gender),
                age_group=str(age_group),
                video_id=video_id
            )
            db.add(detection)
            try:
                db.commit()
                db.refresh(detection)
            except:
                db.rollback()
                logger.error("Ошибка при сохранении обнаружения лица")
                continue

            img_name = save_face_image_to_person_folder(frame, box, similar_id, detection.id)

            results.append({
                "person_id": similar_id,
                "box": box,
                "gender": gender,
                "age": age_group,
                "frame_time": frame_time,
                "face_image": img_name
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

    processing_status["is_processing"] = True
    processing_status["progress"] = 0
    processing_status["current_video_id"] = current_video_id
    processing_status["message"] = "Начало обработки..."

    logger.info(f"Запущена обработка видео: {current_video_path}")

    import threading
    thread = threading.Thread(target=run_video_processing, args=(db,))
    thread.start()

    return {"message": "Video processing started", "video_id": current_video_id}


def run_video_processing(db: Session):
    global processing_status, current_video_path, current_video_id
    try:
        logger.info(f"Начало обработки видео в потоке: {current_video_path}")
        if not os.path.exists(current_video_path):
            logger.error(f"Файл не найден: {current_video_path}")
            processing_status["message"] = "Файл не найден"
            processing_status["is_processing"] = False
            return

        cap = cv2.VideoCapture(current_video_path)
        if not cap.isOpened():
            logger.error("Не удалось открыть видеофайл")
            processing_status["message"] = "Не удалось открыть видеофайл"
            processing_status["is_processing"] = False
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        processing_rate_fps = 5
        frame_interval = max(1, int(fps / processing_rate_fps)) if fps > 0 else 1
        logger.info(f"Параметры видео: {total_frames} кадров, {fps} FPS, длительность: {duration:.2f} сек")

        processed_frames = 0
        frame_number = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if total_frames > 0:
                processing_status["progress"] = int((frame_number / total_frames) * 100)
                processing_status["message"] = f"Обработка кадра {frame_number}/{total_frames}"

            if frame_number % frame_interval == 0:
                time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                logger.info(f"Обработка кадра {frame_number} (время: {time:.2f} сек)")
                results = process_frame_for_detection(frame, time, db, current_video_id)
                if results:
                    logger.info(f"Найдено {len(results)} лиц на кадре {frame_number}")
                processed_frames += 1
            frame_number += 1

        cap.release()
        logger.info(f"Обработка завершена. Обработано {processed_frames} кадров")
        processing_status["progress"] = 100
        processing_status["message"] = "Обработка завершена"
    except Exception as e:
        logger.error(f"Ошибка во время обработки видео: {e}")
        processing_status["message"] = f"Ошибка обработки: {str(e)}"
    finally:
        processing_status["is_processing"] = False


@app.get("/process-video/status")
async def get_processing_status():
    global processing_status
    return {
        "is_processing": processing_status["is_processing"],
        "progress": processing_status["progress"],
        "video_id": processing_status["current_video_id"],
        "message": processing_status["message"]
    }


@app.get("/results/")
async def get_results(db: Session = Depends(get_db)):
    if not current_video_id:
        raise HTTPException(404, "No video processed")
    try:
        persons = db.query(Person).filter(Person.video_id == current_video_id).all()
        detections = db.query(FaceDetection).filter(FaceDetection.video_id == current_video_id).all()
        data = []
        for p in persons:
            dets = [d for d in detections if d.person_id == p.id]
            face_images = [f"faces/person_{p.id}/face_{d.id}.jpg" for d in dets]
            data.append({
                "person": {
                    "id": p.id,
                    "gender": p.gender,
                    "age_group": p.age_group,
                    "first_seen": p.first_seen.isoformat(),
                    "last_seen": p.last_seen.isoformat(),
                    "appearance_count": p.appearance_count,
                    "face_images": face_images
                },
                "detections": [
                    {
                        "id": d.id,
                        "frame_time": d.frame_time,
                        "bounding_box": json.loads(d.bounding_box),
                        "gender": d.gender,
                        "age_group": d.age_group,
                        "face_image": f"faces/person_{p.id}/face_{d.id}.jpg"  # Убрали начальный слэш
                    }
                    for d in dets
                ]
            })
        return {"video_id": current_video_id, "persons": data}
    except Exception as e:
        logger.error(f"Error: {e}")
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
