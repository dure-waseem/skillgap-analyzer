# """
# FastAPI app for SkillGap Analyzer.

# Place this file at the ROOT of your project, alongside crew.jsonc, agents/, tools/.

# Run with:
#     uv add fastapi "uvicorn[standard]" python-multipart
#     uv run uvicorn main:app --reload --port 8000

# Then open http://127.0.0.1:8000 in your browser.
# """

# import shutil
# import uuid
# from pathlib import Path

# from fastapi import FastAPI, File, UploadFile, Form
# from fastapi.responses import HTMLResponse
# from crewai.project import load_crew

# BASE_DIR = Path(__file__).parent
# CREW_FILE = BASE_DIR / "crew.jsonc"
# UPLOAD_DIR = BASE_DIR / "uploads"
# UPLOAD_DIR.mkdir(exist_ok=True)

# app = FastAPI(title="SkillGap Analyzer")


# @app.get("/", response_class=HTMLResponse)
# async def home():
#     """Serves the upload form: CV PDF + pasted Job Description."""
#     return """
#     <html>
#     <head>
#       <title>SkillGap Analyzer</title>
#       <style>
#         body { font-family: sans-serif; max-width: 600px; margin: 60px auto; }
#         textarea { width: 100%; padding: 8px; }
#         input[type=file] { margin: 10px 0; }
#         button {
#           background: #222; color: white; border: none;
#           padding: 10px 24px; border-radius: 6px; cursor: pointer;
#         }
#       </style>
#     </head>
#     <body>
#       <h2>SkillGap Analyzer</h2>
#       <p>Upload your CV and paste the job description to get a personalized learning roadmap.</p>
#       <form action="/analyze" method="post" enctype="multipart/form-data">
#         <label><b>CV (PDF):</b></label><br>
#         <input type="file" name="cv_file" accept="application/pdf" required><br>

#         <label><b>Job Description:</b></label><br>
#         <textarea name="job_description" rows="12" required placeholder="Paste the job description here..."></textarea><br><br>

#         <button type="submit">Analyze</button>
#       </form>
#     </body>
#     </html>
#     """


# @app.post("/analyze", response_class=HTMLResponse)
# def analyze(cv_file: UploadFile = File(...), job_description: str = Form(...)):
#     """
#     Saves the uploaded CV PDF, then runs the crew with the CV path and
#     pasted job description as inputs, and returns the resulting roadmap.
#     """
#     # Save the uploaded PDF with a unique name so concurrent uploads don't collide
#     saved_name = f"{uuid.uuid4().hex}_{cv_file.filename}"
#     saved_path = UPLOAD_DIR / saved_name
#     with saved_path.open("wb") as f:
#         shutil.copyfileobj(cv_file.file, f)

#     # Load the JSONC-defined crew and run it with our inputs
#     crew, defaults = load_crew(CREW_FILE)
#     result = crew.kickoff(inputs={
#         **defaults,
#         "cv_pdf_path": str(saved_path),
#         "job_description": job_description,
#     })

#     return f"""
#     <html>
#     <head><title>Your Learning Roadmap</title></head>
#     <body style="font-family: sans-serif; max-width: 700px; margin: 60px auto;">
#       <h2>Your Learning Roadmap</h2>
#       <pre style="white-space: pre-wrap; background:#f5f5f5; padding:16px; border-radius:8px;">{result.raw}</pre>
#       <br>
#       <a href="/">← Analyze another CV</a>
#     </body>
#     </html>
#     """


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

    Note: this is a plain `def` (not `async def`) on purpose -- FastAPI runs
    sync routes in a worker thread, which avoids the "already running event
    loop" conflict with CrewAI's own internal event loop.
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