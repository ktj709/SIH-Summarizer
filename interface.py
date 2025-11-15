# interface.py
import streamlit as st
import tempfile
import os
import json
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from summarizer import summarize_json_input

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

st.set_page_config(page_title="JSON Summarizer", layout="wide")

st.title("📊 JSON Data Summarizer")
st.markdown("Enter your data in JSON format and get a summarized PDF report uploaded to Cloudinary.")

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
                
                # Upload to Cloudinary
                with st.spinner("Uploading PDF to Cloudinary... ☁️"):
                    try:
                        upload_result = cloudinary.uploader.upload(
                            pdf_path,
                            resource_type="raw",
                            folder="summaries",
                            public_id=f"summary_{os.path.basename(pdf_path).replace('.pdf', '')}"
                        )
                        
                        cloudinary_url = upload_result["secure_url"]
                        
                        # Clean up temporary file
                        if os.path.exists(output_pdf_path):
                            os.remove(output_pdf_path)
                        
                        st.success("✅ PDF uploaded to Cloudinary successfully!")
                        
                        # Display Cloudinary URL
                        st.markdown("---")
                        st.subheader("📄 Your PDF Summary")
                        st.info("Your PDF has been uploaded to Cloudinary. Use the link below to access it:")
                        
                        # Display clickable link
                        st.markdown(f"**🔗 Cloudinary URL:**")
                        st.code(cloudinary_url, language="text")
                        st.markdown(f"[Click here to open PDF]({cloudinary_url})")
                        
                        # Display additional info
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("File Size", f"{upload_result.get('bytes', 0) / 1024:.2f} KB")
                        with col2:
                            st.metric("Format", upload_result.get('format', 'PDF').upper())
                        
                    except Exception as e:
                        st.error(f"❌ Failed to upload to Cloudinary: {str(e)}")
                
                # Preview section
                st.markdown("---")
                st.subheader("📋 Preview")
                
                # Show first 2000 characters
                preview = text_preview[:2000]
                if len(text_preview) > 2000:
                    preview += "\n\n... (truncated, see full summary in the PDF)"
                st.text_area("Summary Preview", preview, height=400)
    
    except json.JSONDecodeError as e:
        st.error(f"❌ Invalid JSON format: {str(e)}")
        st.info("Please check your JSON syntax and try again.")