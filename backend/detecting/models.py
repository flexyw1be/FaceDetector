from typing import Text

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import sessionmaker, declarative_base

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
    image_path = Column(String)  # Добавлено поле для пути к изображению
    confidence = Column(Float)  # Добавлено поле для confidence score


# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()