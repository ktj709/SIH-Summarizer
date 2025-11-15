# image_ocr.py
from PIL import Image
import pytesseract
import numpy as np
import cv2

def ocr_image(pil_image: Image.Image, lang: str = "eng") -> str:
    """Return OCR text for a PIL image using pytesseract."""
    # Convert to grayscale + denoise
    img = np.array(pil_image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # simple thresholding - improves OCR on many scanned images
    _, th = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    pil_processed = Image.fromarray(th)
    text = pytesseract.image_to_string(pil_processed, lang=lang)
    return text.strip()

def is_likely_chart(pil_image: Image.Image, edge_thresh: float = 0.06) -> bool:
    """
    Heuristic: charts/plots tend to have many straight edges lines and axes.
    We compute proportion of Canny edges; if above threshold, mark as likely chart/diagram.
    """
    img = np.array(pil_image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_prop = edges.mean()
    return edge_prop > edge_thresh*255  # tuned heuristic; not perfect

def extract_image_metadata(pil_image: Image.Image) -> dict:
    """
    Returns dict with:
      - ocr_text
      - is_chart
      - size
    """
    ocr_text = ocr_image(pil_image)
    chart_flag = is_likely_chart(pil_image)
    w, h = pil_image.size
    return {"ocr_text": ocr_text, "is_chart": chart_flag, "size": (w, h)}