

import base64
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from huggingface_hub import InferenceClient
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GitHub Configuration
GITHUB_USERNAME = "TkWarrior"
GITHUB_REPO = "Plant_images"
GITHUB_BRANCH = "main"
GITHUB_ACCESS_TOKEN = "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"
IMAGE_FOLDER = "images"

# Hugging Face Configuration
client = InferenceClient(
    provider="hf-inference",
    api_key="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"
)

# Helper function to upload image to GitHub
def upload_image_to_github(file_content: bytes, filename: str) -> str:
    try:
        encoded_content = base64.b64encode(file_content).decode("utf-8")
        file_path = f"{IMAGE_FOLDER}/{filename}"
        url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{file_path}"

        payload = {
            "message": f"Upload {filename}",
            "content": encoded_content,
            "branch": GITHUB_BRANCH,
        }

        headers = {
            "Authorization": f"token {GITHUB_ACCESS_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = requests.put(url, json=payload, headers=headers)
        response.raise_for_status()

        # Return the raw GitHub URL
        return f"https://github.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{file_path}"

    except requests.exceptions.RequestException as e:
        print(f"GitHub Request Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload image to GitHub")
    except Exception as e:
        print(f"GitHub Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Image upload failed")

# FastAPI endpoint to analyze image
@app.post("/analyze-image/")
async def analyze_image(file: UploadFile = File(...)):
   
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail="Invalid file type. Only images are allowed."
            )

        # Read and upload image to GitHub
        image_bytes = await file.read()
        public_url = upload_image_to_github(image_bytes, file.filename)
        print(public_url)
        # Hugging Face inference payload
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe the image in one sentence"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": public_url
                        }
                    }
                ]
            }
        ]

        # Make the Hugging Face API call
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.2-11B-Vision-Instruct",
            messages=messages,
            max_tokens=500,
        )

        # Extract response
        response_message = completion.choices[0].message["content"]
        print(type(response_message))
        return {"description": "response_message"}

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        error_detail = f"Unexpected error: {str(e)}"
        print(error_detail)
        return JSONResponse(status_code=500, content={"detail": error_detail})

# Health check endpoint
@app.get("/")
async def health_check():
    return {"status": "Server is running"}