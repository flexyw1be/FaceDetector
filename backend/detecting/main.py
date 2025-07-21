import cv2
from pathlib import Path
import numpy as np
from typing import List, Dict

# Инициализация путей к моделям
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "ml_models"

faceProto = str(MODELS_DIR / "opencv_face_detector.pbtxt")
faceModel = str(MODELS_DIR / "opencv_face_detector_uint8.pb")
genderProto = str(MODELS_DIR / "gender_deploy.prototxt")
genderModel = str(MODELS_DIR / "gender_net.caffemodel")
ageProto = str(MODELS_DIR / "age_deploy.prototxt")
ageModel = str(MODELS_DIR / "age_net.caffemodel")

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
genderList = ['Male', 'Female']
ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']

# Загрузка моделей
face_net = cv2.dnn.readNet(faceModel, faceProto)
gender_net = cv2.dnn.readNet(genderModel, genderProto)
age_net = cv2.dnn.readNet(ageModel, ageProto)


def highlight_face(net, frame, conf_threshold=0.7):
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
            face_boxes.append([x1, y1, x2, y2])

    return face_boxes


def process_video(video_path: str) -> List[Dict]:
    """Обрабатывает видео и возвращает результаты обнаружения лиц"""
    results = []
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            face_boxes = highlight_face(face_net, frame)

            for box in face_boxes:
                face = frame[max(0, box[1]):min(box[3], frame.shape[0] - 1),
                       max(0, box[0]):min(box[2], frame.shape[1] - 1)]

                if face.size == 0:
                    continue

                blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)

                gender_net.setInput(blob)
                gender_pred = genderList[gender_net.forward().argmax()]

                age_net.setInput(blob)
                age_pred = ageList[age_net.forward().argmax()].strip("()")

                results.append({
                    "box": box,
                    "gender": gender_pred,
                    "age": age_pred,
                    "frame_time": cap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # время в секундах
                })
    finally:
        cap.release()

    return results