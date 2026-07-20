
"""
FastAPI app for SkillGap Analyzer.

Place this file at the ROOT of your project, alongside crew.jsonc, agents/, tools/,
plus the new templates/ and static/ folders.

Run with:
    uv add fastapi "uvicorn[standard]" python-multipart jinja2
    uv run uvicorn main:app --reload --port 8000
"""

import shutil
import uuid
from pathlib import Path
import tempfile
import os
import boto3

from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from crewai.project import load_crew

BASE_DIR = Path(__file__).parent
CREW_FILE = BASE_DIR / "crew.jsonc"
# UPLOAD_DIR = BASE_DIR / "uploads"
# UPLOAD_DIR.mkdir(exist_ok=True)
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
s3_client = boto3.client("s3")

app = FastAPI(title="SkillGap Analyzer")

# Serve /static/* (CSS, JS, images) directly from the static/ folder
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Load HTML pages from templates/ instead of building them as Python strings
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Serves the upload form."""
    return templates.TemplateResponse(request, "index.html")


@app.post("/analyze", response_class=HTMLResponse)
def analyze(request: Request, cv_file: UploadFile = File(...), job_description: str = Form(...)):
    """
    Saves the uploaded CV PDF, runs the crew with the CV path and pasted
    job description as inputs, and renders the resulting roadmap.

    Note: this is a plain `def` (not `async def`) on purpose -- FastAPI runs
    sync routes in a worker thread, which avoids the "already running event
    loop" conflict with CrewAI's own internal event loop.
    """
    file_id = uuid.uuid4().hex
    saved_name = f"{file_id}_{cv_file.filename}"

    with tempfile.TemporaryDirectory() as tmp_dir:
        local_cv_path = Path(tmp_dir) / saved_name
        with local_cv_path.open("wb") as f:
            shutil.copyfileobj(cv_file.file, f)

        crew, defaults = load_crew(CREW_FILE)
        result = crew.kickoff(inputs={
            **defaults,
            "cv_pdf_path": str(local_cv_path),
            "job_description": job_description,
        })


    s3_output_key = f"output/{file_id}_roadmap.txt"
    output_body = f"JOB DESCRIPTION:\n{job_description}\n\n{'='*60}\n\nROADMAP:\n{result.raw}"
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=s3_output_key,
        Body=output_body.encode("utf-8"),
    )

    return templates.TemplateResponse(request,"result.html",{"roadmap": result.raw},)