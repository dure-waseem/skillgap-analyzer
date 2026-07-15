from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import pdfplumber


class PDFReaderInput(BaseModel):
    pdf_path: str = Field(..., description="Path to the CV PDF file to read.")


class PDFReaderTool(BaseTool):
    name: str = "PDF Reader Tool"
    description: str = (
        "Reads a PDF file from disk and returns its full text content. "
        "Use this to extract a candidate's CV text from a PDF file."
    )
    args_schema: Type[BaseModel] = PDFReaderInput

    def _run(self, pdf_path: str) -> str:
        parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    parts.append(t)
        text = "\n".join(parts).strip()
        return text or f"No extractable text found in {pdf_path}."