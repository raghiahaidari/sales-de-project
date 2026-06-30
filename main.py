import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from google.cloud import storage


BASE_DIR = Path(__file__).resolve().parent
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

app = FastAPI(title="GCS File Upload Portal")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"bucket_name": BUCKET_NAME},
    )


@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    if not BUCKET_NAME:
        raise HTTPException(
            status_code=500,
            detail="GCS_BUCKET_NAME environment variable is not configured.",
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="Please choose a file to upload.")

    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(file.filename)
        blob.upload_from_file(file.file, content_type=file.content_type)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}") from exc
    finally:
        await file.close()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "bucket_name": BUCKET_NAME,
            "message": f"{file.filename} uploaded successfully.",
        },
    )
