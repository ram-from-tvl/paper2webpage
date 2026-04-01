import fitz
import requests
import json
import base64

def create_dummy_pdf(filename="dummy.pdf"):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This is a dummy research paper.", fontsize=12)
    page.insert_link({"kind": fitz.LINK_URI, "from": fitz.Rect(50, 50, 200, 70), "uri": "https://github.com/dummy/repo"})
    # Not adding an image to keep it simple, but we can add a simple rect as image if possible.
    doc.save(filename)
    doc.close()
    return filename

def test_process_pdf():
    pdf_file = create_dummy_pdf()
    print("Testing /api/process-pdf...")
    with open(pdf_file, "rb") as f:
        files = {"file": ("dummy.pdf", f, "application/pdf")}
        r = requests.post("http://localhost:8000/api/process-pdf", files=files)
    
    if r.status_code != 200:
        print(f"Error process-pdf: {r.text}")
        return None
    data = r.json()
    print(f"Successfully extracted: {len(data['images'])} images, {len(data['links'])} links. Text length: {len(data['text'])}")
    print(f"Links found: {data['links']}")
    return data

def test_generate_webpage(data):
    if not data:
        return
    print("Testing /api/generate-webpage...")
    payload = {
        "text": data["text"],
        "links": data["links"],
        "image_filenames": [img["filename"] for img in data["images"]]
    }
    r = requests.post("http://localhost:8000/api/generate-webpage", json=payload)
    if r.status_code != 200:
        print(f"Error generate-webpage: {r.text}")
        return
    
    response_data = r.json()
    html = response_data.get("html", "")
    print(f"Successfully generated HTML. Length: {len(html)} bytes")
    print("First 100 bytes of HTML:")
    print(html[:100])

if __name__ == "__main__":
    data = test_process_pdf()
    test_generate_webpage(data)
