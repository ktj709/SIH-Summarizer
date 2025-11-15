# interface.py
import streamlit as st
import tempfile
import os
import json

from summarizer import summarize_json_input
from main import write_formatted_summary_pdf

st.set_page_config(page_title="JSON Summarizer", layout="wide")

st.title("📊 JSON Data Summarizer")
st.markdown("Enter your data in JSON format and get a summarized report in PDF format.")

# Add example JSON format
with st.expander("ℹ️ JSON Format Example"):
    st.code('''{
  "content": "Your text content to summarize...",
  "metadata": {
    "title": "Optional title",
    "author": "Optional author",
    "source": "Optional source"
  }
}''', language="json")
    st.markdown("**Note:** Only the `content` field is required. Metadata fields are optional.")

# JSON input area
input_json = st.text_area(
    "Enter your JSON data:",
    height=300,
    placeholder='{ "content": "Your text here...", "metadata": { "title": "Document Title" } }'
)

if input_json.strip():
    # Validate JSON
    try:
        json_data = json.loads(input_json)
        
        # Check if content field exists
        if "content" not in json_data:
            st.error("❌ JSON must contain a 'content' field!")
        elif not json_data["content"].strip():
            st.error("❌ The 'content' field cannot be empty!")
        else:
            st.success("✅ Valid JSON entered successfully!")
            
            # Run summarization
            if st.button("Summarize JSON Data", type="primary"):
                with st.spinner("Summarizing with Gemini... this may take a minute ⏳"):
                    output_pdf_path = os.path.join(tempfile.gettempdir(), "summarized_report.pdf")
                    
                    # Generate summary and formatted PDF
                    pdf_path, text_preview = summarize_json_input(json_data, output_pdf_path)

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
    
    except json.JSONDecodeError as e:
        st.error(f"❌ Invalid JSON format: {str(e)}")
        st.info("Please check your JSON syntax and try again.")