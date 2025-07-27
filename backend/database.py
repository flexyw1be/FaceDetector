from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from models import Base
from config import SQLALCHEMY_DATABASE_URL
import logging

logger = logging.getLogger(__name__)

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_and_update_db():
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('face_detections')]

    if 'confidence' not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE face_detections ADD COLUMN confidence REAL"))
            logger.info("Added confidence column to face_detections table")

def init_db():
    Base.metadata.create_all(bind=engine)
    check_and_update_db()