# Artizence - AI Interview Platform

Artizence is a high-fidelity AI-driven interview platform that conducts real-time voice interviews. Built with React, FastAPI, LiveKit, Groq, and Deepgram.

## Features

- **Real-time Voice**: Ultra-low latency voice communication powered by LiveKit.
- **Intelligent Interviewer**: Context-aware AI powered by Groq (Llama 3.3 70B).
- **High-speed STT/TTS**: Deepgram Nova-2 for speech-to-text and Deepgram Aura for text-to-speech.
- **Multiple Personas**: Dedicated interviewer personas (Technical, HR, PM, etc.).
- **Modern UI**: Sleek, premium design built with React and custom CSS.

## Tech Stack

- **Frontend**: React, Vite, LiveKit Components.
- **Backend**: FastAPI, Python.
- **Orchestration**: LiveKit Agents.
- **AI Models**: 
  - LLM: Groq (llama-3.3-70b-versatile)
  - STT: Deepgram (nova-2)
  - TTS: Deepgram (aura-asteria-en)

## Prerequisites

- **LiveKit Cloud**: Project keys from [LiveKit](https://livekit.io/).
- **Deepgram**: API Key from [Deepgram](https://deepgram.com/).
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
   DEEPGRAM_API_KEY=your_deepgram_key
   GROQ_API_KEY=your_groq_key
   ```
5. Start the API server:
   ```bash
   python api.py
   ```
6. Start the Agent worker (separate terminal):
   ```bash
   python agent.py dev
   ```

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

## License

© 2024 Artizence Labs Inc. All rights reserved.
