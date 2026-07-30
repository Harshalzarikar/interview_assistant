#!/bin/bash

# Start the AI Agent in the background
python agent.py dev &

# Start the FastAPI server
uvicorn api:app --host 0.0.0.0 --port $PORT
