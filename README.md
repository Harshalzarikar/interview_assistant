# Artizence - Mock Interview System

A high-fidelity AI-driven mock interview platform that conducts real-time voice interviews. Built with React, FastAPI, LiveKit, and Groq.

## Features

- **Real-time Voice**: Ultra-low latency WebRTC voice communication powered by LiveKit.
- **Intelligent Interviewer**: Context-aware AI powered by Groq's high-speed Qwen (qwen3.6-27b) model.
- **Automated Interview Analysis**: Immediately after the interview, the AI analyzes the transcript and outputs strengths, weaknesses, and a score out of 10.
- **Multiple Personas**: Dedicated interviewer personas (Technical, HR, PM, etc.).
- **Live Transcript**: Real-time STT streaming mapped directly to the beautiful React UI.

## Tech Stack

- **Frontend**: React, Vite, LiveKit React Components (`useRoomContext`).
- **Backend**: FastAPI, Python.
- **Voice Orchestration**: LiveKit Agents Python SDK.
- **LLM Engine**: Groq API (`qwen/qwen3.6-27b` for high-speed streaming capability).

## Prerequisites

- **LiveKit Cloud**: Project keys from [LiveKit](https://livekit.io/).
- **Groq**: API Key from [Groq](https://groq.com/).

## Setup Instructions

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables in `.env`:
   ```env
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your_api_key
   LIVEKIT_API_SECRET=your_api_secret
   GROQ_API_KEY=your_groq_key
   ```
5. Start the API server:
   ```bash
   python api.py
   ```
   *Note: The LiveKit Agent worker runs automatically inside the FastAPI process (`api.py`). You do NOT need to run `agent.py dev` manually!*

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies (we use yarn):
   ```bash
   yarn install
   ```
3. Run the development server:
   ```bash
   yarn dev
   ```

### 3. API Testing (Postman)
A Postman collection is included in the repository root for testing the backend independently.
1. Open Postman.
2. Click **Import** and select `InterviewAI_Postman_Collection.json`.
3. Test endpoints like `/api/start-interview` and `/api/analyze-interview`.

## License

© 2024 Artizence Labs Inc. All rights reserved.
