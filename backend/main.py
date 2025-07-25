from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routing.main import router

app = FastAPI(title="Face Detection API")

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Face Detection API", debug=True)

# Добавьте это ПОСЛЕ создания app
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/faces", StaticFiles(directory="faces"), name="faces")