from fastapi import APIRouter, File, UploadFile, HTTPException
import os
import shutil
import uuid
from services.pdf_service import PDFAnalysisService

router = APIRouter(prefix="/pdf", tags=["pdf-analysis"])

# Directory for processing
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, "uploads", "temp_analysis")
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

@router.post("/analyze")
async def analyze_pdf(file: UploadFile = File(...)):
    """
    Non-AI PDF analysis endpoint.
    Extracts booking details using deterministic rules and pdfplumber.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for this analysis pipeline.")

    # 1. Upload/Save temporary file
    file_ext = os.path.splitext(file.filename)[1].lower()
    temp_filename = f"{uuid.uuid4()}{file_ext}"
    temp_path = os.path.join(TEMP_DIR, temp_filename)

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Process using PDFAnalysisService
        pdf_service = PDFAnalysisService()
        result = pdf_service.analyze_pdf(temp_path)
        
        # Add metadata
        result["filename"] = file.filename
        
        return result

    except Exception as e:
        print(f"PDF Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/detect-type")
async def detect_pdf_type(file: UploadFile = File(...)):
    """
    Detects if the PDF is digital (extractable text) or scanned (image-only).
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_path = os.path.join(TEMP_DIR, f"type_detect_{uuid.uuid4()}.pdf")
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        pdf_service = PDFAnalysisService()
        is_scanned = pdf_service.is_scanned_pdf(temp_path)
        
        return {
            "filename": file.filename,
            "type": "scanned" if is_scanned else "digital",
            "extraction_accuracy_expected": "60-80% (low)" if is_scanned else "95-99% (high)"
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
