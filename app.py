import streamlit as st
import requests
import base64
import io
import zipfile
import os

st.set_page_config(page_title="Research Paper Landing Page Generator", layout="wide")

st.title("📄 Research Paper Landing Page Generator")
st.markdown("""
Transform your research paper PDF into a stunning project landing page and deploy it directly to GitHub.
""")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    github_token = st.text_input("GitHub Personal Access Token", type="password", help="Required to create a repository and push files.")
    st.info("Your token is used only for this session to create the repository.")
    
    repo_name = st.text_input("Repository Name", value="research-landing-page")

# Main UI
uploaded_file = st.file_uploader("Upload Research Paper (PDF)", type="pdf")

if uploaded_file and github_token:
    if st.button("Generate & Deploy"):
        try:
            # Step 1: Extracting
            with st.status("Processing PDF...", expanded=True) as status:
                st.write("Extracting text, links, and images...")
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                response = requests.post("http://localhost:8000/api/process-pdf", files=files)
                
                if response.status_code != 200:
                    st.error(f"Error processing PDF: {response.text}")
                    st.stop()
                
                extracted_data = response.json()
                st.write(f"Found {len(extracted_data['images'])} images and {len(extracted_data['links'])} crucial links.")
                
                # Step 2: Generating Webpage
                status.update(label="Generating Webpage with Gemini...", state="running")
                st.write("Crafting a modern Tailwind CSS landing page...")
                
                gen_response = requests.post("http://localhost:8000/api/generate-webpage", json={
                    "text": extracted_data["text"],
                    "links": extracted_data["links"],
                    "image_filenames": [img["filename"] for img in extracted_data["images"]]
                })
                
                if gen_response.status_code != 200:
                    st.error(f"Error generating webpage: {gen_response.text}")
                    st.stop()
                
                html_content = gen_response.json()["html"]
                
                # Step 3: Pushing to GitHub
                status.update(label="Deploying to GitHub...", state="running")
                st.write(f"Creating repository '{repo_name}'...")
                
                deploy_response = requests.post("http://localhost:8000/api/github-deploy", json={
                    "github_token": github_token,
                    "html_content": html_content,
                    "repo_name": repo_name,
                    "image_data": extracted_data["images"]
                })
                
                if deploy_response.status_code != 200:
                    st.warning(f"GitHub deployment failed: {deploy_response.text}. You can still download the source code below.")
                    repo_url = None
                else:
                    repo_url = deploy_response.json()["repo_url"]
                
                status.update(label="Process Complete!", state="complete", expanded=False)

            # Success Message
            if repo_url:
                st.success(f"🚀 Successfully deployed! View your repository here: [{repo_url}]({repo_url})")
                st.balloons()
            
            # Fallback Download
            st.divider()
            st.subheader("Download Source Code")
            
            # Create ZIP in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                zip_file.writestr("index.html", html_content)
                for img in extracted_data["images"]:
                    img_bytes = base64.b64decode(img["content"])
                    zip_file.writestr(f"images/{img['filename']}", img_bytes)
            
            st.download_button(
                label="Download Webpage Source (.zip)",
                data=zip_buffer.getvalue(),
                file_name=f"{repo_name}.zip",
                mime="application/zip"
            )
            
            # Preview
            with st.expander("Preview Generated HTML"):
                st.code(html_content, language="html")

        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

elif not github_token and uploaded_file:
    st.warning("Please provide your GitHub Personal Access Token in the sidebar to proceed.")
elif not uploaded_file:
    st.info("Please upload a research paper PDF to get started.")
