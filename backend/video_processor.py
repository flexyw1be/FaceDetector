import cv2
import os
import json
import numpy as np
from datetime import datetime

from deepface import DeepFace
from sqlalchemy.orm import Session
from models import Person, FaceDetection
from face_utils import get_age_group, get_face_embedding, compare_faces, is_valid_face
from config import FACES_FOLDER, BASE_DIR
import logging

logger = logging.getLogger(__name__)

face_tracks = []


def highlight_face(net, frame, conf_threshold=0.7):
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
                if x1 >= x2 or y1 >= y2 or x2 > w or y2 > h:
                    continue
                boxes.append(([x1, y1, x2, y2], conf))
        return boxes
    except Exception as e:
        logger.error(f"Error in highlight_face: {e}")
        return []


def track_faces(existing_tracks, new_boxes, frame):
    tracked = []
    used_indices = set()

    for i, track_info in enumerate(existing_tracks):
        try:
            box, old_conf = track_info
        except ValueError:
            logger.error(f"Invalid track format: {track_info}")
            continue

        min_distance = float('inf')
        match_idx = -1
        for j, (new_box, new_conf) in enumerate(new_boxes):
            if j in used_indices:
                continue
            cx1 = (box[0] + box[2]) / 2
            cy1 = (box[1] + box[3]) / 2
            cx2 = (new_box[0] + new_box[2]) / 2
            cy2 = (new_box[1] + new_box[3]) / 2
            distance = np.sqrt((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2)
            if distance < min_distance and distance < 100:
                min_distance = distance
                match_idx = j

        if match_idx != -1:
            tracked.append((new_boxes[match_idx], i))
            used_indices.add(match_idx)
        else:
            reduced_conf = max(0.1, old_conf * 0.9)
            tracked.append(((box, reduced_conf), i))

    for j, (box, conf) in enumerate(new_boxes):
        if j not in used_indices:
            tracked.append(((box, conf), -1))

    return tracked


def save_face_image(frame, box, person_id, detection_id):
    try:
        x1, y1, x2, y2 = box
        h, w = frame.shape[:2]
        expand = 0.3
        new_x1 = max(0, x1 - int((x2 - x1) * expand))
        new_y1 = max(0, y1 - int((y2 - y1) * expand))
        new_x2 = min(w, x2 + int((x2 - x1) * expand))
        new_y2 = min(h, y2 + int((y2 - y1) * expand))

        face_region = frame[new_y1:new_y2, new_x1:new_x2]
        if face_region.size == 0 or (new_x2 - new_x1) < 50 or (new_y2 - new_y1) < 50:
            return None

        person_dir = os.path.join(BASE_DIR, FACES_FOLDER, f"person_{person_id}")
        os.makedirs(person_dir, exist_ok=True)
        filename = f"face_{detection_id}.jpg"
        img_path = os.path.join(person_dir, filename)
        cv2.imwrite(img_path, face_region, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return f"faces/person_{person_id}/{filename}"
    except Exception as e:
        logger.error(f"Error saving face image: {e}")
        return None


def process_frame(frame, frame_time, db: Session, video_id: str, face_net):
    global face_tracks
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        frame_processed = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        new_boxes = highlight_face(face_net, frame_processed, 0.7)
        tracked_boxes = track_faces(face_tracks, new_boxes, frame_processed)
        face_tracks = [item[0] for item in tracked_boxes]

        results = []
        for item in tracked_boxes:
            try:
                box_info, track_id = item
                box, conf = box_info
                x1, y1, x2, y2 = box
                face_region = frame[y1:y2, x1:x2]

                if not is_valid_face(face_region):
                    continue

                embedding = get_face_embedding(face_region)
                if embedding is None:
                    continue

                gender = "Unknown"
                age_group = "Unknown"
                try:
                    rgb_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2RGB)
                    analysis = DeepFace.analyze(
                        img_path=rgb_face,
                        actions=['gender', 'age'],
                        enforce_detection=False,
                        detector_backend='opencv',
                        silent=True
                    )
                    if isinstance(analysis, list):
                        analysis = analysis[0]
                    if 'gender' in analysis:
                        gender = max(analysis['gender'].items(), key=lambda x: x[1])[0]
                    if 'age' in analysis:
                        age = analysis['age']
                        age_group = get_age_group(age)
                except Exception as e:
                    logger.error(f"Analysis error: {e}")

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
                                updated_embedding = (stored_embedding * (
                                            p.appearance_count - 1) + embedding) / p.appearance_count
                                p.face_encoding = updated_embedding.tobytes()
                                db.commit()
                                break
                        except Exception as e:
                            logger.error(f"Face comparison error: {e}")
                            continue

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
                    except Exception as e:
                        db.rollback()
                        logger.error(f"Person creation error: {e}")
                        continue

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

                img_path = save_face_image(frame, box, similar_id, detection.id)
                if img_path:
                    detection.image_path = img_path
                    db.commit()
                else:
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

            except Exception as e:
                logger.error(f"Error processing face: {e}")
                continue

        return results
    except Exception as e:
        logger.error(f"Frame processing error: {e}")
        db.rollback()
        return []