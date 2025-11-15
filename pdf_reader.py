# pdf_reader.py
import fitz  # PyMuPDF
from pdf2image import convert_from_bytes
import io
from PIL import Image
import os
from typing import List, Tuple

def extract_pages_text_and_images(pdf_path: str, ocr_on_fail: bool = True) -> List[dict]:
    """
    Returns a list, one entry per page:
    {
      "page_no": int,
      "text": str,           # text extracted (may be empty)
      "images": [PIL.Image], # images extracted from page as PIL images
      "was_scanned": bool    # True if we had to use OCR
    }
    """
    doc = fitz.open(pdf_path)
    results = []
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text").strip()
        images = []

        # Extract embedded images from the page
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            images.append(pil)

        was_scanned = False
        if (not text or len(text) < 30) and ocr_on_fail:
            # Fallback: render page to image and run OCR externally (we only convert here)
            was_scanned = True
            pil_page = page.get_pixmap(dpi=200).pil_tobytes(format="png")
            pil_image = Image.open(io.BytesIO(pil_page)).convert("RGB")
            images.insert(0, pil_image)  # page image for OCR/graph analysis
            # do not run OCR here; leave to OCR module to decide

        results.append({
            "page_no": i+1,
            "text": text,
            "images": images,
            "was_scanned": was_scanned
        })
    doc.close()
    return results