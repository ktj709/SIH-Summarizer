# fastapi_app.py
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# import your pipeline runner
from main import run  

app = FastAPI(
    title="PDF Summarizer API",
    description="Upload a PDF and get a summarized version.",
    version="1.0.0"
)

# Add CORS middleware (optional, useful if you have a frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "✅ FastAPI PDF Summarizer is running!"}

@app.post("/summarize")
async def summarize_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and receive a summarized PDF in return.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    tmp_input_path = None
    tmp_output_path = None
    
    try:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
            tmp_input.write(await file.read())
            tmp_input_path = tmp_input.name
        
        # Define output file path
        tmp_output_path = tmp_input_path.replace(".pdf", "_summary.pdf")
        
        # Run your summarization pipeline
        # run() now returns (pdf_path, text_preview)
        pdf_path, _ = run(tmp_input_path, tmp_output_path)
        
        # Return summarized file
        return FileResponse(
            path=pdf_path,
            filename=f"summary_{file.filename}",
            media_type="application/pdf",
            background=None  # Don't delete immediately
        )
    
    except Exception as e:
        # Clean up on error
        if tmp_input_path and os.path.exists(tmp_input_path):
            os.remove(tmp_input_path)
        if tmp_output_path and os.path.exists(tmp_output_path):
            os.remove(tmp_output_path)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "service": "PDF Summarizer API",
        "version": "1.0.0"
    }

# Optional: Add cleanup endpoint for maintenance
@app.post("/cleanup")
async def cleanup_temp_files():
    """
    Clean up temporary files (admin endpoint).
    In production, you might want to add authentication here.
    """
    temp_dir = tempfile.gettempdir()
    cleaned = 0
    try:
        for filename in os.listdir(temp_dir):
            if filename.endswith("_summary.pdf") or (filename.startswith("tmp") and filename.endswith(".pdf")):
                filepath = os.path.join(temp_dir, filename)
                try:
                    os.remove(filepath)
                    cleaned += 1
                except:
                    pass
        return {"message": f"Cleaned up {cleaned} temporary files"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
