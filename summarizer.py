# summarizer.py
import io
import textwrap
from gemini_client import GeminiClient
from image_ocr import extract_image_metadata
from tqdm import tqdm
from datetime import datetime

# Initialize Gemini client once
client = GeminiClient()

def chunk_text(text: str, max_chars: int = 35000):
    """Naive chunker by chars; tune for model context size."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start+max_chars]
        # try to break at last newline or sentence end
        last_break = max(chunk.rfind("\n"), chunk.rfind("."))
        if last_break > int(0.5*max_chars):
            chunk = text[start:start+last_break+1]
            start = start + last_break + 1
        else:
            start += max_chars
        chunks.append(chunk)
    return chunks

def format_paragraph(text: str, width: int = 100, indent: int = 0) -> str:
    """
    Format a paragraph with proper word wrapping and indentation.
    Uses textwrap for proper word boundaries.
    """
    if not text.strip():
        return ""
    
    indent_str = ' ' * indent
    # Use textwrap for proper word wrapping
    wrapped = textwrap.fill(
        text.strip(),
        width=width,
        initial_indent=indent_str,
        subsequent_indent=indent_str,
        break_long_words=False,
        break_on_hyphens=False
    )
    return wrapped

def format_text_with_paragraphs(text: str, width: int = 100, indent: int = 0) -> str:
    """
    Format text preserving paragraph breaks with proper word wrapping.
    """
    if not text.strip():
        return ""
    
    # Split by double newlines (paragraph breaks) or single newlines
    paragraphs = text.split('\n')
    formatted_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        formatted = format_paragraph(para, width=width, indent=indent)
        if formatted:
            formatted_paragraphs.append(formatted)
    
    # Join with double newlines for paragraph separation
    return '\n\n'.join(formatted_paragraphs)

def create_formatted_report(summaries: list, source_file: str = "document.pdf") -> str:
    """
    Create a professionally formatted report from page summaries.
    """
    lines = []
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    separator = "=" * 100
    subseparator = "-" * 100
    
    # HEADER SECTION
    lines.append(separator)
    lines.append("PDF SUMMARY REPORT".center(100))
    lines.append(separator)
    lines.append(f"Source File: {source_file}")
    lines.append(f"Generated: {timestamp}")
    lines.append(f"Total Pages: {len(summaries)}")
    lines.append(separator)
    lines.append("")
    lines.append("")
    
    # TABLE OF CONTENTS
    lines.append("TABLE OF CONTENTS")
    lines.append(subseparator)
    lines.append("")
    
    for summary in summaries:
        page_no = summary['page_no']
        short = summary['combined_short']
        
        # Truncate and add ellipsis if too long
        if len(short) > 85:
            short = short[:82] + "..."
        
        lines.append(f"Page {page_no:3d}: {short}")
    
    lines.append("")
    lines.append(separator)
    lines.append("")
    lines.append("")
    
    # DETAILED PAGE SUMMARIES
    for summary in summaries:
        page_no = summary['page_no']
        
        # Page header
        lines.append("")
        lines.append(separator)
        lines.append(f"PAGE {page_no}".center(100))
        lines.append(separator)
        lines.append("")
        
        # TEXT CONTENT
        if summary['text_summary']:
            lines.append("TEXT CONTENT:")
            lines.append(subseparator)
            lines.append("")
            
            formatted_text = format_text_with_paragraphs(summary['text_summary'], width=100)
            lines.append(formatted_text)
            lines.append("")
            lines.append("")
        
        # IMAGE ANALYSIS
        if summary['image_summaries']:
            lines.append("IMAGE ANALYSIS:")
            lines.append(subseparator)
            lines.append("")
            
            for idx, img_data in enumerate(summary['image_summaries'], 1):
                lines.append(f"Image {idx}:")
                lines.append("")
                
                # Image metadata
                meta = img_data['meta']
                width = meta.get('width', 'N/A')
                height = meta.get('height', 'N/A')
                img_format = meta.get('format', 'N/A')
                mode = meta.get('mode', 'N/A')
                
                lines.append(f"  Dimensions: {width} x {height} pixels")
                lines.append(f"  Format: {img_format}")
                lines.append(f"  Mode: {mode}")
                lines.append("")
                lines.append("  Description:")
                lines.append("")
                
                # Format image description with indentation
                desc = img_data['desc']
                formatted_desc = format_text_with_paragraphs(desc, width=96, indent=4)
                lines.append(formatted_desc)
                lines.append("")
                lines.append("")
        
        lines.append("")
    
    # FOOTER
    lines.append(separator)
    lines.append("END OF REPORT".center(100))
    lines.append(separator)
    
    return '\n'.join(lines)

def summarize_pdf_pages(page_records: list, model="gemini-1.5-flash", 
                        create_report: bool = False, source_file: str = "document.pdf"):
    """
    Summarize PDF pages with optional formatted text report.
    
    Args:
        page_records: output of extract_pages_text_and_images()
        model: Gemini model to use
        create_report: if True, returns (summaries, formatted_report_text)
        source_file: source filename for report header
    
    Returns:
        list of dicts: [{'page_no', 'text_summary', 'image_summaries', 'combined_short'}]
        or tuple: (summaries_list, formatted_report_text) if create_report=True
    """
    outputs = []
    
    for rec in tqdm(page_records, desc="Summarizing pages"):
        page_no = rec["page_no"]
        text = rec["text"]

        # Summarize text — chunk if necessary
        text_summary = ""
        if text.strip():
            chunks = chunk_text(text)
            chunk_summaries = []
            for c in chunks:
                s = client.summarize_text(c)
                chunk_summaries.append(s.strip())
            text_summary = "\n\n".join(chunk_summaries)  # Double newline between chunks
        else:
            text_summary = ""

        # Summarize images
        image_summaries = []
        for img in rec["images"]:
            meta = extract_image_metadata(img)
            # Convert PIL image → bytes for Gemini
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            desc = client.analyze_image(buf.getvalue())
            desc_lower = desc.strip().lower()
            
            # Filter out black/empty images
            black_keywords = [
                "completely black", "filled black rectangle", "solid black", "uniformly dark", 
                "entirely black", "pure black", "devoid of", "no discernible",
                "uniform expanse of darkness", "uniformly black", "solid, uniform expanse"
            ]
            
            is_black_image = any(keyword in desc_lower for keyword in black_keywords)
            
            # Only add if it's not a black/empty image
            if not is_black_image:
                image_summaries.append({"meta": meta, "desc": desc.strip()})

        # Create a short combined page summary for table of contents
        combined_short = ""
        if text_summary:
            # Get first sentence or first 100 chars
            first_line = text_summary.split('\n')[0]
            if len(first_line) > 100:
                first_line = first_line[:100]
            combined_short += first_line
        
        if image_summaries:
            img_desc = image_summaries[0]["desc"]
            if img_desc:
                first_img_line = img_desc.split('\n')[0]
                if len(first_img_line) > 50:
                    first_img_line = first_img_line[:50]
                combined_short += f" | Image: {first_img_line}"

        outputs.append({
            "page_no": page_no,
            "text_summary": text_summary,
            "image_summaries": image_summaries,
            "combined_short": combined_short
        })
    
    if create_report:
        formatted_report = create_formatted_report(outputs, source_file)
        return outputs, formatted_report
    
    return outputs

def summarize_text_input(text: str, output_pdf_path: str, model="gemini-2.0-flash"):
    """
    Summarize text input and generate a formatted PDF report.
    
    Args:
        text: Input text to summarize
        output_pdf_path: Path where the output PDF will be saved
        model: Gemini model to use
    
    Returns:
        tuple: (pdf_path, formatted_report_text)
    """
    from main import write_formatted_summary_pdf
    
    # Chunk the text if necessary
    text_summary = ""
    if text.strip():
        chunks = chunk_text(text)
        chunk_summaries = []
        for c in tqdm(chunks, desc="Summarizing text"):
            s = client.summarize_text(c)
            chunk_summaries.append(s.strip())
        text_summary = "\n\n".join(chunk_summaries)
    
    # Create a summary record (simulating page 1)
    summary_record = {
        "page_no": 1,
        "text_summary": text_summary,
        "image_summaries": [],  # No images from text input
        "combined_short": text_summary.split('\n')[0][:100] if text_summary else "Text Summary"
    }
    
    summaries = [summary_record]
    
    # Create formatted text report
    formatted_report = create_formatted_report(summaries, source_file="text_input.txt")
    
    # Generate formatted PDF report
    write_formatted_summary_pdf(summaries, output_path=output_pdf_path, source_filename="text_input.txt")
    
    return output_pdf_path, formatted_report

def summarize_json_input(json_data: dict, output_pdf_path: str, model="gemini-2.0-flash"):
    """
    Summarize JSON input data and generate a formatted PDF report.
    
    Args:
        json_data: Dictionary containing 'content' and optional 'metadata'
                  Expected format: {
                      "content": "text to summarize",
                      "metadata": {
                          "title": "optional title",
                          "author": "optional author",
                          "source": "optional source"
                      }
                  }
        output_pdf_path: Path where the output PDF will be saved
        model: Gemini model to use
    
    Returns:
        tuple: (pdf_path, formatted_report_text)
    """
    from main import write_formatted_summary_pdf
    
    # Extract content from JSON
    text = json_data.get("content", "")
    metadata = json_data.get("metadata", {})
    
    # Extract metadata fields
    source_title = metadata.get("title", "JSON Input")
    source_author = metadata.get("author", "")
    source_name = metadata.get("source", "json_data.json")
    
    # Chunk the text if necessary
    text_summary = ""
    if text.strip():
        chunks = chunk_text(text)
        chunk_summaries = []
        for c in tqdm(chunks, desc="Summarizing JSON content"):
            s = client.summarize_text(c)
            chunk_summaries.append(s.strip())
        text_summary = "\n\n".join(chunk_summaries)
    
    # Create a summary record (simulating page 1)
    summary_record = {
        "page_no": 1,
        "text_summary": text_summary,
        "image_summaries": [],  # No images from JSON input
        "combined_short": text_summary.split('\n')[0][:100] if text_summary else source_title
    }
    
    summaries = [summary_record]
    
    # Create formatted text report with metadata
    formatted_report = create_formatted_report(summaries, source_file=source_name)
    
    # Add metadata section to the report if available
    if source_author or source_title != "JSON Input":
        metadata_section = "\n\nMETADATA:\n"
        metadata_section += "-" * 100 + "\n"
        if source_title != "JSON Input":
            metadata_section += f"Title: {source_title}\n"
        if source_author:
            metadata_section += f"Author: {source_author}\n"
        metadata_section += "-" * 100 + "\n"
        # Insert metadata after header
        formatted_report = formatted_report.replace(
            "=" * 100 + "\n\n\n",
            "=" * 100 + metadata_section + "\n\n",
            1
        )
    
    # Generate formatted PDF report
    write_formatted_summary_pdf(summaries, output_path=output_pdf_path, source_filename=source_name)
    
    return output_pdf_path, formatted_report