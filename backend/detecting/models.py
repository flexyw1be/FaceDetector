from sqlalchemy import Column, Integer, String, Float, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()


class Person(Base):
    __tablename__ = 'persons'

    id = Column(Integer, primary_key=True)
    face_encoding = Column(Text)  # JSON строка с вектором лица
    gender = Column(String(10))
    age_group = Column(String(20))
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    appearance_count = Column(Integer, default=1)
    video_id = Column(String(50))  # ID видео для фильтрации


class FaceDetection(Base):
    __tablename__ = 'face_detections'

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer)  # Ссылка на Person
    frame_time = Column(Float)
    bounding_box = Column(Text)  # JSON строка [x1, y1, x2, y2]
    confidence = Column(Float, default=0.95)
    gender = Column(String(10))
    age_group = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    video_id = Column(String(50))  # ID видео для фильтрации



engine = create_engine('sqlite:///face_detection.db')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()