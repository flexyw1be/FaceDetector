# main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
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

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Импортируем insightface
try:
    import insightface
    from insightface.app import FaceAnalysis

    logger.info("InsightFace загружен успешно")
except ImportError as e:
    logger.error(f"Ошибка импорта insightface: {e}")
    raise

# Пути
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "ml_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_FOLDER = "uploads"
FACES_FOLDER = "faces"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FACES_FOLDER, exist_ok=True)

# Пути к моделям OpenCV
faceProto = str(MODELS_DIR / "opencv_face_detector.pbtxt")
faceModel = str(MODELS_DIR / "opencv_face_detector_uint8.pb")
genderProto = str(MODELS_DIR / "gender_deploy.prototxt")
genderModel = str(MODELS_DIR / "gender_net.caffemodel")
ageProto = str(MODELS_DIR / "age_deploy.prototxt")
ageModel = str(MODELS_DIR / "age_net.caffemodel")

# Глобальные переменные
face_net = None
gender_net = None
age_net = None
current_video_path = None
current_video_id = None

genderList = ['Male', 'Female']
ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)


# Загрузка моделей OpenCV
def load_models():
    global face_net, gender_net, age_net
    try:
        if os.path.exists(faceModel) and os.path.exists(faceProto):
            face_net = cv2.dnn.readNet(faceModel, faceProto)
            logger.info("Face detection model loaded")
        else:
            logger.warning("Face model not found")

        if os.path.exists(genderModel) and os.path.exists(genderProto):
            gender_net = cv2.dnn.readNet(genderModel, genderProto)
            logger.info("Gender model loaded")
        else:
            logger.warning("Gender model not found")

        if os.path.exists(ageModel) and os.path.exists(ageProto):
            age_net = cv2.dnn.readNet(ageModel, ageProto)
            logger.info("Age model loaded")
        else:
            logger.warning("Age model not found")
    except Exception as e:
        logger.error(f"Ошибка загрузки моделей OpenCV: {e}")


load_models()

# Инициализация InsightFace
try:
    # Инициализация модели детекции лиц
    face_app = FaceAnalysis(name='buffalo_s', root='./insightface_models')
    face_app.prepare(ctx_id=0, det_size=(640, 640))
    logger.info("InsightFace model initialized")
except Exception as e:
    logger.error(f"Ошибка инициализации InsightFace: {e}")
    raise

# Создание приложения
app = FastAPI(title="Face Detection API", debug=True)

# Монтируем статику
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/faces", StaticFiles(directory="faces"), name="faces")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
            return None

        person_folder = os.path.join(FACES_FOLDER, f"person_{person_id}")
        os.makedirs(person_folder, exist_ok=True)

        filename = f"detection_{detection_id}.jpg"
        path = os.path.join(person_folder, filename)

        cv2.rectangle(face_region, (int((x2 - x1) * expand), int((y2 - y1) * expand)),
                      (int((x2 - x1) * expand) + (x2 - x1), int((y2 - y1) * expand) + (y2 - y1)),
                      (0, 255, 0), 2)
        cv2.imwrite(path, face_region)
        return f"/faces/person_{person_id}/{filename}"
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        return None


def get_face_embedding(face):
    rgb_face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
    faces = face_app.get(rgb_face)
    return faces[0].embedding if len(faces) > 0 else None


def compare_faces(embedding1, embedding2, threshold=0.6):
    if embedding1 is None or embedding2 is None:
        return False
    similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
    return similarity > (1 - threshold)


def process_frame_for_detection(frame, frame_time, db: Session, video_id: str):
    if face_net is None:
        return []
    try:
        boxes = highlight_face(face_net, frame, 0.3)
        results = []
        for box in boxes:
            x1, y1, x2, y2 = box
            face = frame[y1:y2, x1:x2]
            if face.size == 0:
                continue

            embedding = get_face_embedding(face)
            if embedding is None:
                continue

            gender = "Unknown"
            age = "Unknown"
            if gender_net and age_net:
                try:
                    blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
                    gender_net.setInput(blob)
                    gender = genderList[gender_net.forward().argmax()]
                    age_net.setInput(blob)
                    age = ageList[age_net.forward().argmax()]
                except:
                    pass

            similar_id = None
            persons = db.query(Person).filter(Person.video_id == video_id).all()
            for p in persons:
                if p.face_encoding:
                    stored_embedding = np.frombuffer(p.face_encoding, dtype=np.float64)
                    if compare_faces(embedding, stored_embedding, 0.6):
                        similar_id = p.id
                        p.last_seen = datetime.utcnow()
                        p.appearance_count += 1
                        if not p.gender:
                            p.gender = gender
                        db.commit()
                        break

            if similar_id is None:
                new_person = Person(
                    face_encoding=embedding.tobytes(),
                    gender=gender,
                    age_group=age,
                    video_id=video_id
                )
                db.add(new_person)
                db.commit()
                db.refresh(new_person)
                similar_id = new_person.id

            detection = FaceDetection(
                person_id=similar_id,
                frame_time=frame_time,
                bounding_box=json.dumps(box),
                gender=gender,
                age_group=age,
                video_id=video_id
            )
            db.add(detection)
            db.commit()
            db.refresh(detection)

            img_name = save_face_image_to_person_folder(frame, box, similar_id, detection.id)
            results.append({
                "person_id": similar_id,
                "box": box,
                "gender": gender,
                "age": age,
                "frame_time": frame_time,
                "face_image": img_name
            })
        return results
    except Exception as e:
        logger.error(f"Ошибка обработки кадра: {e}")
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


@app.get("/process-video/")
async def process_video(db: Session = Depends(get_db)):
    if not current_video_path or not current_video_id:
        raise HTTPException(404, "No video uploaded")
    if not os.path.exists(current_video_path):
        raise HTTPException(404, "File not found")
    cap = cv2.VideoCapture(current_video_path)
    if not cap.isOpened():
        raise HTTPException(500, "Cannot open video file")
    frame_count = 0
    max_frames = 30
    while frame_count < max_frames:
        success, frame = cap.read()
        if not success:
            break
        time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        process_frame_for_detection(frame, time, db, current_video_id)
        frame_count += 1
    cap.release()
    return {"message": "OK", "frames": frame_count, "video_id": current_video_id}


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
            face_images = [f"/faces/person_{p.id}/detection_{d.id}.jpg" for d in dets]
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
                        "face_image": f"/faces/person_{p.id}/detection_{d.id}.jpg"
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
            "gender_detection": gender_net is not None,
            "age_detection": age_net is not None,
            "face_recognition": 'face_app' in globals()
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
