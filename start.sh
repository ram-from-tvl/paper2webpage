#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI backend in the background
python3 main.py &

# Start Streamlit frontend on port 3000
streamlit run app.py --server.port 3000 --server.address 0.0.0.0
