#!/bin/bash

# Start the Monolith (FastAPI + AI Agent in one process)
uvicorn api:app --host 0.0.0.0 --port $PORT
