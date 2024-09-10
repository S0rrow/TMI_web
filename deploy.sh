#!/bin/bash
cd /home/ubuntu/TMI_web
git pull origin main
pip install -r requirements.txt

# Check if Streamlit is running on port 8501 and stop it
if lsof -i :8501; then
  pkill -f 'streamlit run app.py'
fi

# Start Streamlit app in the background
nohup streamlit run app.py --server.port 8501 --server.enableCORS false --server.enableXsrfProtection false > streamlit.log 2>&1 &