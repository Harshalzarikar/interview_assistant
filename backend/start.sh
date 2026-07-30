#!/bin/bash

# Start the AI Agent in the background
python agent.py start &

# Start the FastAPI server
uvicorn api:app --host 0.0.0.0 --port $PORT
