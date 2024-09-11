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
PID=$(lsof -t -i:8501)
if [ -n "$PID" ]; then
  echo "Stopping Streamlit process with PID: $PID"
  kill -9 $PID
else
  echo "No Streamlit process is running on port 8501"
fi

# Start Streamlit app in the background
nohup streamlit run app.py --server.port 8501 --server.enableCORS false --server.enableXsrfProtection false > streamlit.log 2>&1 &

echo "app deployment complete."