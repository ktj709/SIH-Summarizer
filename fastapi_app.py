# fastapi_app.py

import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

# import your pipeline runner
from main import run  

app = FastAPI(
    title="PDF Summarizer API",
    description="Upload a PDF and get a summarized version.",
    version="1.0.0"
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

    try:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_input:
            tmp_input.write(await file.read())
            tmp_input_path = tmp_input.name

        # Define output file path
        tmp_output_path = tmp_input_path.replace(".pdf", "_summary.pdf")

        # Run your summarization pipeline
        run(tmp_input_path, tmp_output_path)

        # Return summarized file
        return FileResponse(
            path=tmp_output_path,
            filename="summary.pdf",
            media_type="application/pdf"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    finally:
        # Clean up uploaded file
        if os.path.exists(tmp_input_path):
            os.remove(tmp_input_path)
