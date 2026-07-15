
"""
FastAPI app for SkillGap Analyzer.

"""

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from crewai.project import load_crew

BASE_DIR = Path(__file__).parent
CREW_FILE = BASE_DIR / "crew.jsonc"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

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

    """
    saved_name = f"{uuid.uuid4().hex}_{cv_file.filename}"
    saved_path = UPLOAD_DIR / saved_name
    with saved_path.open("wb") as f:
        shutil.copyfileobj(cv_file.file, f)

    crew, defaults = load_crew(CREW_FILE)
    result = crew.kickoff(inputs={
        **defaults,
        "cv_pdf_path": str(saved_path),
        "job_description": job_description,
    })

    return templates.TemplateResponse(request,"result.html",{"roadmap": result.raw},)
