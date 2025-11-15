# fastapi_app.py
import os
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

# import your pipeline runner
from summarizer import summarize_json_input

app = FastAPI(
    title="JSON Summarizer API",
    description="Submit data in JSON format and get a summarized PDF.",
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

class Metadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    source: Optional[str] = None

class JSONInput(BaseModel):
    content: str
    metadata: Optional[Metadata] = None

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "✅ FastAPI JSON Summarizer is running!",
        "usage": {
            "endpoint": "/summarize",
            "method": "POST",
            "format": {
                "content": "Your text content (required)",
                "metadata": {
                    "title": "Optional title",
                    "author": "Optional author",
                    "source": "Optional source"
                }
            }
        }
    }

@app.post("/summarize")
async def summarize_json(input_data: JSONInput):
    """
    Submit JSON data and receive a summarized PDF in return.
    
    Expected JSON format:
    {
        "content": "Your text content to summarize",
        "metadata": {
            "title": "Optional document title",
            "author": "Optional author name",
            "source": "Optional source file name"
        }
    }
    """
    if not input_data.content.strip():
        raise HTTPException(status_code=400, detail="Content field cannot be empty.")
    
    tmp_output_path = None
    
    try:
        # Define output file path
        tmp_output_path = os.path.join(tempfile.gettempdir(), "summary_output.pdf")
        
        # Convert Pydantic model to dict
        json_dict = {"content": input_data.content}
        if input_data.metadata:
            json_dict["metadata"] = input_data.metadata.dict(exclude_none=True)
        
        # Run your summarization pipeline
        # summarize_json_input() returns (pdf_path, text_preview)
        pdf_path, _ = summarize_json_input(json_dict, tmp_output_path)
        
        # Return summarized file
        return FileResponse(
            path=pdf_path,
            filename="json_summary.pdf",
            media_type="application/pdf",
            background=None  # Don't delete immediately
        )
    
    except Exception as e:
        # Clean up on error
        if tmp_output_path and os.path.exists(tmp_output_path):
            os.remove(tmp_output_path)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "service": "Text Summarizer API",
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
            if filename.endswith("_summary.pdf") or filename == "summary_output.pdf":
                filepath = os.path.join(temp_dir, filename)
                try:
                    os.remove(filepath)
                    cleaned += 1
                except:
                    pass
        return {"message": f"Cleaned up {cleaned} temporary files"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")