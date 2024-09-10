#!/bin/bash
cd /home/ubuntu/TMI_web
git pull origin main

# virtual environemnt variable
VENV_DIR="venv"

# check if venv already exists
if [ -d "$VENV_DIR" ]; then
  echo "Virtual Environment already exists. Updating dependencies..."
  source $VENV_DIR/bin/activate
else
  echo "Virtual environment does not exist. Creating a new one..."
  python3 -m venv $VENV_DIR
  source $VENV_DIR/bin/activate
fi

pip install -r requirements.txt

# Check if Streamlit is running on port 8501 and stop it
if lsof -i :8501; then
  pkill -f 'streamlit run app.py'
fi

# Start Streamlit app in the background
nohup streamlit run app.py --server.port 8501 --server.enableCORS false --server.enableXsrfProtection false > streamlit.log 2>&1 &

echo "app deployment complete."