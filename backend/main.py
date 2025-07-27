from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import cv2
import os
import uuid
import json
import logging
import threading
from datetime import datetime
from sqlalchemy.orm import Session

# Изменяем импорты с относительных на абсолютные
from config import faceProto, faceModel, UPLOAD_FOLDER
from database import get_db, init_db
from video_processor import process_frame
from models import Person, FaceDetection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Face Detection API", debug=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/faces", StaticFiles(directory="faces"), name="faces")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация базы данных
init_db()

# Глобальные переменные
face_net = None
current_video_path = None
current_video_id = None

processing_status = {
    "is_processing": False,
    "progress": 0,
    "current_video_id": None,
    "message": ""
}


def load_models():
    global face_net
    try:
        if os.path.exists(faceModel) and os.path.exists(faceProto):
            face_net = cv2.dnn.readNet(faceModel, faceProto)
            logger.info("Face detection model loaded")
        else:
            logger.warning("Face model not found")
    except Exception as e:
        logger.error(f"Error loading OpenCV models: {e}")


load_models()


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
        "message": "Processing started..."
    }

    def process_video():
        try:
            cap = cv2.VideoCapture(current_video_path)
            if not cap.isOpened():
                raise Exception("Could not open video file")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = max(1, int(fps / 5)) if fps > 0 else 1

            frame_number = 0
            while True:
                ret, frame = cap.read()
                if not ret: break

                if frame_number % frame_interval == 0:
                    time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                    process_frame(frame, time, db, current_video_id, face_net)

                if total_frames > 0:
                    progress = int((frame_number / total_frames) * 100)
                    processing_status["progress"] = progress
                    processing_status["message"] = f"Processing frame {frame_number}/{total_frames}"

                frame_number += 1

            processing_status.update({
                "is_processing": False,
                "progress": 100,
                "message": "Processing completed"
            })
            cap.release()
        except Exception as e:
            processing_status.update({
                "is_processing": False,
                "message": f"Error: {str(e)}"
            })
            logger.error(f"Video processing error: {e}")

    thread = threading.Thread(target=process_video)
    thread.start()

    return {"message": "Video processing started", "video_id": current_video_id}


@app.get("/process-video/status")
async def get_processing_status():
    return processing_status


@app.get("/detections/")
async def get_all_detections(db: Session = Depends(get_db)):
    if not current_video_id:
        raise HTTPException(404, "No video processed")

    try:
        detections = db.query(FaceDetection).filter(FaceDetection.video_id == current_video_id).all()
        return {
            "detections": [{
                "id": d.id,
                "person_id": d.person_id,
                "frame_time": d.frame_time.isoformat(),
                "bounding_box": d.bounding_box,
                "gender": d.gender,
                "age_group": d.age_group,
                "video_id": d.video_id,
                "image_path": d.image_path,
                "confidence": d.confidence
            } for d in detections]
        }
    except Exception as e:
        logger.error(f"Error getting detections: {e}")
        raise HTTPException(500, str(e))


@app.get("/results/")
async def get_results(db: Session = Depends(get_db)):
    if not current_video_id:
        raise HTTPException(404, "No video processed")

    try:
        min_appearances = 2
        persons = db.query(Person).filter(
            Person.video_id == current_video_id,
            Person.appearance_count >= min_appearances
        ).order_by(Person.appearance_count.desc()).all()

        detections = db.query(FaceDetection).filter(FaceDetection.video_id == current_video_id).all()

        results = []
        for p in persons:
            person_dets = [d for d in detections if d.person_id == p.id]
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
