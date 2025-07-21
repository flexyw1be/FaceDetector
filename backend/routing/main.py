from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import uuid
import os
from pathlib import Path
import json
from backend.detecting.main import process_video  # Импорт функции обработки

router = APIRouter(prefix="/api", tags=["API"])

# Конфигурация путей
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"

# Создание директорий
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_video(
        background_tasks: BackgroundTasks,
        video: UploadFile = File(...)
):
    video_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{video_id}_{video.filename}"
    result_path = RESULTS_DIR / f"{video_id}.json"

    try:
        # Сохраняем видео
        with open(file_path, "wb") as buffer:
            while content := await video.read(1024 * 1024):  # Читаем по 1MB за раз
                buffer.write(content)

        # Запускаем обработку в фоне
        background_tasks.add_task(
            process_and_save_results,
            str(file_path),
            str(result_path),
        video_id
    )

        return JSONResponse({
            "video_id": video_id,
            "filename": video.filename,
            "status": "processing",
            "message": "Video uploaded and processing started"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def process_and_save_results(video_path: str, result_path: str, video_id: str):
    """Обрабатывает видео и сохраняет результаты"""
    try:
        results = process_video(video_path)

        # Форматируем результаты
        formatted_results = {
            "video_id": video_id,
            "status": "completed",
            "analysis": {
                "total_faces": len(results),
                "faces": results
            }
        }

        # Сохраняем в JSON
        with open(result_path, "w") as f:
            json.dump(formatted_results, f, indent=2)

    except Exception as e:
        # В случае ошибки сохраняем информацию об ошибке
        with open(result_path, "w") as f:
            json.dump({
                "video_id": video_id,
                "status": "error",
                "error": str(e)
            }, f)


@router.get("/results/{video_id}")
async def get_results(video_id: str):
    """Возвращает результаты анализа видео"""
    result_path = RESULTS_DIR / f"{video_id}.json"

    if not result_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Results not ready or video ID not found"
        )

    with open(result_path, "r") as f:
        results = json.load(f)

    if results["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=results["error"]
        )

    return JSONResponse(results)