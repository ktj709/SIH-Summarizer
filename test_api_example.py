"""
Example script to test the JSON Summarizer API with Cloudinary upload
"""
import requests
import json

# API endpoint
API_URL = "http://localhost:8000/summarize"

# Sample JSON data
data = {
    "content": """
    This is a sample text that needs to be summarized. 
    You can include any amount of text here, and the API will process it,
    generate a summary using Gemini AI, create a formatted PDF report,
    and upload it to Cloudinary.
    
    The response will contain the Cloudinary URL where you can access
    the generated PDF summary.
    """,
    "metadata": {
        "title": "Sample Document",
        "author": "Test User",
        "source": "test_document.txt"
    }
}

# Make POST request
print("Sending request to API...")
response = requests.post(API_URL, json=data)

# Check response
if response.status_code == 200:
    result = response.json()
    print("\n✅ Success!")
    print(f"Cloudinary URL: {result['cloudinary_url']}")
    print(f"Public ID: {result['public_id']}")
    print(f"File Size: {result['bytes']} bytes")
    print(f"Message: {result['message']}")
    print(f"\n📄 Access your PDF here: {result['cloudinary_url']}")
else:
    print(f"\n❌ Error: {response.status_code}")
    print(response.json())
