# Cloudinary Integration Guide

## Overview
The API now uploads generated PDF summaries to Cloudinary and returns the public URL instead of downloading the file directly.

## Setup

1. **Environment Variables** (already configured in `.env`):
```env
CLOUDINARY_CLOUD_NAME=dm6cpqvty
CLOUDINARY_API_KEY=843722665331658
CLOUDINARY_API_SECRET=gAUhq1it0dYwOOCJBl9Y05cF60A
GEMINI_API_KEY=AIzaSyAsqlZ8MhhKkQfLExzBL0CK8NiLiQJJeoI
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

## API Usage

### Endpoint: POST `/summarize`

**Request Body**:
```json
{
  "content": "Your text content to summarize (required)",
  "metadata": {
    "title": "Optional document title",
    "author": "Optional author name",
    "source": "Optional source file name"
  }
}
```

**Response**:
```json
{
  "success": true,
  "cloudinary_url": "https://res.cloudinary.com/dm6cpqvty/raw/upload/v1234567890/summaries/summary_output.pdf",
  "public_id": "summaries/summary_output",
  "format": "pdf",
  "bytes": 45678,
  "message": "PDF successfully uploaded to Cloudinary"
}
```

## Example Usage

### Using Python (requests):
```python
import requests

data = {
    "content": "Your text to summarize...",
    "metadata": {
        "title": "My Document",
        "author": "John Doe"
    }
}

response = requests.post("http://localhost:8000/summarize", json=data)
result = response.json()
print(f"PDF URL: {result['cloudinary_url']}")
```

### Using cURL:
```bash
curl -X POST "http://localhost:8000/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your text to summarize...",
    "metadata": {
      "title": "My Document"
    }
  }'
```

### Using JavaScript (fetch):
```javascript
const data = {
  content: "Your text to summarize...",
  metadata: {
    title: "My Document",
    author: "Jane Doe"
  }
};

fetch('http://localhost:8000/summarize', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(data)
})
.then(response => response.json())
.then(result => {
  console.log('PDF URL:', result.cloudinary_url);
});
```

## Running the API

```bash
# Start the FastAPI server
uvicorn fastapi_app:app --reload

# The API will be available at:
# http://localhost:8000

# View API documentation at:
# http://localhost:8000/docs
```

## Cloudinary URL Format

The generated PDF will be uploaded to:
```
https://res.cloudinary.com/dm6cpqvty/raw/upload/v[timestamp]/summaries/summary_[filename].pdf
```

You can access this URL directly in a browser to view/download the PDF.

## Features

- ✅ Automatic PDF upload to Cloudinary
- ✅ Secure HTTPS URLs
- ✅ Permanent storage (unless manually deleted)
- ✅ Direct browser access to PDFs
- ✅ Organized in `summaries/` folder
- ✅ Automatic cleanup of temporary local files

## Notes

- PDFs are stored in the `summaries/` folder in your Cloudinary account
- The `.env` file is gitignored to protect your API keys
- Temporary local files are automatically cleaned up after upload
