<div align="center">
  <h1>📄 Research Paper Landing Page Generator</h1>
  <p>Transform your research paper PDF into a stunning project landing page and deploy it directly to GitHub.</p>
</div>

## Architecture Overview
This application is an end-to-end Proof of Concept (POC) consisting of:
- **Backend (FastAPI)**: Handles the heavy lifting — extracting text/URLs/images from PDFs via `PyMuPDF`, generating beautiful Tailwind CSS HTML code utilizing Google's `gemini-2.5-flash` model, and integrating with `PyGithub` to push straight to a GitHub repository.
- **Frontend (Streamlit)**: A sleek and modular UI that allows the user to upload their research paper PDF, configure their GitHub deployment token, and monitor the process dynamically via progress boxes.

## Prerequisites
- Python 3.10+
- A valid **Gemini API Key** 
- A **GitHub Personal Access Token (PAT)** with repository creation permissions (inserted through the Streamlit UI).

---

## 🚀 How to Run Locally

### 1. Environment Setup
First, create a virtual environment to isolate the project dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
Install all required Python packages (FastAPI, Streamlit, PyMuPDF, google-genai, etc.):
```bash
pip install -r requirements.txt
```

### 3. API Key Configuration
Create a `.env` file in the root directory (you can copy `.env.example`).
```bash
GEMINI_API_KEY="your-gemini-api-key-here"
```
*(Note: As an alternative during local testing, the `main.py` is configured with a fallback free-tier API key if the `.env` var is not successfully configured.)*

### 4. Start the Application
You need to run both the FastAPI server AND the Streamlit frontend. The easiest way to boot both is to run the start script provided:

```bash
bash start.sh
```

**Alternatively, you can run them manually in separate terminals:**
**Terminal 1 (Backend):**
```bash
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
source venv/bin/activate
streamlit run app.py --server.port 3000 --server.address 0.0.0.0
```

### 5. Open Your Browser
If using the manual mode or the `start.sh` script, your Streamlit app should soon automatically pop open in your browser natively.
Otherwise, navigate to: **[http://localhost:3000](http://localhost:3000)**

---

## Output Fallback
If the GitHub deployment step throws a permission error (e.g., token expires or invalid scopes), the Streamlit UI safely traps the error and generates a `.zip` file out of your parsed images and the new Gemini HTML code. You can download this file locally via a fallback download button!
