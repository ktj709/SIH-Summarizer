import os
from pdf_reader import extract_pages_text_and_images
from summarizer import summarize_pdf_pages
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import textwrap

def write_formatted_summary_pdf(summary_records, output_path="pdf_summary_report.pdf", source_filename="input.pdf"):
    """
    Generate a well-formatted PDF report from the summary records.
    This creates a PDF that looks like the formatted text report.
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    margin = 20*mm
    
    def draw_separator(y_pos, char="=", width_chars=100):
        """Draw a separator line"""
        separator = char * width_chars
        c.setFont("Courier", 8)
        c.drawString(margin, y_pos, separator)
        return y_pos - 12
    
    def draw_centered_text(y_pos, text, font="Helvetica-Bold", size=12):
        """Draw centered text"""
        c.setFont(font, size)
        text_width = c.stringWidth(text, font, size)
        x = (width - text_width) / 2
        c.drawString(x, y_pos, text)
        return y_pos - 15
    
    def draw_wrapped_text(y_pos, text, font="Helvetica", size=10, max_width=170*mm, indent=0):
        """Draw wrapped text and return new y position"""
        c.setFont(font, size)
        wrapper = textwrap.TextWrapper(width=95, initial_indent=' '*indent, subsequent_indent=' '*indent)
        lines = []
        for paragraph in text.split('\n'):
            if paragraph.strip():
                lines.extend(wrapper.wrap(paragraph))
            else:
                lines.append('')
        
        for line in lines:
            if y_pos < 50:
                c.showPage()
                y_pos = height - margin
            c.drawString(margin, y_pos, line)
            y_pos -= 12
        
        return y_pos
    
    # Start first page
    y = height - margin
    
    # Header
    y = draw_separator(y, "=", 100)
    y = draw_centered_text(y, "PDF SUMMARY REPORT", "Helvetica-Bold", 14)
    y = draw_separator(y, "=", 100)
    
    # Metadata
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, f"Source File: {source_filename}")
    y -= 12
    c.drawString(margin, y, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    y -= 12
    c.drawString(margin, y, f"Total Pages: {len(summary_records)}")
    y -= 12
    
    y = draw_separator(y, "=", 100)
    y -= 15
    
    # Table of Contents
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "TABLE OF CONTENTS")
    y -= 12
    y = draw_separator(y, "-", 100)
    y -= 5
    
    c.setFont("Helvetica", 9)
    for rec in summary_records:
        short_summary = rec['combined_short'][:75] + "..." if len(rec['combined_short']) > 75 else rec['combined_short']
        line = f"Page {rec['page_no']:3d}: {short_summary}"
        if y < 50:
            c.showPage()
            y = height - margin
        c.drawString(margin, y, line)
        y -= 11
    
    y -= 10
    y = draw_separator(y, "=", 100)
    
    # Detailed summaries for each page
    for rec in summary_records:
        c.showPage()
        y = height - margin
        
        y -= 10
        y = draw_separator(y, "=", 100)
        y = draw_centered_text(y, f"PAGE {rec['page_no']}", "Helvetica-Bold", 14)
        y = draw_separator(y, "=", 100)
        y -= 10
        
        # Text content section
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "TEXT CONTENT:")
        y -= 12
        y = draw_separator(y, "-", 100)
        y -= 5
        
        if rec['text_summary']:
            y = draw_wrapped_text(y, rec['text_summary'], "Helvetica", 10)
        else:
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(margin, y, "(No extractable text on this page)")
            y -= 15
        
        y -= 10
        
        # Image analysis section
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, y, "IMAGE ANALYSIS:")
        y -= 12
        y = draw_separator(y, "-", 100)
        y -= 5
        
        if rec['image_summaries']:
            for idx, imr in enumerate(rec['image_summaries'], 1):
                c.setFont("Helvetica-Bold", 10)
                c.drawString(margin, y, f"Image {idx}:")
                y -= 15
                
                # Image metadata
                c.setFont("Helvetica", 9)
                c.drawString(margin + 5, y, "Dimensions: N/A x N/A pixels")
                y -= 11
                c.drawString(margin + 5, y, "Format: N/A")
                y -= 11
                c.drawString(margin + 5, y, "Mode: N/A")
                y -= 15
                
                c.setFont("Helvetica-Bold", 9)
                c.drawString(margin + 5, y, "Description:")
                y -= 15
                
                y = draw_wrapped_text(y, imr['desc'], "Helvetica", 9, indent=4)
                y -= 15
                
                if y < 100:
                    c.showPage()
                    y = height - margin
        else:
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(margin, y, "(No images detected on this page)")
            y -= 15
        
        y -= 10
    
    # Final page with end marker
    c.showPage()
    y = height - margin
    y -= 10
    y = draw_separator(y, "=", 100)
    y = draw_centered_text(y, "END OF REPORT", "Helvetica-Bold", 14)
    y = draw_separator(y, "=", 100)
    
    c.save()

def run(pdf_path: str, out_pdf: str = "pdf_summary_report.pdf"):
    """
    Run the PDF summarization pipeline and generate a formatted PDF report.
    
    Args:
        pdf_path: Input PDF file path
        out_pdf: Output PDF report path
    
    Returns:
        str: Path to the generated PDF report
    """
    pages = extract_pages_text_and_images(pdf_path, ocr_on_fail=True)
    
    # Generate summaries with text report for preview
    summaries, formatted_report = summarize_pdf_pages(
        pages, 
        model="gemini-2.0-flash",
        create_report=True,
        source_file=pdf_path
    )
    
    # Generate formatted PDF report
    write_formatted_summary_pdf(summaries, output_path=out_pdf, source_filename=pdf_path)
    
    print("Formatted PDF summary written to:", out_pdf)
    
    # Return both paths (PDF for download, text for preview)
    return out_pdf, formatted_report

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="Path to input PDF")
    parser.add_argument("--out", default="pdf_summary_report.pdf", help="Output summary PDF")
    args = parser.parse_args()
    run(args.pdf, args.out)
