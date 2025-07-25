# models.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, LargeBinary, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# База данных SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./face_detection.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True, index=True)
    face_encoding = Column(LargeBinary)  # 512-мерный вектор от insightface
    gender = Column(String)
    age_group = Column(String)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    appearance_count = Column(Integer, default=1)
    video_id = Column(String, index=True)

class FaceDetection(Base):
    __tablename__ = "face_detections"
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer)
    frame_time = Column(Float)
    bounding_box = Column(String)  # JSON: [x1, y1, x2, y2]
    gender = Column(String)
    age_group = Column(String)
    video_id = Column(String, index=True)

# Создаём таблицы
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()