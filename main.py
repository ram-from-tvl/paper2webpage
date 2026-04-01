import os
import io
import zipfile
import base64
import tempfile
import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
from github import Github
from google import genai
from pydantic import BaseModel

app = FastAPI()

# Initialize Gemini Client
def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not found in environment")
    return genai.Client(api_key=api_key)

class GitHubPushRequest(BaseModel):
    github_token: str
    html_content: str
    repo_name: str
    image_data: List[dict]  # List of {"filename": str, "content": base64_str}

@app.post("/api/process-pdf")
async def process_pdf(file: UploadFile = File(...)):
    try:
        pdf_content = await file.read()
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        
        full_text = ""
        links = []
        images = []
        
        # Temporary directory for images
        temp_dir = tempfile.mkdtemp()
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            full_text += page.get_text()
            
            # Extract links
            page_links = page.get_links()
            for link in page_links:
                if "uri" in link:
                    uri = link["uri"]
                    # Filter for crucial links
                    if any(domain in uri.lower() for domain in ["github.com", "huggingface.co", "arxiv.org", "zenodo.org"]):
                        links.append(uri)
            
            # Extract images
            image_list = page.get_images(full_res=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                filename = f"image_{page_num}_{img_index}.{image_ext}"
                
                # Store in memory as base64 for the response
                images.append({
                    "filename": filename,
                    "content": base64.b64encode(image_bytes).decode("utf-8")
                })

        doc.close()
        
        return {
            "text": full_text[:10000],  # Truncate for prompt if too long
            "links": list(set(links)),
            "images": images
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-webpage")
async def generate_webpage(data: dict):
    try:
        text = data.get("text")
        links = data.get("links")
        image_filenames = data.get("image_filenames")
        
        client = get_gemini_client()
        
        prompt = f"""
        You are an expert web developer and designer. I am providing you with the text, important URLs, and extracted image filenames from a research paper. 
        Your job is to generate a single, beautiful index.html file using Tailwind CSS via CDN. 
        This page will act as the project's official landing page. 
        It must include: 
        1. A hero section with the paper title and authors.
        2. An 'About the Project' summary.
        3. A section highlighting the crucial links (Code, Datasets) with nice buttons.
        4. Placeholders for the images using the exact filenames provided: {', '.join(image_filenames)}.
        
        Research Paper Text Snippet:
        {text[:5000]}
        
        Crucial Links:
        {', '.join(links)}
        
        Output ONLY the raw HTML code, nothing else. Do not include markdown code blocks.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview",
            contents=prompt
        )
        
        html_content = response.text.strip()
        # Clean up if Gemini wrapped it in markdown
        if html_content.startswith("```html"):
            html_content = html_content[7:]
        if html_content.endswith("```"):
            html_content = html_content[:-3]
            
        return {"html": html_content.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/github-deploy")
async def github_deploy(request: GitHubPushRequest):
    try:
        g = Github(request.github_token)
        user = g.get_user()
        
        # Create repo
        repo = user.create_repo(request.repo_name, private=False, auto_init=True)
        
        # Create index.html
        repo.create_file("index.html", "Initial landing page", request.html_content)
        
        # Upload images
        for img in request.image_data:
            image_bytes = base64.b64decode(img["content"])
            repo.create_file(f"images/{img['filename']}", f"Upload {img['filename']}", image_bytes)
            
        return {"repo_url": repo.html_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
