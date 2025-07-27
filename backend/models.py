from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

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
    confidence = Column(Float)