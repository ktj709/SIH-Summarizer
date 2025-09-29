# interface.py
import streamlit as st
import tempfile
import os

from main import run  # use the full pipeline

st.set_page_config(page_title="PDF Summarizer", layout="wide")

st.title("📄 Multi-Modal PDF Summarizer")
st.markdown("Upload a PDF (with text, diagrams, and graphs) and get a summarized report.")

# File uploader
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file is not None:
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        input_path = tmp.name

    st.success("✅ PDF uploaded successfully!")
    
    # Run summarization
    if st.button("Summarize PDF", type="primary"):
        with st.spinner("Summarizing with Gemini... this may take a minute ⏳"):
            output_pdf_path = os.path.join(tempfile.gettempdir(), "summarized_report.pdf")
            
            # Generate formatted PDF and get text for preview
            pdf_path, text_preview = run(input_path, output_pdf_path)

        st.success("🎉 Summarization complete!")
        
        # Single download button for formatted PDF report
        st.download_button(
            label="📄 Download Summary Report (PDF)",
            data=open(pdf_path, "rb").read(),
            file_name="summarized_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        # Preview section
        st.markdown("---")
        st.subheader("📋 Preview")
        
        # Show first 2000 characters
        preview = text_preview[:2000]
        if len(text_preview) > 2000:
            preview += "\n\n... (truncated, download PDF report to see complete summary)"
        st.text_area("Summary Preview", preview, height=400)